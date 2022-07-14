import yaml
from pathlib import Path
import subprocess
from subprocess import Popen, PIPE, STDOUT
import os

# subprocess.Popen("ls", shell=True, cwd="Stackwise-Virtual")
class RunSWV():
    def __init__(self):
        self.username = None
        self.password = None
        self.enablepassword = None
        self.hostname1 = None
        self.number1 = None
        self.priority1 = None
        self.ipaddress1 = None
        self.port1 = None
        self.protocol1 = None
        self.hostname2 = None
        self.number2 = None
        self.priority2 = None
        self.ipaddress2 = None
        self.port2 = None
        self.protocol2 = None

    def create_yaml(self):
        base_dir = Path(__file__).resolve().parent
        with open(base_dir / "testbed" / "template_tb.yaml") as f:
            template = yaml.safe_load(f)
            template["testbed"]["tacacs"]["username"] = self.username
            template["testbed"]["passwords"]["tacacs"] = self.password
            template["testbed"]["passwords"]["enable"] = self.enablepassword 
            template["testbed"]["passwords"]["line"] = self.enablepassword

            template["devices"]["SWITCH-1"]["alias"] = self.hostname1
            template["devices"]["SWITCH-1"]["custom"]["switchnumber"] = self.number1
            template["devices"]["SWITCH-1"]["custom"]["switchpriority"] = self.priority1
            template["devices"]["SWITCH-1"]["connections"]["a"]["protocol"] = self.protocol1
            template["devices"]["SWITCH-1"]["connections"]["a"]["ip"] = self.ipaddress1
            template["devices"]["SWITCH-1"]["connections"]["a"]["port"] = self.port1

            template["devices"]["SWITCH-2"]["alias"] = self.hostname2
            template["devices"]["SWITCH-2"]["custom"]["switchnumber"] = self.number2
            template["devices"]["SWITCH-2"]["custom"]["switchpriority"] = self.priority2
            template["devices"]["SWITCH-2"]["connections"]["a"]["protocol"] = self.protocol2
            template["devices"]["SWITCH-2"]["connections"]["a"]["ip"] = self.ipaddress2
            template["devices"]["SWITCH-2"]["connections"]["a"]["port"] = self.protocol2

        with open(base_dir / "testbed" / "SV_testbed.yaml", "w") as f:
           return (yaml.dump(template, f, default_flow_style=False))

    def txt_file(self):
        base_dir = Path(__file__).resolve().parent
        with open(base_dir / "testbed" / "SV_testbed.yaml") as f:
            parsed = yaml.safe_load(f)

            return yaml.dump(parsed, sort_keys=True, default_flow_style=False)

    # def run_script(self):
    #     base_dir = Path(__file__).resolve().parent.parent.parent.parent

    #     self.create_yaml()

    #     os.chdir(base_dir / "Stackwise-Virtual")
    #     subprocess.run(["./stackwisevirtual.sh", "-c", "./testbed/config_tb.yaml"])
