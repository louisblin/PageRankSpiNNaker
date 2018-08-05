#!/usr/bin/env python
"""
Pool-based monitoring of the live logs of the smallest job ID running
"""
import os
import nmpi
import time

USERNAME = 'llb'
COLLAB_ID = 14744

c = nmpi.Client(USERNAME)
latest_job = int(c.completed_jobs(COLLAB_ID)[0].split('/')[-1])
URI = c.resource_map['queue'] + '/{}'


def find_running_job(curr):
    try:
        status = c.job_status(URI.format(curr + 1))
        if status == 'submitted':
            return curr
        print('Skipping job #{} ({})...'.format(curr, status))
        return find_running_job(curr + 1)
    except Exception as ex:
        if 'no such job' in str(ex).lower():
            return curr
        else:
            raise ex

while True:
    latest_job = find_running_job(latest_job)
    log = c.get_job(URI.format(latest_job))['log']

    os.system('clear && date')
    print('\nLatest job #{}...\n{}\n|=> job={}'.format(latest_job, log, latest_job))

    time.sleep(.1)
