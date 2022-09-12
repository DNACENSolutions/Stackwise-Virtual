import os
from pathlib import Path
import subprocess
from subprocess import Popen
from celery import shared_task
import datetime
from datetime import datetime
from celery.utils.log import get_task_logger
logger = get_task_logger("TASK LOG")

@shared_task
def create_SWV(file, id):
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    logger.info(base_dir)
    os.chdir(base_dir / "/pyats/sol_eng_stackwise_virtual")
    logger.info(os.getcwd())
    process = Popen(["pyats","run","job","job/svl_job.py","--testbed",("website/files/testbeds/"+file)],stdout=subprocess.PIPE)
    id = id +".txt"
    output = process.stdout.read()
    logger.info(output)
    file = open(id, 'w')
    file.write(output.decode("utf-8"))
    return True
