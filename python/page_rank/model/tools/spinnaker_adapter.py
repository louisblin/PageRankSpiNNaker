import io
import logging

import numpy as np

import spynnaker8 as p
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.interface.interface_functions \
    import RouterProvenanceGatherer

from page_rank.model.python_models.model_data_holders.page_rank_data_holder \
    import PageRankDataHolder as Page_Rank
from page_rank.model.python_models.synapse_dynamics.synapse_dynamics_noop \
    import SynapseDynamicsNoOp
from page_rank.model.tools.spinnaker_adapter_interface import \
    SpiNNakerAdapterInterface
from page_rank.model.tools.utils import getLogger

RANK = 'v'
PROVENANCE_LOGGER = 'spinn_front_end_common.interface.abstract_spinnaker_base'

_logger = getLogger(__name__)


#
# Main simulation interface
#

class SpiNNakerAdapter(SpiNNakerAdapterInterface):

    def __init__(self):
        SpiNNakerAdapterInterface.__init__(self)

        # State variable
        self._model = None

    def simulation_setup(self, *args, **kwargs):
        """Setup the SpiNNaker simulation framework

        :return: None
        """
        p.setup(*args, **kwargs)

    def simulation_teardown(self):
        """Tear down the SpiNNaker simulation framework

        :return: None
        """
        p.end()

    def build_page_rank_graph(self, vertices, edges, atoms_per_core=None,
                              page_rank_kwargs=None):
        """Create a sPyNNaker simulation graph from the Page Rank input graph.

        Maps the graph to sPyNNaker.

        :return: None
        """

        # Pre-processing, compute inbound / outbound edges for each node
        n_neurons = len(vertices)
        outgoing_edges_count = [0] * n_neurons
        incoming_edges_count = [0] * n_neurons
        for src, tgt in edges:
            outgoing_edges_count[src] += 1
            incoming_edges_count[tgt] += 1

        # Vertices
        self._model = p.Population(
            n_neurons,
            Page_Rank(
                rank_init=1. / n_neurons,
                incoming_edges_count=incoming_edges_count,
                outgoing_edges_count=outgoing_edges_count,
                **(page_rank_kwargs or {})
            ),
            label="page_rank")

        if atoms_per_core:
            p.set_number_of_neurons_per_core(atoms_per_core)

        # Edges
        p.Projection(
            self._model, self._model,
            p.FromListConnector(edges),
            synapse_type=SynapseDynamicsNoOp()
        )

    def simulation_run(self, *args, **kwargs):
        """Run the simulation on SpiNNaker.

        :return: None
        """

        # Record ranks
        self._model.record([RANK])

        # Run simulation
        p.run(*args, **kwargs)

    def extract_ranks(self):
        """Extract the per-iteration ranks computed during the simulation.

        :return: <np.array> ranks
        """

        raw_ranks =  self._model.get_data(RANK).segments[0].filter(name=RANK)[0]
        return np.array([[np.float64(cell / 2 ** 17) for cell in row]
                          for row in raw_ranks])

    def extract_router_provenance(self, collect_names=None):
        """Extract the router information for the given names.

        :type collect_names: [<str>] router entries to extract
        :return: <dict> name-indexed names
        """
        if collect_names is None:
            collect_names = [
                'total_multi_cast_sent_packets',
                'total_created_packets',
                'total_dropped_packets',
                'total_missed_dropped_packets',
                'total_lost_dropped_packets'
            ]

        m = globals_variables.get_simulator()

        router_provenance = RouterProvenanceGatherer()
        router_prov = router_provenance(m._txrx, m._machine, m._router_tables,
                                        True)

        res = dict().fromkeys(collect_names, 0)
        for item in router_prov:
            _logger.debug('{} => {}'.format(item.names, item.value))
            name = item.names[-1]
            if name in collect_names:
                res[name] += int(item.value)

        return res

    def produced_provenance_warnings(self):
        """Whether the simulation produced provenance data warnings.

        :return: <bool>
        """
        with io.BytesIO() as log_capture_string:
            log = logging.getLogger(PROVENANCE_LOGGER)
            map(log.removeHandler, log.handlers)
            log.addHandler(logging.StreamHandler(log_capture_string))

            self.simulation_teardown()

            return bool(log_capture_string.getvalue())
