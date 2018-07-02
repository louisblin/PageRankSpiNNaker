import abc


class SpiNNakerAdapterInterface(metaclass=abc.ABCMeta):

    def __init__(self):
        pass

    @abc.abstractmethod
    def simulation_setup(self, *args, **kwargs):
        """Setup the SpiNNaker simulation framework

        :return: None
        """
        pass

    @abc.abstractmethod
    def simulation_teardown(self):
        """Tear down the SpiNNaker simulation framework

        :return: None
        """
        pass

    @abc.abstractmethod
    def build_page_rank_graph(self, vertices, edges, **kwargs):
        """Create a sPyNNaker simulation graph from the Page Rank input graph.

        :return: None
        """
        pass

    @abc.abstractmethod
    def simulation_run(self, *args, **kwargs):
        """Run the simulation on SpiNNaker.

        :return: None
        """
        pass

    @abc.abstractmethod
    def extract_ranks(self):
        """Extract the per-iteration ranks computed during the simulation.

        :return: <np.array> ranks
        """
        pass

    @abc.abstractmethod
    def extract_router_provenance(self, collect_names=None):
        """Extract the router information for the given names.

        :arg collect_names: [<str>] router entries to extract
        :return: <dict> name-indexed names
        """
        pass

    @abc.abstractmethod
    def produced_provenance_warnings(self):
        """Whether the simulation produced provenance data warnings.

        :return: <bool>
        """
        pass
