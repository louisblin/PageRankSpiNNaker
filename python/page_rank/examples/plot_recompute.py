import argparse
import random
import os

import numpy as np

from page_rank.examples.plot_atoms_per_core_vs_running_time \
    import do_plot as do_plot_1
from page_rank.examples.plot_graph_size_vs_running_time \
    import do_plot as do_plot_2
from page_rank.examples.plot_packet_drop_vs_time_scale_factor \
    import do_plot as do_plot_3
from page_rank.examples.utils import setup_cli


def replot(csv=None, node_count=None, rm=False, show_out=None):
    data = np.loadtxt(csv, delimiter=',')
    graph_args = dict(show_graph=show_out, save_graph=True)

    if 'atoms_per_core_vs_running_time' in csv:
        do_plot_1(data[0], data[1], node_count, **graph_args)

    if 'graph_size_vs_running_time' in csv:
        do_plot_2(data[0], data[1], data[2], **graph_args)

    if 'packet_drop_vs_time_scale_factor' in csv:
        do_plot_3(data[:, 0], data[:, 1:], node_count, **graph_args)

    if rm:
        os.unlink(csv)
        os.unlink(csv[:-4] + '.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plots graph size vs. Python / SpiNNaker running times.')
    parser.add_argument('csv', help='CSV data file to recompute from')
    parser.add_argument('-n', '--node-count', type=int)
    parser.add_argument('-r', '--rm', action='store_true')
    parser.add_argument('-o', '--show-out', action='store_true')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    setup_cli(parser, replot)
