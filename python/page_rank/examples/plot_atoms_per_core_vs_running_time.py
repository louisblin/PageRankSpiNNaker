import argparse
import math
import random
import os
import sys

import tqdm
import matplotlib.pyplot as plt
import numpy as np

from page_rank.examples.utils import runner, save_plot_data
from page_rank.examples.tune_time_scale_factor import sim_worker

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms
TSF_MIN = 50
TSF_RES = 10
TSF_MAX = 300


def run(node_count=None, core_min=None, core_step=None, core_max=None,
        show_out=None):
    cores = list(range(core_min, core_max+1, core_step))

    # Fit the same graph size of 1, 2, ... 15 cores
    atoms_per_core_list = []
    for n_cores in cores:
        atoms_per_core_list.append(math.ceil(node_count / float(n_cores)))

    tsfs = []
    for atoms_per_core in tqdm.tqdm(atoms_per_core_list):
        tsf = runner(sim_worker, node_count=node_count,
                     edge_count=10 * node_count, atoms_per_core=atoms_per_core,
                     tsf_min=TSF_MIN, tsf_res=TSF_RES, tsf_max=TSF_MAX)
        tsfs.append(tsf)

    return do_plot(cores, tsfs, node_count, show_out=show_out)


def do_plot(cores, tsfs, node_count, show_out=False):
    print("Displaying graph. "
          "Check DISPLAY={} if this hangs...".format(os.getenv('DISPLAY')))
    plt.clf()

    # Normalise data
    raw_data = np.array([cores, tsfs])
    tsfs = np.array(tsfs) / float(tsfs[0]) * 100
    print('\n=== DATA [cores, tsfs] ===\n{}'.format(np.array([cores, tsfs])))

    plt.plot(cores, tsfs, 'b-', label="SpiNNaker running time")
    plt.legend()
    plt.xticks(cores)
    plt.yticks()
    plt.xlabel('Cores')
    plt.ylabel('Run time (in arbitrary unit)')
    plt.suptitle("Tuning number of Page Rank vertices managed by a single core")
    plt.title(("Mapping a fixed-size graph (|V|={}, |E|={}) onto a varying "
               "number of SpiNNaker cores.\n15 cores / chip").format(
        node_count, 10 * node_count), fontsize=8)

    save_plot_data('plots/atoms_per_core_vs_running_time', raw_data)

    if show_out:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plots atoms per core vs. SpiNNaker running times.')
    parser.add_argument('node_count', metavar='NODES', type=int)
    parser.add_argument('core_min', metavar='CORE_MIN', type=int, default=1)
    parser.add_argument('core_step', metavar='CORE_STEP', type=int, default=1)
    parser.add_argument('core_max', metavar='CORE_MAX', type=int, default=15)
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    sys.exit(run(**vars(parser.parse_args())))
