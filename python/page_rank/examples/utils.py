import fnmatch
import os
import random
from multiprocessing import Process
from time import sleep

import numpy as np

from page_rank.model.tools.utils import install_requirements, \
    PageRankNoConvergence, getLogger


def _mk_label(n):
    return '#%d' % n


def _mk_edges(node_count, edge_count):
    import tqdm

    # Under these constraints we can comply with the requirements below
    assert node_count <= edge_count <= node_count ** 2, \
        "Need node_count=%d < edge_count=%d < %d " % (node_count,
        edge_count, node_count ** 2)

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

    if fnmatch.fnmatch(path, '*.*'):
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


def save_plot_data(path, data):
    import matplotlib.pyplot as plt

    save_dir = mk_path(path)
    i = max(map(int, [f[4:-4] for f in os.listdir(save_dir)] + [0])) + 1

    np.savetxt(os.path.join(save_dir, 'run-%d.csv' % i), data, delimiter=',')
    plt.savefig(os.path.join(save_dir, 'run-%d.png' % i))

    print('\n>>> Results saved at %s/run-%d.*' % (save_dir, i))


def mk_graph(node_count, edge_count):
    labels = map(_mk_label, list(range(node_count)))
    edges = _mk_edges(node_count, edge_count)

    return edges, labels


def runner(fn, node_count=None, edge_count=None, **kwargs):
    while True:
        edges, labels = mk_graph(node_count, edge_count)
        try:
            return fn(edges=edges, labels=labels, **kwargs)
        # Redo iteration because generated graph did not converge
        except PageRankNoConvergence:
            print('Skipping PageRankNoConvergence graph...')


def setup_cli_and_run(parser, fn):
    parser.add_argument('-t', '--timeout', type=int, default=None,
                        help='Simulation timeout. Default is no timeout.')
    parser.add_argument('--hbp', action='store_true', help='Is running on HBP.')
    kwargs = dict(vars(parser.parse_args()))

    timeout = kwargs.pop('timeout')
    hbp = kwargs.pop('hbp')

    # Install requirements missing on HBP
    if hbp:
        import matplotlib
        matplotlib.use('Agg')
        install_requirements()

    # Set timer to terminate simulation after `timeout` seconds
    p = None
    if timeout is not None:
        def worker(pid):
            getLogger().important('Will time out in {} sec...'.format(timeout))
            sleep(timeout)

            getLogger().error('Timing out after {} sec!'.format(timeout))
            os.system('kill -TERM %d' % pid)

        p = Process(target=worker, args=(os.getpid(),))
        p.start()

    # Run simulation
    try:
        exit(fn(**kwargs))
    finally:
        # Cancel timer
        if p is not None:
            p.terminate()
