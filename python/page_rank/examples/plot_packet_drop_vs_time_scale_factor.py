import argparse
import random
import os
import sys

import tqdm
import matplotlib.pyplot as plt
import numpy as np

from page_rank.model.tools.simulation import PageRankSimulation, LOG_HIGHLIGHTS
from page_rank.examples.utils import runner, save_plot_data, \
    extract_router_provenance

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms
PROVENANCE_ITEMS = [
    'total_dropped_packets',  # Network overflow
    'total_lost_dropped_packets',  # MC packets effectively dumped
    'Dumped_from_a_processor',  # CPU overflow
]


def _sim_worker(edges=None, labels=None, tsf=None):
    params = dict(time_scale_factor=tsf)
    with PageRankSimulation(RUN_TIME, edges, labels, params,
                            log_level=LOG_HIGHLIGHTS) as s:
        s.run()
        prov = extract_router_provenance(PROVENANCE_ITEMS)

    return [prov[name] for name in PROVENANCE_ITEMS]


def run(node_count=None, tsf_min=None, tsf_step=None, tsf_max=None,
        show_out=None):
    edge_count = node_count * 10
    tsfs = list(range(tsf_min, tsf_max + 1, tsf_step))
    prov_list = []

    for tsf in tqdm.tqdm(tsfs):
        prov_list.append(runner(
            _sim_worker, node_count=node_count, edge_count=edge_count, tsf=tsf))

    return do_plot(tsfs, prov_list, node_count, show_out=show_out)


def do_plot(tsfs, prov_list, node_count, show_out=False):
    print("Displaying graph. "
          "Check DISPLAY={} if this hangs...".format(os.getenv('DISPLAY')))
    plt.clf()

    # Normalise data
    x = np.array([tsfs]).reshape(-1, 1)
    data = np.concatenate((x, prov_list), axis=1)
    print('\n\n=== DATA [tsfs prov_list..] ===\n{}'.format(data))

    for idx, label in enumerate(PROVENANCE_ITEMS):
        y = data[:, idx + 1] / 1000.
        plt.plot(x, y, label=label.replace('_', ' ').lower())
    plt.legend()
    plt.xticks()
    plt.yticks()
    plt.xlabel('Time allowance (in time_scale_factor)')
    plt.ylabel('Packets dropped (x1000)')
    # plt.suptitle("Tuning hardware time step to avoid dropping packets")
    plt.title(("Fixed-size graph (|V|={}, |E|={}). "
               "255 vertices / core, 15 cores / chip").format(
        node_count, 10 * node_count), fontsize=9)

    save_plot_data('plots/packet_drop_vs_time_scale_factor', data)

    if show_out:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plots graph size vs. Python / SpiNNaker running times.')
    parser.add_argument('node_count', metavar='NODES', type=int)
    parser.add_argument('tsf_min', metavar='TSF_MIN', type=int)
    parser.add_argument('tsf_step', metavar='TSF_STEP', type=int)
    parser.add_argument('tsf_max', metavar='TSF_MAX', type=int)
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    sys.exit(run(**vars(parser.parse_args())))
