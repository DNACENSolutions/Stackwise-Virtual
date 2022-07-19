'''
svl_job.py

This job is to launch the script: scripts/stackwise_virtual.py.

This should be run in your python environment with pyats installed. 

Run this job from parent directory:
    pyats run job job/svl_job.py --testbed ./testbed/9500_sv_tb.yaml

Support Platform: Linux/MAC/Ubuntu

'''
# see https://pubhub.devnetcloud.com/media/pyats/docs/easypy/jobfile.html
# for how job files work

# optional author information
# (update below with your contact information if needed)
__author__ = 'Cisco Systems Inc.'
__copyright__ = 'Copyright (c) 2019, Cisco Systems Inc.'
__contact__ = ['pawansi@cisco.com']
__credits__ = ['list', 'of', 'credit']
__version__ = 1.0

import io
import os
import time
from pyats.easypy import run
from pyats.easypy import Task
# compute the script path from this location
SCRIPT_PATH = os.path.dirname("./")
MAX_TASK_WAIT_TIME=3600
def main(runtime):
    '''job file entrypoint'''
    print(runtime.testbed)
    if "switchstackinggroups" not in runtime.testbed.custom.keys():
        print("switchstackinggroups infor is missing in the testbed")
        return False
    job_list=[]
    script_name = os.path.join(SCRIPT_PATH,'scripts/stackwise_virtual.py')
    for svl_pair in runtime.testbed.custom['switchstackinggroups']:
        print(svl_pair)
        task1 = Task(testscript = script_name,
                        runtime=runtime,
                        svl_pair=svl_pair,
                        taskid = f"SVLTask-{script_name.split('/')[-1]}-{svl_pair['platformType']}:{svl_pair['switchs']}")
        job_list.append(task1)
        # start the task
        task1.start()
        time.sleep(1)

    # wait for a max runtime of 60*5 seconds = 5 minutes
    for task1 in job_list:
        result = task1.wait(MAX_TASK_WAIT_TIME)
        print(result)
