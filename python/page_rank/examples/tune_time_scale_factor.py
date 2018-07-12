import argparse
import random

from page_rank.examples.utils import setup_cli_and_run
from page_rank.model.tools.utils import getLogger, FailedOnWarningError, \
    LOG_IMPORTANT

N_ITER = 25
RUN_TIME = N_ITER * .1  # multiplied by time step in ms
LOG_LEVEL = 20  # LOG_IMPORTANT
MAX_ITER = 15

_logger = getLogger()


def _run(tsf, edges, labels, pause, verify):
    from page_rank.model.tools.simulation import PageRankSimulation

    # Run simulation / report
    _logger.important('|> Running w/ time_scale_factor=%d\n' % tsf)
    params = dict(time_scale_factor=tsf)
    with PageRankSimulation(
            RUN_TIME, edges, labels, params, fail_on_warning=True,
            pause=pause, log_level=LOG_LEVEL) as s:
        s.run(verify=verify, diff_only=True)


def _find_tsf_range(tsf_min_in, *run_args):
    tsf_min = tsf_min_in
    tsf_max = tsf_min_in

    for i in range(MAX_ITER):
        tsf_max = tsf_min_in + (2 ** i) * 100
        _logger.important('Check tsf_max=%d\n' % tsf_max)
        try:
            _run(tsf_max, *run_args)
            return tsf_min, tsf_max
        # Raised warnings, update lower bound tsf_min on execution time
        except FailedOnWarningError:
            tsf_min = tsf_max

    raise RuntimeError('Could not find tsf_max in range ({},{}). Consider '
                       'increasing max_iter.'.format(tsf_min, tsf_max))


def _find_tsf(tsf_min, tsf_res, tsf_max, *run_args):
    # If resolution expressed as a percentage relative to tsf
    # Example: if we return tsf=50 w/ tsf_res=.1, it means the true value of tsf
    #          is in the range [45-50]
    if tsf_res < 1:
        condition = lambda t, tsf_diff: tsf_diff > t * tsf_res
    # Otherwise, resolution expressed as absolute difference
    else:
        condition = lambda t, tsf_diff: tsf_diff > tsf_res

    tsf = 0
    while condition(tsf, abs(tsf_max - tsf_min)):
        tsf = tsf_min + (tsf_max - tsf_min) // 2
        try:
            _run(tsf, *run_args)
            # No error, reduce upper bound
            tsf_max = tsf
        except FailedOnWarningError:
            # Error, increase lower bound
            tsf_min = tsf

    _logger.important('==> RESULT: time_scale_factor=%d\n' % tsf_max)
    return tsf_max


def sim_worker(edges=None, labels=None, verify=None, pause=None,
               tsf_min=None, tsf_res=None, tsf_max=None):
    run_args = (edges, labels, pause, verify)

    if tsf_max is None:
        tsf_min, tsf_max = _find_tsf_range(tsf_min, *run_args)
        _logger.important('Found range (%d,%d)\n' % (tsf_min, tsf_max))

    return _find_tsf(tsf_min, tsf_res, tsf_max, *run_args)


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
    setup_cli_and_run(parser, sim_worker)
