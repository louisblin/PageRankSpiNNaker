import numpy as np

from page_rank.model.tools.spinnaker_adapter_interface import \
    SpiNNakerAdapterInterface


#
# Main simulation interface
#

class SpiNNakerTestAdapter(SpiNNakerAdapterInterface):

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
        return np.array()

    def extract_router_provenance(self, collect_names=None):
        """Extract the router information for the given names.

        :type collect_names: [<str>] router entries to extract
        :return: <dict> name-indexed names
        """
        return np.array()

    def produced_provenance_warnings(self):
        """Whether the simulation produced provenance data warnings.

        :return: <bool>
        """
        return False
