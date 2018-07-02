import argparse
import logging
import random
import time

import numpy as np

from page_rank.examples.utils import runner, save_plot_data, setup_cli_and_run
from page_rank.model.tools.utils import graph_visualiser, LOG_IMPORTANT, \
    PageRankNoConvergence

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms
TSF_MIN = 10
TSF_RES = 200


def _log_info(*args, **kwargs):
    logging.warning(*args, **kwargs)


def _sim_worker(edges=None, labels=None, skip_python=None, **tsf_kwargs):
    from page_rank.examples.tune_time_scale_factor import sim_worker

    tsf = sim_worker(edges, labels, verify=False, pause=False, **tsf_kwargs)
    pyt = 0

    if skip_python:
        return tsf, pyt

    import page_rank.model.tools.simulation as sim
    params = dict(time_scale_factor=tsf)
    with sim.PageRankSimulation(
            RUN_TIME, edges, labels, params, log_level=LOG_IMPORTANT) as s:
        # Init graph for PR, and compute
        s.run()
        s.draw_input_graph(show_graph=False)
        start = time.time()
        try:
            # Ensure all iterations will be completed with a unrealistic tol
            s.do_python_page_rank(max_iter=N_ITER, tol=1e-100)
            raise RuntimeError('Did not complete all iterations')
        except PageRankNoConvergence:
            pass
        pyt = time.time() - start

    return tsf, pyt


def run(cores=None, show_out=None):
    import tqdm

    n_sizes = []
    tsfs = []
    pyts = []
    tsf_max = TSF_MIN
    tsf_min = TSF_MIN

    for n_core in tqdm.tqdm(cores):
        node_count = 255 * n_core
        edge_count = 10 * node_count

        # # Try to find tsf as fast as possible
        # for i in range(10):
        #     tsf_max = tsf + 2 ** i * 100
        #     _log_info('[cores={}] Checking range ({}, {})\n'.format(n_core, tsf, tsf_max))
        #     tsf, pyt = runner(
        #         _sim_worker, node_count=node_count, edge_count=edge_count,
        #         tsf_min=tsf, tsf_res=TSF_RES, tsf_max=tsf_max)
        #     if tsf + TSF_RES < tsf_max:
        #         break

        # Try to find tsf as fast as possible
        for i in range(15):
            tsf_max = tsf_min + 2 ** i * 100
            _log_info(
                '[cores={}] Checking range ({}, {})\n'.format(n_core, tsf_min,
                                                              tsf_max))
            tsf, pyt = runner(
                _sim_worker, node_count=node_count, edge_count=edge_count,
                tsf_min=tsf_max - TSF_RES - 1, tsf_res=TSF_RES, tsf_max=tsf_max)
            if tsf < tsf_max:
                break
            tsf_min = tsf

        _log_info('[cores={}] Found range ({}, {})\n'.format(n_core, tsf_min,
                                                             tsf_max))
        tsf, pyt = runner(
            _sim_worker, node_count=node_count, edge_count=edge_count,
            tsf_min=tsf_min, tsf_res=TSF_RES, tsf_max=tsf_max)

        n_sizes.append(node_count + edge_count)
        tsfs.append(tsf)
        pyts.append(pyt)
        _log_info(
            '[cores={}] CURR =>>\n{}'.format(n_core, np.array([n_sizes, tsfs])))

        do_plot(n_sizes, tsfs, pyts, show_graph=show_out, save_graph=True)
        exit(0)  # TODO: remove me


@graph_visualiser
def do_plot(n_sizes, tsfs, pyts):
    import matplotlib.pyplot as plt

    # Normalise data
    raw_data = np.array([n_sizes, tsfs, pyts])
    n_sizes = np.array(n_sizes) / (255 + 255 * 10)  # size => cores
    tsfs = np.array(tsfs) / float(tsfs[0])
    # pyts = np.array(pyts) / float(pyts[0])
    _log_info('\n=== DATA [n_sizes, tsfs, pyts] ===\n{}'.format(
        np.array([n_sizes, tsfs, pyts])))

    # Python runtime with with trend line (linear fitting as PR is O(|V|+|E|))
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
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    setup_cli_and_run(parser, run)
