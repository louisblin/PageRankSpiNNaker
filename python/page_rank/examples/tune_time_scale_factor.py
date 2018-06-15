import argparse
import random
import sys

import page_rank.model.tools.simulation as sim
from page_rank.examples.utils import runner

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by timestep in ms


def _mk_sim_run(edges=None, labels=None, verify=None, pause=None,
                tsf_min=None, tsf_res=None, tsf_max=None):
    tsf = None

    while abs(tsf_max - tsf_min) > tsf_res:
        try:
            tsf = tsf_min + (tsf_max - tsf_min) // 2

            # Run simulation / report
            print('\n|> Running with time_scale_factor={}'.format(tsf))
            params = dict(time_scale_factor=tsf)
            with sim.PageRankSimulation(
                    RUN_TIME, edges, labels, params, fail_on_warning=True,
                    pause=pause, log_level=sim.LOG_LEVEL_PAGE_RANK_INFO) as s:
                s.run(verify=verify, diff_only=True)

            # No error, reduce tsf
            tsf_max = tsf
        except sim.FailedOnWarningError:
            # No error, increase tsf
            tsf_min = tsf

    print('RESULT: time_scale_factor={}'.format(tsf))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run random Page Rank graphs')
    parser.add_argument('node_count', metavar='NODES', type=int,
                        help='# nodes per graph')
    parser.add_argument('edge_count', metavar='EDGES', type=int,
                        help='# edges per graph')
    parser.add_argument('tsf_min', metavar='TSF_MIN', type=int,
                        help='min time_scale_factor')
    parser.add_argument('tsf_res', metavar='TSF_res', type=int, default=10,
                        help='time_scale_factor resolution. Default is 10.')
    parser.add_argument('tsf_max', metavar='TSF_MAX', type=int,
                        help='max time_scale_factor')
    parser.add_argument('-v', '--verify', action='store_true',
                        help='Verify sim w/ Python PR impl')
    parser.add_argument('-p', '--pause', action='store_true',
                        help='Pause after each runs')

    # Recreate the same graphs for the same arguments
    random.seed(42)
    sys.exit(runner(_mk_sim_run, **vars(parser.parse_args())))
