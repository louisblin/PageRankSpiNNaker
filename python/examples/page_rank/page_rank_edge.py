from enum import Enum

from pacman.model.partitioned_graph.multi_cast_partitioned_edge import MultiCastPartitionedEdge


class PageRankEdge(MultiCastPartitionedEdge):
    """ Used in conjunction with a page rank vertex to execute the page rank simulation
    """

    DIRECTIONS = Enum(value="EDGES", names=[("DIRECTED", 0)])

    def __init__(self, pre_subvertex, post_subvertex, n_keys=1, label=None):
        MultiCastPartitionedEdge.__init__(self, pre_subvertex, post_subvertex, label=label)
        self._direction = PageRankEdge.DIRECTIONS.DIRECTED

    @property
    def direction(self):
        """

        :return:
        """
        return self._direction

    def is_partitioned_edge(self):
        return True

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "PageRankEdge:{}:{}".format(self._label, self._direction)
