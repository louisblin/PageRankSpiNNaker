import argparse
import random
import os
import sys
import time

import tqdm
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import page_rank.model.tools.simulation as sim
from page_rank.examples.utils import runner, save_plot_data, mk_path
from page_rank.examples.tune_time_scale_factor import sim_worker

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms
TSF_MIN = 575
TSF_RES = 10


def _sim_worker(edges=None, labels=None, **tsf_kwargs):
    tsf = sim_worker(edges, labels, verify=False, pause=False, **tsf_kwargs)

    # params = dict(time_scale_factor=tsf)
    # with sim.PageRankSimulation(
    #         RUN_TIME, edges, labels, params,
    #         log_level=sim.LOG_HIGHLIGHTS) as s:
    #     # Init graph for PR, and compute
    #     s.run()
    #     s.draw_input_graph(show_graph=False)
    #     start = time.time()
    #     try:
    #         # Ensure all iterations will be completed with a unrealistic tol
    #         s.compute_page_rank(max_iter=N_ITER, tol=1e-100)
    #         raise RuntimeError('Did not complete all iterations')
    #     except nx.PowerIterationFailedConvergence:
    #         pass
    #     pyt = time.time() - start

    return tsf, 0  # pyt


def run(core_min=None, core_step=None, core_max=None, show_out=None):
    cores = list(range(core_min, core_max + 1, core_step))

    n_sizes = []
    tsfs = []
    pyts = []
    tsf = TSF_MIN

    for n_core in tqdm.tqdm(cores):
        node_count = 255 * n_core
        edge_count = 10 * node_count

        # Try to find tsf as fast as possible
        for i in range(10):
            tsf_max = tsf + 2 ** i * 100
            tsf, pyt = runner(
                _sim_worker, node_count=node_count, edge_count=edge_count,
                tsf_min=tsf, tsf_res=TSF_RES, tsf_max=tsf_max)
            if tsf + TSF_RES < tsf_max:
                break

        n_sizes.append(node_count + edge_count)
        tsfs.append(tsf)
        pyts.append(pyt)

    return do_plot(n_sizes, tsfs, pyts, show_out)


def do_plot(n_sizes, tsfs, pyts, show_out=False):
    print("Displaying graph. "
          "Check DISPLAY={} if this hangs...".format(os.getenv('DISPLAY')))
    plt.clf()

    # Normalise data
    raw_data = np.array([n_sizes, tsfs, pyts])
    n_sizes = np.array(n_sizes) / (255 + 255*10)  # size => cores
    tsfs = np.array(tsfs) / float(tsfs[0])
    pyts = np.array(pyts) / float(pyts[0])
    print('\n=== DATA [n_sizes, tsfs, pyts] ===\n{}'.format(
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
        n_sizes_proj, pyts_proj = n_sizes[idx-1:], p(n_sizes)[idx-1:]
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
    plt.suptitle("Page Rank (PR) scalability of Python vs. SpiNNaker")
    plt.title("Graph size in cores, each core manages |V|=255, |E|=2,550. "
              "15 cores / chip.\nPR complexity is O(|V|+|E|), hence the linear "
              "fit  --  Average speed-up: x%.02f" % speedup, fontsize=8)

    save_plot_data('plots/graph_size_vs_running_time', raw_data)

    if show_out:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plots graph size vs. Python / SpiNNaker running times.')
    parser.add_argument('core_min', metavar='CORE_MIN', type=int, default=1)
    parser.add_argument('core_step', metavar='CORE_STEP', type=int, default=1)
    parser.add_argument('core_max', metavar='CORE_MAX', type=int, default=15)
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    sys.exit(run(**vars(parser.parse_args())))