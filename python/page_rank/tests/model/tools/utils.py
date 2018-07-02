import numpy as np

from page_rank.model.tools.spinnaker_adapter_interface import \
    SpiNNakerAdapterInterface


#
# Dummy SpiNNaker adapter interface
#

class SpiNNakerTestAdapter(SpiNNakerAdapterInterface):

    def __init__(self, ranks=None, router_prov=None, has_prov_warnings=False):
        SpiNNakerAdapterInterface.__init__(self)

        if ranks is None:
            ranks = np.array([])
        self._ranks = ranks

        if router_prov is None:
            router_prov = np.array([])
        self._router_prov = router_prov

        self._has_prov_warnings = has_prov_warnings

    def simulation_setup(self, *args, **kwargs):
        pass

    def simulation_teardown(self):
        pass

    def build_page_rank_graph(self, *args, **kwargs):
        pass

    def simulation_run(self, *args, **kwargs):
        pass

    def extract_ranks(self):
        """Extract the per-iteration ranks computed during the simulation.

        :return: <np.array> ranks
        """
        return self._ranks

    def extract_router_provenance(self, collect_names=None):
        """Extract the router information for the given names.

        :type collect_names: [<str>] router entries to extract
        :return: <dict> name-indexed names
        """
        return self._router_prov

    def has_provenance_warnings(self):
        """Whether the simulation produced provenance data warnings.

        :return: <bool>
        """
        return self._has_prov_warnings