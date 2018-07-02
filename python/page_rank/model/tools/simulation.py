import logging
import matplotlib.pyplot as plt

import networkx as nx
import numpy as np

from page_rank.model.tools.utils import FailedOnWarningError, \
    graph_visualiser, to_fp, getLogger, silence_output, node_formatter, \
    format_ranks_string, compute_page_rank
from page_rank.model.tools.spinnaker_adapter import SpiNNakerAdapter

FLOAT_PRECISION = 5
TOL = 10 ** (-FLOAT_PRECISION)

NX_NODE_SIZE = 350
ANNOTATION = 'Simulated with SpiNNaker_under_version(1!4.0.0-Riptalon)'
DEFAULT_SPYNNAKER_PARAMS = {
    # Time interval between each timer tick on SpiNNaker
    'timestep': .1,  # ms
    # Slow down factor
    # `timestep' ms on machine = `time_scale_factor' * `timestep' in real time
    'time_scale_factor': 10,
    # Range of random back off delays between packet sent
    # set to minimum, i.e. a timestep, as we don't want to wait
    'min_delay': .1,  # ms
    'max_delay': .1,  # ms
}


#
# Main simulation interface
#

def _gen_labels(edges):
    return map(str, set([s for s, _ in edges] + [t for _, t in edges]))


def _gen_sim_vertices(labels):
    return list(range(len(labels)))


def _gen_sim_edges(edges, labels, sim_vertices):
    labels_to_ids = dict(zip(labels, sim_vertices))
    return [(labels_to_ids[src], labels_to_ids[tgt]) for src, tgt in edges]


