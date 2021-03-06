import argparse
import math
import random

import numpy as np

from page_rank.examples.tune_time_scale_factor import sim_worker
from page_rank.examples.utils import runner, save_plot_data, setup_cli_and_run
from page_rank.model.tools.utils import graph_visualiser

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms
TSF_MIN = 50
TSF_RES = 10
TSF_MAX = 300


def run(node_count=None, cores=None, show_out=None):
    import tqdm

    # Fit the same graph size onto 1, 2, ... 15 cores
    atoms_per_core_list = []
    for n_cores in cores:
        atoms_per_core_list.append(math.ceil(node_count / float(n_cores)))

    tsfs = []
    for atoms_per_core in tqdm.tqdm(atoms_per_core_list):
        tsf = runner(sim_worker, node_count=node_count,
                     edge_count=10 * node_count, atoms_per_core=atoms_per_core,
                     tsf_min=TSF_MIN, tsf_res=TSF_RES, tsf_max=TSF_MAX)
        tsfs.append(tsf)

    return do_plot(cores, tsfs, node_count, show_graph=show_out)


@graph_visualiser
def do_plot(cores, tsfs, node_count):
    import matplotlib.pyplot as plt

    # Need a 2D matrix to save as csv - copy node_count
    if hasattr(node_count, '__len__'):
        node_count_row = node_count
        node_count = node_count[0]
    else:
        node_count_row = [node_count] * len(cores)
    raw_data = np.array([cores, tsfs, node_count_row])

    # Normalise data
    tsfs = np.array(tsfs) / float(tsfs[0]) * 100
    print('\n=== DATA [cores, tsfs] ===\n{}'.format(np.array([cores, tsfs])))

    plt.plot(cores, tsfs, 'b-', label="SpiNNaker running time")
    plt.legend()
    plt.xticks(cores)
    plt.yticks()
    plt.xlabel('Cores')
    plt.ylabel('Run time (in arbitrary unit)')
    # plt.suptitle("Tuning number of Page Rank vertices managed by a single core")
    plt.title(("Mapping a fixed-size graph (|V|={}, |E|={}) onto a \n"
               "varying number of cores. 15 cores / chip").format(
        node_count, 10 * node_count), fontsize=9)

    save_plot_data('plots/atoms_per_core_vs_running_time', raw_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plots atoms per core vs. SpiNNaker running times.')
    parser.add_argument('node_count', metavar='NODES', type=int)
    parser.add_argument('cores', nargs='+', type=int)
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    setup_cli_and_run(parser, run)
