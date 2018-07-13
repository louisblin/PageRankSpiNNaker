import argparse
import gzip
import os
import site
import tempfile

from page_rank.examples.tune_time_scale_factor import sim_worker
from page_rank.examples.utils import setup_cli_and_run

# Info here: https://snap.stanford.edu/data/web-Google.html
DATA_SET_URL = "https://snap.stanford.edu/data/web-Google.txt.gz"
TSF_MIN = 1000
TSF_RES = .1  # % of tsf.
RUN_TIME = 250 * .1  # time step


def _get_edges():
    # Install and import requests, not in project requirements.txt
    os.system('pip install --user requests')
    reload(site)
    import requests

    file_name = tempfile.mktemp()
    with open(file_name, "wb") as f:
        r = requests.get(DATA_SET_URL)
        f.write(r.content)

    with gzip.open(file_name, 'rb') as f:
        lines = f.readlines()
        lines = [str(l).strip() for l in lines]
        return [tuple(l.split('\t')) for l in lines if not l.startswith('#')]


def run():
    tsf = sim_worker(_get_edges(), tsf_min=TSF_MIN, tsf_res=TSF_RES)
    millis = tsf * RUN_TIME

    print('Ran Page Rank in {}ms'.format(millis))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Using webgraph from the Google programming contest, 2002.")

    setup_cli_and_run(parser, run)