class PageRankSimulation:

    def __init__(self, run_time, edges, labels=None, parameters=None,
                 damping=.85, log_level=logging.INFO, pause=False,
                 fail_on_warning=False, spinnaker_adapter=SpiNNakerAdapter()):
        """Creates an object to define, run and inspect a Page Rank simulation.

        :param run_time: time to run the computation for
        :param edges: list of edges
        :param labels: labels of the nodes
        :param parameters: sPyNNaker setup() parameters
        :param damping: damping factor in Page Rank
        :param log_level: global log level
        :param pause: pausing the simulation before it ends and is unloaded from
                      the SpiNNaker chips allows for inspection of the
                      post-simulation state through `ybug'
                      (see SpiNNakerManchester/spinnaker_tools)

        :param fail_on_warning: throw an exception if simulation throws warnings
        :param spinnaker_adapter: adapter to interact with the neural model
        """
        self._validate_graph_structure(edges, labels, damping)

        # Simulation parameters
        self._run_time = run_time
        self._edges = edges
        self._labels = labels or _gen_labels(self._edges)
        self._sim_vertices = _gen_sim_vertices(self._labels)
        self._sim_edges = _gen_sim_edges(self._edges, self._labels,
                                              self._sim_vertices)
        self._parameters = DEFAULT_SPYNNAKER_PARAMS
        self._parameters.update(parameters or {})
        self._damping = damping
        self._pause = pause
        self._fail_on_warning = fail_on_warning
        self._spinnaker_adapter = spinnaker_adapter

        # Simulation state variables
        self._sim_ranks = None
        self._sim_convergence = None
        self._input_networkx_repr = None
        self._simulation_has_ran = True

        # Numpy printing with some precision and no scientific notation
        np.set_printoptions(suppress=True, precision=FLOAT_PRECISION)

        # logging
        self._logger = getLogger(log_level=log_level)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._pause:
                raw_input('Press any key to finish...')

            if self._fail_on_warning:
                if self._spinnaker_adapter.has_provenance_warnings():
                    raise FailedOnWarningError()
            else:
                self._spinnaker_adapter.simulation_teardown()
        # else, exception is cascaded if there is one...
        #   simulation_teardown() not executed, fails on sPyNNaker runtime error

    #
    # Private functions, internal helpers
    #

    def _validate_graph_structure(self, edges, labels, damping):
        # Ensure to duplicate edges
        size_diff = len(edges) - len(set(edges))
        if size_diff != 0:
            raise ValueError("Found %d forbidden duplicate edges." % size_diff)

        # Ensure all nodes connected (no dangling nodes)
        if labels:
            size_diff = len(labels) - len(_gen_labels(edges))
            if size_diff != 0:
                raise ValueError("Found %d dangling nodes (extra 'labels' "
                                 "not used in 'edges')." % size_diff)

        # Ensure damping factor has a valid range
        if not (0 <= damping < 1):
            raise ValueError("Damping factor '%.02f' not in [0,1)." % damping)

    def _get_damping_factor(self):
        # Ensures float is encoded in fixed-point without precision loss
        return float(to_fp(self._damping))

    def _get_damping_sum(self):
        # Ensures float is encoded in fixed-point without precision loss
        return float(to_fp((1. - self._damping) / len(self._labels)))

    def _init_networkx_repr(self):
        if self._input_networkx_repr is None:
            # Graph structure
            g = nx.Graph().to_directed()
            g.add_edges_from(self._edges)

            # Save graph for Page Rank python computations
            self._input_networkx_repr = g
        return self._input_networkx_repr

    def _extract_sim_ranks(self):
        """Extracts the rank computed during the simulation.

        :return: (<np.array> ranks, <int> number of iterations to convergence)
        """
        if not self._simulation_has_ran:
            raise RuntimeError('You first need to .run(...) the simulation.')

        if self._sim_ranks is None:
            ranks = self._spinnaker_adapter.extract_ranks()

            # Compute convergence
            xlast = ranks[0]
            N = len(xlast)
            convergence = len(ranks)

            for it, x in enumerate(ranks[1:]):
                err = sum([abs(x_i - x_last_i)
                           for x_i, x_last_i in zip(x, xlast)])
                if err < N * TOL:
                    convergence = it + 1  # since we began at index #1
                    break
                xlast = x

            # Copy first convergence row to all remaining
            for i in range(convergence + 1, len(ranks)):
                ranks[i, :] = ranks[convergence, :]

            self._sim_ranks, self._sim_convergence = ranks, convergence
        return self._sim_ranks, self._sim_convergence

    def _verify_sim(self, verify, diff_only=False, diff_max=50):
        """Verifies simulation results correctness.

        Checks the ranks results from the simulation match those given by a
        Python implementation of Page Rank in networkx.

        :return: bool, whether the results match
        """
        msg = "\n"

        # Get last row of the ranks computed in the simulation
        self._logger.important("Extracting computed ranks...")
        computed_ranks, it = self._extract_sim_ranks()
        computed_ranks = computed_ranks[-1]
        msg += "[SpiNNaker] Convergence < 10e-%d in #%d iterations.\n" % (
            FLOAT_PRECISION, it)

        if not verify:
            return True, msg + "Correctness unchecked.\n"

        # Get Page Rank from python implementation
        self._logger.important("Computing Page Rank...")
        expected_ranks, it = self.do_python_page_rank()
        msg += "[Python PR] Convergence < 10e-%d in #%d iterations.\n" % (
            FLOAT_PRECISION, it)

        # Compare at defined precision
        is_correct = np.allclose(computed_ranks, expected_ranks, atol=TOL)

        if is_correct:
            msg += "CORRECT Page Rank results.\n"
            if not diff_only:
                msg += format_ranks_string(self._labels, {
                    'Computed': computed_ranks
                })
        else:
            msg += ("INCORRECT Page Rank results.\n" +
                    format_ranks_string(self._labels, {
                        'Computed': computed_ranks,
                        'Expected': expected_ranks
                    }, diff_only, diff_max))

        return is_correct, msg

    #
    # Exposed functions
    #

    def run(self, verify=False, atoms_per_core=None, **kwargs):
        """Runs the simulation.

        :param verify: check the results with a Page Rank python implementation.
        :param atoms_per_core: number of vertices to set per core
        :return: bool, correctness of the simulation results
        """

        with silence_output(enable=self._logger.isEnabledFor(logging.INFO)):
            # Setup simulation
            self._spinnaker_adapter.simulation_setup(**self._parameters)

            # Build graph
            page_rank_kwargs = dict(
                damping_factor=self._get_damping_factor(),
                damping_sum=self._get_damping_sum()
            )

            self._spinnaker_adapter.build_page_rank_graph(
                self._sim_vertices, self._sim_edges,
                atoms_per_core=atoms_per_core, page_rank_kwargs=page_rank_kwargs
            )

            # Run
            self._spinnaker_adapter.simulation_run(self._run_time)
            self._simulation_has_ran = True

            # Correctness check
            is_correct, msg = self._verify_sim(verify, **kwargs)

        self._logger.important(msg)
        return is_correct

    def do_python_page_rank(self, max_iter=100, tol=TOL):
        """Return the PageRank of the nodes in the graph.

        Adapted to return the # of iterations necessary to compute the Page Rank

        Source
        ------
        networkx/algorithms/link_analysis/pagerank_alg.py
        """

        # Init graph structure
        g = self._init_networkx_repr()
        labels = self._labels
        d = self._get_damping_factor()
        d_sum = self._get_damping_sum()

        return compute_page_rank(g, labels, d, d_sum, tol, max_iter)

    @graph_visualiser
    def draw_input_graph(self, save_graph=False):
        """Compute a graphical representation of the input graph.
        """

        # Graph structure
        g = self._init_networkx_repr()

        # Graph formatting
        pos = nx.layout.spring_layout(g)
        nx.draw_networkx_nodes(g, pos, node_size=NX_NODE_SIZE, node_color='red')
        nx.draw_networkx_edges(g, pos, arrowstyle='->')
        nx.draw_networkx_labels(g, pos, font_color='white', font_weight='bold')
        self_loops = g.nodes_with_selfloops()
        nx.draw_networkx_nodes(self_loops, pos, node_size=NX_NODE_SIZE,
                               node_color='black')

        # Figure layout
        plt.gca().set_axis_off()
        plt.suptitle('Input graph for Page Rank')
        plt.title('Black nodes are self-looping', fontsize=8)

        if save_graph:
            plt.savefig('input_graph.png')

    @graph_visualiser
    def draw_output_graph(self, save_graph=False):
        """Displays the computed rank over time.
        """

        # Collect simulation ranks
        ranks, _ = self._extract_sim_ranks()

        # Ranks formatting
        ranks = ranks.swapaxes(0, 1)
        labels = self._labels or list(range(len(ranks)))
        for lbl, r in zip(labels, ranks):
            plt.plot(np.round(r, FLOAT_PRECISION), label=node_formatter(lbl))

        # Figure layout
        plt.legend()
        plt.xticks()
        plt.yticks()
        plt.xlabel('Time (ms)')
        plt.ylabel('Rank')
        plt.suptitle("Rank over time")
        plt.title(ANNOTATION, fontsize=6)

        if save_graph:
            plt.savefig('input_graph.png')