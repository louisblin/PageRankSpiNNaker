import io
import logging
import matplotlib.pyplot as plt

import networkx as nx
import numpy as np

from page_rank.model.tools.utils import FailedOnWarningError, check_sim_ran, \
    graph_visualiser, to_fp, to_hex, getLogger, silence_output, \
    PageRankNoConvergence, node_formatter, float_formatter, format_ranks_string
from page_rank.model.tools.spinnaker_adapter import SpiNNakerAdapter

RANK = 'v'
NX_NODE_SIZE = 350
ITER_BITS = 2  # see c_models/src/neuron/in_messages.h
FLOAT_PRECISION = 5
TOL = 10 ** (-FLOAT_PRECISION)
ANNOTATION = 'Simulated with SpiNNaker_under_version(1!4.0.0-Riptalon)'
PROVENANCE_LOGGER = 'spinn_front_end_common.interface.abstract_spinnaker_base'
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

class PageRankSimulation:

    def __init__(self, run_time, edges, labels=None, parameters=None,
                 damping=.85, log_level=logging.INFO, pause=False,
                 fail_on_warning=False, spinnaker_adapter=SpiNNakerAdapter()):
        self._validate_graph_structure(edges, labels, damping)

        # Simulation parameters
        self._run_time = run_time
        self._edges = edges
        self._labels = labels or self._gen_labels(self._edges)
        self._sim_vertices = self._gen_sim_vertices(self._labels)
        self._sim_edges = self._gen_sim_edges(self._edges, self._labels,
                                              self._sim_vertices)
        self._parameters = DEFAULT_SPYNNAKER_PARAMS
        self._parameters.update(parameters or {})
        self._damping = damping
        self._pause = pause
        self._fail_on_warning = fail_on_warning
        self._spinnaker_adapter = spinnaker_adapter

        # Simulation state variables
        self._model = None
        self._sim_ranks = None
        self._sim_convergence = None
        self._input_networkx_repr = None

        # Numpy printing with some precision and no scientific notation
        np.set_printoptions(suppress=True, precision=FLOAT_PRECISION)

        # logging
        self._logger = getLogger(name=__name__, log_level=log_level)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._pause:
                raw_input('Press any key to finish...')

            if self._fail_on_warning and \
                    self._spinnaker_adapter.produced_provenance_warnings():
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
            raise ValueError("graph structure error - %d duplicate(s) found." %
                             size_diff)

        # Ensure all nodes connected (no dangling nodes)
        if labels:
            size_diff = len(labels) - len(self._gen_labels(edges))
            if size_diff != 0:
                raise ValueError("#labels don't match #edges by %d labels." %
                                 size_diff)

        # Ensure damping factor has a valid range
        if not (0 <= damping < 1):
            raise ValueError("Damping factor '%.02f' not in valid range [0,1)."
                             % damping)

    @staticmethod
    def _gen_labels(edges):
        return map(str, set([s for s, _ in edges] + [t for _, t in edges]))

    @staticmethod
    def _gen_sim_vertices(labels):
        return list(range(len(labels)))

    @staticmethod
    def _gen_sim_edges(edges, labels, sim_vertices):
        labels_to_ids = dict(zip(labels, sim_vertices))
        return [(labels_to_ids[src], labels_to_ids[tgt]) for src, tgt in edges]

    @check_sim_ran
    def _extract_sim_ranks(self):
        """Extracts the rank computed during the simulation.

        :return: (<np.array> ranks, <int> number of iterations to convergence)
        """
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
        expected_ranks, it = self.compute_page_rank()
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

            # Correctness check
            is_correct, msg = self._verify_sim(verify, **kwargs)

        self._logger.important(msg)
        return is_correct

    def compute_page_rank(self, max_iter=100, tol=TOL):
        """Return the PageRank of the nodes in the graph.

        Adapted to return the # of iterations necessary to compute the Page Rank

        Source
        ------
        networkx/algorithms/link_analysis/pagerank_alg.py

        """
        # Init graph structure
        g = self._init_networkx_repr()

        w = nx.stochastic_graph(g, weight=None)
        n = w.number_of_nodes()

        # Init fixed-point constants
        d = to_fp(self._get_damping_factor())
        tol = to_fp(tol)
        zero = to_fp(0)
        one = to_fp(1.)
        n = to_fp(n)
        damping_sum = to_fp(self._get_damping_sum())

        # Iterate up to max_iter iterations
        x = dict.fromkeys(w, one / n)
        for iter_no in range(max_iter):
            self._logger.debug('\n===== TIME STEP = {} ====='.format(iter_no))
            x_last = x
            x = dict.fromkeys(x_last.keys(), zero)

            for node in x:
                pkt = x_last[node] / to_fp(len(w[node]))
                self._logger.debug('[t=%04d|#%3s] Sending pkt %f[%s]' % (
                    iter_no, node, pkt, to_hex(pkt)))

                # Exchange ranks
                for conn_node in w[node]:  # edge: node -> conn_node
                    prev = x[conn_node]
                    # Simulates payload-lossy encoding of the iteration
                    # See c_models/src/neuron/in_messages.h
                    #   function: in_messages_payload_format
                    x[conn_node] += ((pkt >> ITER_BITS) << ITER_BITS)
                    self._logger.debug("[idx=%3s] %f[%s] + %f[%s] = %f[%s]" % (
                        conn_node, prev, to_hex(prev), pkt,
                        to_hex(pkt), x[conn_node],
                        to_hex(x[conn_node])))

            # Compute dangling factor
            if d != one:
                for node in x:
                    prev = x[node]
                    x[node] = damping_sum + d * x[node]
                    self._logger.debug(
                        "[idx=%3s] %f[%s] * %f[%s] + %f[%s] = %f[%s]" % (
                            node, d, to_hex(d), prev, to_hex(prev),
                            damping_sum,
                            to_hex(damping_sum), x[node],
                            to_hex(x[node])))

            # Check convergence, l1 norm
            err = sum([abs(x[node] - x_last[node]) for node in x])
            if err < n * tol:
                if self._labels:
                    x = np.array([np.float64(x[v]) for v in self._labels])
                return x, iter_no + 1  # iter t+1 happens at the end of time t

        raise PageRankNoConvergence(max_iter)

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

        Note: pausing the simulation before it ends and is unloaded from the
              SpiNNaker chips allows for inspection of the post-simulation state
              through `ybug' (see SpiNNakerManchester/spinnaker_tools)
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


