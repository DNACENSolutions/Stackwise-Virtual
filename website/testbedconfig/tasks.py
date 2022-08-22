import os
from pathlib import Path
import subprocess
from subprocess import Popen
from celery import shared_task


@shared_task
def create_SWV(file, id):
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    print(base_dir)
    os.chdir(base_dir / "Stackwise-Virtual")
    print(os.getcwd())
    from job.svl_job import run
    process = Popen(["./stackwisevirtual.sh", "-c", file], stdout=subprocess.PIPE)
    id = id + ".txt"
    output = process.stdout.read()
    file = open(id, 'w')
    file.write(output.decode("utf-8"))
    #run(file)
    print(run)
    return True
 
# def delete_SWV(file):
#     base_dir = Path(__file__).resolve().parent.parent.parent.parent
#     os.chdir(base_dir / "Stackwise-Virtual")
#     return Popen(["./stackwisevirtual.sh", "-d", file])

# def update_SWV(file):
#     base_dir = Path(__file__).resolve().parent.parent.parent.parent
#     os.chdir(base_dir / "Stackwise-Virtual")
#     return Popen(["./stackwisevirtual.sh", "-u", file])