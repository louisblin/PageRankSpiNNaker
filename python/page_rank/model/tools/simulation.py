import io
import logging
import os
import sys
from contextlib import contextmanager

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import spynnaker8 as p
from prettytable import PrettyTable

from page_rank.model.python_models.model_data_holders.page_rank_data_holder \
    import PageRankDataHolder as Page_Rank
from page_rank.model.python_models.synapse_dynamics.synapse_dynamics_noop \
    import SynapseDynamicsNoOp
from page_rank.model.tools.fixed_point import FXfamily


LOG_HIGHLIGHTS = logging.INFO + 1
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

logger = logging.getLogger(__name__)


#
# Utility functions
#

class FailedOnWarningError(RuntimeError):
    pass

def _log_info(*args, **kwargs):
    logging.log(LOG_HIGHLIGHTS, *args, **kwargs)


def check_sim_ran(func):
    """Raises an error is the simulation was not ran.

    State variable `self._model' serves as a proxy to determine if .start(...)
    was called.

    :return: None
    """
    def wrapper(self, *args, **kwargs):
        if self._model is None:
            raise RuntimeError('You first need to .start(...) the simulation.')
        return func(self, *args, **kwargs)

    return wrapper


#
# Main simulation interface
#

class PageRankSimulation:

    def __init__(self, run_time, edges, labels=None, parameters=None,
                 damping=.85, log_level=logging.INFO, pause=False,
                 fail_on_warning=False):
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

        # Simulation state variables
        self._model = None
        self._sim_ranks = None
        self._sim_convergence = None
        self._input_graph = None

        # Numpy printing with some precision and no scientific notation
        np.set_printoptions(suppress=True, precision=FLOAT_PRECISION)

        # logging
        logging.basicConfig(level=log_level, datefmt='%Y-%m-%d %H:%M:%S',
                            format='%(asctime)s %(levelname)s: %(message)s')
        logger.setLevel(log_level)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._pause:
                raw_input('Press any key to finish...')

            if self._fail_on_warning:
                with io.BytesIO() as log_capture_string:
                    log = logging.getLogger(PROVENANCE_LOGGER)
                    map(log.removeHandler, log.handlers)
                    log.addHandler(logging.StreamHandler(log_capture_string))

                    p.end()  # fails on sPyNNaker runtime error

                    # Fail on warning
                    if log_capture_string.getvalue():
                        raise FailedOnWarningError()
            else:
                p.end()  # fails on sPyNNaker runtime error

        # else, exception is cascaded if there is one...

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

    @staticmethod
    def _node_formatter(name):
        return "Node %s" % name

    @staticmethod
    def _float_formatter(number):
        return ("%.{}f".format(FLOAT_PRECISION)) % number

    def _get_ranks_string(self, ranks, diff_only=False, diff_max=50):
        """Pretty prints a table of ranks values

        :param ranks: dict of name-indexed rows of values, or list of a single
                      row of values
        :return: None
        """
        if diff_only and len(ranks) == 2:
            # Filter out valid ranks
            [(lbl1, row_1), (lbl2, row_2)] = ranks.items()
            diff_idx = [i for i, (r1, r2) in enumerate(zip(row_1, row_2))
                        if abs(r1 - r2) >= TOL]
            labels = [self._labels[i] for i in diff_idx]
            row_1 = [row_1[i] for i in diff_idx]
            row_2 = [row_2[i] for i in diff_idx]
            if len(diff_idx) > diff_max:
                compacted_label = "{}..{}".format(labels[diff_max], labels[-1])
                labels = labels[:diff_max] + [compacted_label]
                row_1  = row_1[:diff_max]  + [0]
                row_2  = row_2[:diff_max]  + [0]

            # Construct table
            table = PrettyTable([''] + map(self._node_formatter, labels))
            table.add_row([lbl1] + map(self._float_formatter, row_1))
            table.add_row([lbl2] + map(self._float_formatter, row_2))
        else:
            # Multiple rows, indexed by row name
            table = PrettyTable([''] + map(self._node_formatter, self._labels))
            for name, row in ranks.items():
                table.add_row([name] + map(self._float_formatter, row))

        return table.get_string()

    def _create_page_rank_model(self, atoms_per_core):
        """Maps the graph to sPyNNaker.

        :return: p.Population, the neural model to compute Page Rank
        """
        # Pre-processing, compute inbound / outbound edges for each node
        n_neurons = len(self._sim_vertices)
        outgoing_edges_count = [0] * n_neurons
        incoming_edges_count = [0] * n_neurons
        for src, tgt in self._sim_edges:
            outgoing_edges_count[src] += 1
            incoming_edges_count[tgt] += 1

        # Vertices
        pop = p.Population(
            n_neurons,
            Page_Rank(
                damping_factor=self._get_damping_factor(),
                damping_sum=self._get_damping_sum(),
                rank_init=1. / n_neurons,
                incoming_edges_count=incoming_edges_count,
                outgoing_edges_count=outgoing_edges_count
            ),
            label="page_rank")

        if atoms_per_core:
            pop._vertex.set_max_atoms_per_core(atoms_per_core)

        # Edges
        p.Projection(
            pop, pop,
            p.FromListConnector(self._sim_edges),
            synapse_type=SynapseDynamicsNoOp()
        )

        return pop

    @check_sim_ran
    def _extract_sim_ranks(self):
        """Extracts the rank computed during the simulation.

        :return: (<np.array> ranks, <int> number of iterations to convergence)
        """
        if self._sim_ranks is None:
            raw_ranks = \
                self._model.get_data(RANK).segments[0].filter(name=RANK)[0]
            ranks = np.array([[np.float64(cell / 2 ** 17) for cell in row]
                              for row in raw_ranks])

            # Compute convergence
            xlast = ranks[0]
            N = len(xlast)
            convergence = len(ranks)

            for it, x in enumerate(ranks[1:]):
                err = sum([abs(x_i - xlast_i)
                           for x_i, xlast_i in zip(x, xlast)])
                if err < N * TOL:
                    convergence = it + 1  # since we began at index #1
                    break
                xlast = x

            # Copy first convergence row to all remaining
            for i in range(convergence + 1, len(ranks)):
                ranks[i, :] = ranks[convergence, :]

            self._sim_ranks, self._sim_convergence = ranks, convergence
        return self._sim_ranks, self._sim_convergence

    @staticmethod
    def _to_fp(n):
        return FXfamily(n_bits=32)(n)

    @staticmethod
    def _to_hex(fp):
        return fp.toBinaryString(logBase=4, twosComp=False)

    def _get_damping_factor(self):
        # Ensures float is can be losslessly encoded in fixed-point
        return float(self._to_fp(self._damping))

    def _get_damping_sum(self):
        # Ensures float is can be losslessly encoded in fixed-point
        return float(self._to_fp((1. - self._damping) / len(self._labels)))

    def _verify_sim(self, verify, diff_only=False, diff_max=50):
        """Verifies simulation results correctness.

        Checks the ranks results from the simulation match those given by a
        Python implementation of Page Rank in networkx.

        :return: bool, whether the results match
        """
        msg = "\n"

        # Get last row of the ranks computed in the simulation
        _log_info("Extracting computed ranks...")
        computed_ranks, it = self._extract_sim_ranks()
        computed_ranks = computed_ranks[-1]
        msg += "[SpiNNaker] Convergence < 10e-%d in #%d iterations.\n" % (
            FLOAT_PRECISION, it)

        if not verify:
            return True, msg + "Correctness unchecked."

        # Get Page Rank from python implementation
        _log_info("Computing Page Rank...")
        expected_ranks, it = self.compute_page_rank()
        msg += "[Python PR] Convergence < 10e-%d in #%d iterations.\n" % (
            FLOAT_PRECISION, it)

        # Compare at defined precision
        is_correct = np.allclose(computed_ranks, expected_ranks, atol=TOL)

        if is_correct:
            msg += "CORRECT Page Rank results.\n"
            if not diff_only:
                msg += self._get_ranks_string({
                    'Computed': computed_ranks
                })
        else:
            msg += ("INCORRECT Page Rank results.\n" +
                    self._get_ranks_string({
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
        :param silence_output: remove output
        :return: bool, correctness of the simulation results
        """

        # Setup simulation
        @ConditionalSilencer(not logger.isEnabledFor(logging.INFO))
        def _run():
            p.setup(**self._parameters)

            self._model = self._create_page_rank_model(atoms_per_core)
            self._model.record([RANK])

            p.run(self._run_time)
            return self._verify_sim(verify, **kwargs)

        is_correct, msg = _run()
        _log_info(msg)
        return is_correct

    def compute_page_rank(self, max_iter=100, tol=TOL):
        """Return the PageRank of the nodes in the graph.

        Adapted to return the # of iterations necessary to compute the Page Rank

        Source
        ------
        networkx/algorithms/link_analysis/pagerank_alg.py

        """
        # Init graph structure
        if self._input_graph is None:
            # Compute input graph if not defined
            self.draw_input_graph(show_graph=False)

        W = nx.stochastic_graph(self._input_graph, weight=None)
        N = W.number_of_nodes()

        # Init fixed-point constants
        d = self._to_fp(self._get_damping_factor())
        tol = self._to_fp(tol)
        ZERO = self._to_fp(0)
        ONE = self._to_fp(1.)
        N = self._to_fp(N)
        damping_sum = self._to_fp(self._get_damping_sum())

        # Iterate up to max_iter iterations
        x = dict.fromkeys(W, ONE / N)
        for iter in range(max_iter):
            logger.debug('\n===== TIME STEP = {} ====='.format(iter))
            xlast = x
            x = dict.fromkeys(xlast.keys(), ZERO)

            for node in x:
                pkt = xlast[node] / self._to_fp(len(W[node]))
                logger.debug('[t=%04d|#%3s] Sending pkt %f[%s]' % (
                    iter, node, pkt, self._to_hex(pkt)))

                # Exchange ranks
                for conn_node in W[node]:  # edge: node -> conn_node
                    prev = x[conn_node]
                    # Simulates payload-lossy encoding of the iteration
                    # See c_models/src/neuron/in_messages.h
                    #   function: in_messages_payload_format
                    x[conn_node] += ((pkt >> ITER_BITS) << ITER_BITS)
                    logger.debug("[idx=%3s] %f[%s] + %f[%s] = %f[%s]" % (
                        conn_node, prev, self._to_hex(prev), pkt,
                        self._to_hex(pkt), x[conn_node],
                        self._to_hex(x[conn_node])))

            # Compute dangling factor
            if d != ONE:
                for node in x:
                    prev = x[node]
                    x[node] = damping_sum + d * x[node]
                    logger.debug(
                        "[idx=%3s] %f[%s] * %f[%s] + %f[%s] = %f[%s]" % (
                            node, d, self._to_hex(d), prev, self._to_hex(prev),
                            damping_sum,
                            self._to_hex(damping_sum), x[node],
                            self._to_hex(x[node])))

            # Check convergence, l1 norm
            err = sum([abs(x[node] - xlast[node]) for node in x])
            if err < N * tol:
                if self._labels:
                    x = np.array([np.float64(x[v]) for v in self._labels])
                return x, iter + 1  # iter t+1 happens at the end of time t
        raise nx.PowerIterationFailedConvergence(max_iter)

    def draw_input_graph(self, show_graph=False):
        """Compute a graphical representation of the input graph.

        :param show_graph: whether to display the graph, default is False
        :return: None
        """

        # Graph structure
        G = nx.Graph().to_directed()
        G.add_edges_from(self._edges)

        # Save graph for Page Rank python computations
        self._input_graph = G

        if show_graph:
            _log_info("Displaying input graph. "
                      "Check DISPLAY={} if this hangs...".format(
                os.getenv('DISPLAY')))
            # Clear plot
            plt.clf()

            # Graph layout
            pos = nx.layout.spring_layout(G)
            nx.draw_networkx_nodes(G, pos, node_size=NX_NODE_SIZE,
                                   node_color='red')
            nx.draw_networkx_edges(G, pos, arrowstyle='->')
            nx.draw_networkx_labels(G, pos, font_color='white',
                                    font_weight='bold')
            self_loops = G.nodes_with_selfloops()
            nx.draw_networkx_nodes(self_loops, pos, node_size=NX_NODE_SIZE,
                                   node_color='black')

            # Show graph
            plt.gca().set_axis_off()
            plt.suptitle('Input graph for Page Rank')
            plt.title('Black nodes are self-looping', fontsize=8)
            plt.show()

    @check_sim_ran
    def draw_output_graph(self, show_graph=True):
        """Displays the computed rank over time.

        Note: pausing the simulation before it ends and is unloaded from the
              SpiNNaker chips allows for inspection of the post-simulation state
              through `ybug' (see SpiNNakerManchester/spinnaker_tools)

        :param show_graph: whether to display the graph, default is False
        :return: None
        """
        ranks, _ = self._extract_sim_ranks()

        if show_graph:
            _log_info("Displaying output graph. "
                      "Check DISPLAY={} if this hangs...".format(
                os.getenv('DISPLAY')))
            plt.clf()

            ranks = ranks.swapaxes(0, 1)
            labels = self._labels or list(range(len(ranks)))
            for lbl, r in zip(labels, ranks):
                plt.plot(np.round(r, FLOAT_PRECISION),
                         label=self._node_formatter(lbl))
            plt.legend()
            plt.xticks()
            plt.yticks()
            plt.xlabel('Time (ms)')
            plt.ylabel('Rank')
            plt.suptitle("Rank over time")
            plt.title(ANNOTATION, fontsize=6)
            plt.show()


#
# Utility functions
#


class ConditionalSilencer(object):
    def __init__(self, condition):
        self._condition = condition

    def __call__(self, func):
        if not self._condition:
            return func  # Return the function unchanged, not decorated.

        def wrapper(*args, **kwargs):
            with output_silencer():
                return func(*args, **kwargs)

        return wrapper


@contextmanager
def output_silencer(file_name=os.devnull):
    with open(file_name, "w") as new_target:
        old_stdout, sys.stdout = sys.stdout, new_target
        old_stderr, sys.stderr = sys.stderr, new_target
        try:
            yield new_target
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
