import argparse
import random
import sys
import time

import numpy as np

from page_rank.examples.utils import runner, save_plot_data, setup_cli_and_run
from page_rank.model.tools.utils import graph_visualiser, LOG_IMPORTANT, \
    PageRankNoConvergence, getLogger

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by time step in ms
TSF_MIN = 20
TSF_RES = .1  # % of tsf.

_logger = getLogger()


def _sim_worker(edges=None, labels=None, skip_python=False, **tsf_kwargs):
    from page_rank.model.tools.simulation import PageRankSimulation
    from page_rank.examples.tune_time_scale_factor import sim_worker

    tsf = sim_worker(edges, labels, verify=False, pause=False, **tsf_kwargs)
    pyt = 0

    # Skip python run (takes too long on large graphs)
    if skip_python:
        _logger.warning('Skipping Python run')
        return tsf, pyt

    # Compute python Page Rank running time
    params = dict(time_scale_factor=tsf)
    with PageRankSimulation(
            RUN_TIME, edges, labels, params, log_level=LOG_IMPORTANT) as s:
        start = time.time()
        try:
            # Ensure all iterations will be completed with a unrealistic tol
            s.do_python_page_rank(max_iter=N_ITER, tol=1e-100)
            raise RuntimeError('Did not complete all iterations')
        except PageRankNoConvergence:
            pass
        pyt = time.time() - start

    return tsf, pyt


def run(cores=None, show_out=None, skip_python_from=None):
    import tqdm

    n_sizes = []
    tsfs = []
    pyts = []
    tsf = TSF_MIN

    for n_core in tqdm.tqdm(cores):
        node_count = 255 * n_core
        edge_count = 10 * node_count
        skip_python = n_core >= skip_python_from

        tsf, pyt = runner(
            _sim_worker, node_count=node_count, edge_count=edge_count,
            tsf_min=tsf, tsf_res=TSF_RES, skip_python=skip_python)

        n_sizes.append(n_core)
        tsfs.append(tsf)
        pyts.append(pyt)
        _logger.important('[cores={}] [n_sizes, tsfs] =\n{}'.format(
            n_core, np.array([n_sizes, tsfs])))

    do_plot(n_sizes, tsfs, pyts, show_graph=show_out)


@graph_visualiser
def do_plot(n_sizes, tsfs, pyts):
    import matplotlib.pyplot as plt

    raw_data = np.array([n_sizes, tsfs, pyts])

    # Normalise data
    n_sizes = np.array(n_sizes)
    tsfs = np.array(tsfs) / float(tsfs[0])
    if float(pyts[0]) != 0:
        pyts = np.array(pyts) / float(pyts[0])

    _logger.important('\n\n=== DATA [n_sizes, tsfs, pyts] ===\n{}'.format(
        np.array([n_sizes, tsfs, pyts])))

    # If python values are missing (from skip_python_from option), assume big
    # scales (log-log graph) and complete the curve with a trend line (linear
    # fitting as PR is O(|V|+|E|))
    if any(np.where(pyts == 0)[0]):
        idx = np.where(pyts == 0)[0][0]
        valid_n_sizes, valid_pyts = n_sizes[:idx], pyts[:idx]

        plt.loglog(valid_n_sizes, valid_pyts, 'r-', basex=2, basey=2,
                   label="Python running time")

        # For missing values, add a trend line
        z = np.polyfit(valid_n_sizes, valid_pyts, 1)
        p = np.poly1d(z)
        n_sizes_proj, pyts_proj = n_sizes[idx - 1:], p(n_sizes)[idx - 1:]
        plt.loglog(n_sizes_proj, pyts_proj, 'r--', basex=2, basey=2,
                   label="Linear fitting projection")

        # SpiNNaker run time
        plt.loglog(n_sizes, tsfs, 'b-', basex=2, basey=2,
                   label="SpiNNaker running time")

        speedup = (p(n_sizes) / tsfs).mean()
        plt.grid(True)
    # Otherwise, use a normal graph
    else:
        plt.plot(n_sizes, pyts, 'r-', label="Python running time")
        plt.plot(n_sizes, tsfs, 'b-', label="SpiNNaker running time")

        speedup = (pyts / tsfs).mean()

    plt.legend()
    plt.xticks()
    plt.yticks()
    plt.xlabel('Graph size (in #cores at full computational load)')
    plt.ylabel('Run time (in arbitrary unit)')
    # plt.suptitle("Page Rank (PR) scalability of Python vs. SpiNNaker")
    plt.title("Graph size in cores, each core manages |V|=255, |E|=2,550. "
              "15 cores / chip.\nPR complexity is O(|V|+|E|), hence the linear "
              "fit  --  Average speed-up: x%.02f" % speedup, fontsize=9)

    save_plot_data('plots/graph_size_vs_running_time', raw_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plots graph size vs. Python / SpiNNaker running times.')
    parser.add_argument('cores', nargs='+', type=int)
    parser.add_argument('-s', '--skip-python-from', type=int,
                        default=sys.maxsize, help='# Core to skip python from')
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    setup_cli_and_run(parser, run)
