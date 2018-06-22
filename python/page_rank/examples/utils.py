import importlib
import os
import random
import re

import numpy as np
import pip

from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.interface.interface_functions \
    import RouterProvenanceGatherer


def _mk_label(n):
    return '#%d' % n


def _mk_edges(node_count, edge_count):
    import tqdm

    # Under these constraints we can comply with the requirements below
    assert node_count <= edge_count <= node_count ** 2, \
        "Need node_count=%d < edge_count=%d < %d " % (node_count, edge_count,
                                                      node_count ** 2)

    def _mk_node():
        return random.randint(0, node_count - 1)

    # Ensures no double edges
    edges = set([])

    # Ensures no dangling nodes
    for i in range(node_count):
        edges.add((i, _mk_node()))

    for _ in tqdm.tqdm(range(node_count, edge_count), desc="Generating edges",
                       initial=node_count, total=edge_count):
        while True:
            prev_len = len(edges)
            edges.add((_mk_node(), _mk_node()))
            if len(edges) > prev_len:
                break
            # else, continue because we've added an already existing edge

    # Map node ids to formatted strings
    return [(_mk_label(src), _mk_label(tgt))
            for src, tgt in tqdm.tqdm(edges, desc="Formatting edges")]


def mk_path(path):
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), path))

    if re.match('.*\..*', path):
        dir_path = os.path.dirname(path)
    else:
        dir_path = path

    build_stack = []
    while not os.path.exists(dir_path):
        build_stack.append(dir_path)
        dir_path = os.path.dirname(dir_path)

    for d in reversed(build_stack):
        os.makedirs(d)

    return path


def save_plot_data(path, raw_data):
    import matplotlib.pyplot as plt

    save_dir = mk_path(path)
    i = max(map(int, [f[4:-4] for f in os.listdir(save_dir)])) + 1
    np.savetxt(os.path.join(save_dir, 'run-%d.csv' % i), raw_data, delimiter=',')
    plt.savefig(os.path.join(save_dir, 'run-%d.png' % i))
    print('\n>>> Results saved at %s/run-%d.*' % (save_dir, i))


def mk_graph(node_count, edge_count):
    labels = map(_mk_label, list(range(node_count)))
    edges = _mk_edges(node_count, edge_count)

    return edges, labels


def runner(fn, node_count=None, edge_count=None, **kwargs):
    import networkx as nx

    while True:
        edges, labels = mk_graph(node_count, edge_count)
        try:
            return fn(edges=edges, labels=labels, **kwargs)
        # Redo iteration because generated graph did not converge
        except nx.PowerIterationFailedConvergence:
            print('Skipping nx.PowerIterationFailedConvergence graph...')


def extract_router_provenance(collect_names=None):
    if collect_names is None:
        collect_names = [
            'total_multi_cast_sent_packets',
            'total_created_packets',
            'total_dropped_packets',
            'total_missed_dropped_packets',
            'total_lost_dropped_packets'
        ]

    m = globals_variables.get_simulator()

    router_provenance = RouterProvenanceGatherer()
    router_prov = router_provenance(m._txrx, m._machine, m._router_tables, True)

    res = dict().fromkeys(collect_names, 0)
    for item in router_prov:
        print('{} => {}'.format(item.names, item.value))
        name = item.names[-1]
        if name in collect_names:
            res[name] += int(item.value)

    return res


def _install_and_import(package, version):
    fname = '{}=={}'.format(package, version)
    try:
        importlib.import_module(package)
    except ImportError:
        pip.main(['install', '--user', fname])
    finally:
        import site
        reload(site)
        globals()[package] = importlib.import_module(package)


def install_requirements():
    import matplotlib
    matplotlib.use('Agg')
    _install_and_import('networkx' , '2.1')
    _install_and_import('prettytable', '0.7.2')
    _install_and_import('tqdm', '4.23.4')