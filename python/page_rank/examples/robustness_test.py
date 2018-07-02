import argparse
import random

from page_rank.examples.utils import runner, setup_cli_and_run

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms
PARAMETERS = {
    # Experimental results of good values
    # |V|=400  |E|=600   : ts=1. tsf=40
    # |V|=800  |E|=1200  : ts=1. tsf=45
    # |V|=1600 |E|=2400  : ts=1. tsf=150
    # |V|=3200 |E|=4800  : ts=?  tsf=?
    # 210 for 1 core / 65K
    # 235 for 15 cores / 50,000
    # 400 for 30 cores / 20,000
    'time_scale_factor': 400,
}


def _mk_sim_run(edges=None, labels=None, verify=None, pause=None,
                show_out=None, log_level=None):
    import page_rank.model.tools.simulation as sim

    # Run simulation / report
    with sim.PageRankSimulation(RUN_TIME, edges, labels, PARAMETERS,
                                log_level=log_level, pause=pause) as s:
        is_correct = s.run(verify=verify, diff_only=True)
        s.draw_output_graph(show_graph=show_out)
        return is_correct


def run(runs=None, **kwargs):
    import tqdm

    results = [runner(_mk_sim_run, runs, **kwargs)
               for _ in tqdm.tqdm(range(runs), total=runs)]
    correct = sum(map(int, results))
    print('Finished robustness test with %d/%d passed.' % (correct, runs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run random Page Rank graphs')
    parser.add_argument('-r', '--runs', type=int, default=1,
                        help='# runs. Default is 1.')
    parser.add_argument('node_count', metavar='NODES', type=int,
                        help='# nodes per graph')
    parser.add_argument('edge_count', metavar='EDGES', type=int,
                        help='# edges per graph')
    parser.add_argument('-v', '--verify', action='store_true',
                        help='Verify sim w/ Python PR impl')
    parser.add_argument('-p', '--pause', action='store_true',
                        help='Pause after each runs')
    parser.add_argument('-o', '--show-out', action='store_true',
                        help='Display ranks curves output')
    parser.add_argument('-l', '--log-level', type=int,
                        default=sim.LOG_HIGHLIGHTS,
                        help='The integer log level to set')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    setup_cli_and_run(parser, run)
