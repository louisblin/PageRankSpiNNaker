import argparse
import random
import sys

import networkx as nx
import tqdm

import page_rank.model.tools.simulation as sim


def _mk_label(n):
    return '#%d' % n


def _mk_edges(node_count, edge_count):
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


def mk_graph(node_count, edge_count):
    labels = map(_mk_label, list(range(node_count)))
    edges = _mk_edges(node_count, edge_count)

    return edges, labels


def runner(fn, runs=1, node_count=None, edge_count=None, **kwargs):
    errors = 0
    for _ in tqdm.tqdm(range(runs), total=runs):
        while True:
            edges, labels = mk_graph(node_count, edge_count)
            try:
                is_correct = fn(edges=edges, labels=labels, **kwargs)
                errors += 0 if is_correct else 1
                break
            # Redo iteration because generated graph did not converge
            except nx.PowerIterationFailedConvergence:
                print('Skipping nx.PowerIterationFailedConvergence graph...')
    return errors
