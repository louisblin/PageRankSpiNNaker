#!/usr/bin/env python
"""
Pool-based monitoring of the queue of jobs submitted on HBP
"""
import os
import nmpi
import time

USERNAME = 'llb'
COLLAB_ID = 14744

c = nmpi.Client(USERNAME)

while True:
    queued = c.queued_jobs()
    completed = c.completed_jobs(COLLAB_ID)

    os.system('clear && date')
    print(  '====== QUEUE[%d] ======' % len(queued))
    for j in queued:
        print(j)

    print('\n==== FINISHED[%d] ====' % len(completed))
    for j in completed[:10]:
        print(j)
    if len(completed) >  10:
        print('...')

    time.sleep(3)
