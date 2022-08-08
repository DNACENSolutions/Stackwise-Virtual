import os
from pathlib import Path
from subprocess import Popen

def create_SWV(file):
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    os.chdir(base_dir / "Stackwise-Virtual")
    return Popen(["./stackwisevirtual.sh", "-c", file])

def delete_SWV(file):
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    os.chdir(base_dir / "Stackwise-Virtual")
    return Popen(["./stackwisevirtual.sh", "-d", file])

def update_SWV(file):
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    os.chdir(base_dir / "Stackwise-Virtual")
    return Popen(["./stackwisevirtual.sh", "-u", file])