#Stackwise vitual Class. Models two switches as one HA device.
from threading import Thread
from pyats.topology import loader
import logging
import re
import time
from unicon.eal.dialogs import Statement, Dialog
from pyats.topology import Device
import traceback
from unicon.utils import Utils as unicon_utils

#=================================Global Constants=====
SVLVERSION_9500="16.8.1"
SVLVERSION_9400="16.9.1"
SVLVERSION_9600="16.12.1"
MAXRELOADTIMEOUT=400
EXCEPTIONRELOADTIMEWAIT=120
PLATFORMVERSIONREFERENCE=[
    {   "platform": ["C9500-40X","C5900-16X","C5900-12Q","C9500-24Q"],
        "ref_version": SVLVERSION_9500
    },
    {   "platform": ["C9407R","C9400R"],
        "ref_version": SVLVERSION_9400
    },
    {   "platform": ["C9606R"],
        "ref_version": SVLVERSION_9600
    }
]
SKIPCONLIST=[ 'defaults','alt', 'con_credentials']
CONNECTIONKEYS=['a','b','c','d','e','f']
SUPPORTED_PLATFORMS_LIST=[9500, 9400, 9600, "9500", "9400", "9600"] 
#Logger initize
Logger = logging.getLogger(__name__)

#================Device Interactive dialog confirmations for UNICON to provide cli user confirmations
DIALOG_CONFIRM = Dialog([
        Statement(pattern=r'^.*continue\?\[y/n\]\?\s*\[yes\]\:.*$',
                  action="sendline(yes)",
                  loop_continue=True,
                  continue_timer=False)])
DIALOG_CONFIRM1 =  Dialog([
        Statement(pattern=r"^.*continue\?\[y/n\]\?.*$",
                  action="sendline(y)",
                  loop_continue=True,
                  continue_timer=False),
        Statement(pattern=r"^.*\[confirm\(\(y/n\)?\].*$",
                  action="sendline(y)",
                  loop_continue=True,
                  continue_timer=False)])
#===============Internal Functions======================
#==========================================================
# clear console line for dev 
#==========================================================
#==========================================================
# connect with clear line if needed 
#==========================================================
def uni_connect(dev, retry=2, wait_sec=1, config_timeout=120):
    '''
    Function: uni_connect 
    Description: Function used to connect to the device through cosole line with device details provided in testbed file.
                    If connection to console fail, it tries to clear the console line and reconnect on more time.
    Inputs: Device object
            retry count, Default 2
            Wait_sec between retries, Default 1
            Max config_timeout, Default 120
    '''
    result = False
    import copy

    for run in range(retry): 
        try:
            print(dev.connections.a.protocol)
            print(dev.connections.a.ip)
            dev.connect(prompt_recovery=True)
            dev.configure.timeout = config_timeout
            result = True
            break
        except ConnectionError as e:
            logger.warning("Failed login through primary , trying clearing console and retry")
            try:
                if dev.connections.a.protocol=="telnet":
                    uni_clear_console(dev)
                dev.disconnect()
                time.sleep(wait_sec)
            except:
                logger.error(traceback.format_exc())
                logger.info("clearing line for try:{}/{}".format(run+1, retry))
                if dev.connections.default.protocol=="telnet":
                    uni_clear_console(dev)
                dev.disconnect()
                time.sleep(wait_sec)
        if result:
            break
    return result
def uni_clear_console(dev):
    '''
        Function: uni_clear_console
        Description: Function to clear console line for a device.
        If console user/Pass is configured in the terminal server, then con_credebtials need to be provided in TB
        Under device connections as below.

        con_credentials:
                terminal_server_username: <tsusername>
                terminal_server_password: <tspassword>
                terminal_server_enable_password: <tsenablepass>
    '''
    uu = unicon_utils()
    starts = []
    if dev.start:
        starts = [dev.start]
    elif dev.subconnections:
        for p in dev.subconnections:
            starts.append(p.start)

    for start in starts:
        for console in start:
            if len(console.split()) == 3:
                if 'telnet' in console:
                    term_serv = console.split()[1]
                    port = console.split()[2]
                    if int(port) > 6000:
                        port = int(port) - 6000
                    if int(port) > 3000:
                        port = int(port) - 3000
                    elif int(port) > 2000:
                        port = int(port) - 2000
                    if 'con_credentials' in dev.connections:
                        username = dev.connections.con_credentials.terminal_server_username
                        password = dev.connections.con_credentials.terminal_server_password
                        enable_password = dev.connections.con_credentials.terminal_server_enable_password
                        uu.clear_line(term_serv, port, username, password, enable_password)
                    else:
                        uu.clear_line(term_serv, port)
                else:
                    logger.error("Dev: {} Unable to clear console: {}".
                        format(dev.name, console))
            else:
                logger.error("Dev: {} Unable to clear console: {}".
                    format(dev.name, console))

def wait_for_reload_to_complete(timeout):
    timePassed=0
    while timePassed < timeout:
        time.sleep(10)
        timePassed += 10
        Logger.info("Device reload is in progress, waiting for device to be ready to connect.")
    Logger.info("Device reload wait completed, connecting to device now.")
    return True

#=========================Class/Functions===============
#Multithread run
class MultiUserThreadWithReturn(Thread):
    '''
        Multithread clas to run functions in parallel.
    '''
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None, daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)
        self._Thread__target = target
        self._Thread__args = args
        self._Thread__kwargs = kwargs
        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args,
                                                **self._Thread__kwargs)
    def join(self):
        Thread.join(self)
        return self._return

#Class for SVL main object
class StackWiseVirtual(object):
    '''
        This is the main clas for modeling a stackwise virtual and perform config/update/delete operation
    '''
    def __init__(self, testbed):
        self.testbed=testbed
        self.device_pair_list=[]

    def get_device_pairs(self, svlPair=None):
        '''
            USAGES: This function 
                    1. From the yaml input file, identify the stackpair member. 
                    2. Create a device object for stackpair as single HA device.
                    3. Combines the console connection to single pair from both member stack members.
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        for pair in self.testbed.custom['switchstackinggroups']:
            if not svlPair:
                if pair["numberofswitches"] != len(pair["switchs"]): 
                    Logger.error(
                        "Testbed File Validation Error: The number of devices {}, an count devices provided {} does not match".format(
                                    pair["numberofswitches"],pair["switchs"]))
                    raise
                dev_stack={}
                count=1
                for switch in pair["switchs"]:
                    dev_stack["switch{}".format(count)] = switch
                    count=count+1
                    dev_stack['pairinfo'] = pair
                if self.testbed.devices[dev_stack["switch1"]].custom.switchnumber == 1:
                    switch1 = "switch1"
                    switch2 = "switch2"
                else:
                    switch1 = "switch2"
                    switch2 = "switch1"
                dev_stack['stackwiseVirtualDev'] =  Device(name=self.testbed.devices[dev_stack[switch1]].name+"svl",
                            type=self.testbed.devices[dev_stack[switch1]].type,
                            os=self.testbed.devices[dev_stack[switch1]].os,
                            testbed=self.testbed.devices[dev_stack[switch1]].testbed,
                            passwords=self.testbed.devices[dev_stack[switch1]].passwords,
                            credentials=self.testbed.devices[dev_stack[switch1]].credentials,
                            tacacs=self.testbed.devices[dev_stack[switch1]].tacacs,
                            custom=self.testbed.devices[dev_stack[switch1]].custom,
                            connections=self.testbed.devices[dev_stack[switch1]].connections)
                for key in list(self.testbed.devices[dev_stack[switch2]].connections.keys()):
                    if key in SKIPCONLIST:
                        continue
                    else:
                        for k in CONNECTIONKEYS:
                            if k in list(self.testbed.devices[dev_stack[switch1]].connections.keys()):
                                continue
                            else:
                                print(self.testbed.devices[dev_stack[switch2]].connections[key])
                                if self.testbed.devices[dev_stack[switch2]].connections[key]["protocol"] == "ssh":
                                    continue
                                else:
                                    self.testbed.devices[dev_stack[switch1]].connections[key] = self.testbed.devices[dev_stack[switch2]].connections[key]
                                    break

                Logger.info(dev_stack['stackwiseVirtualDev'].connections)
                dev_stack["status"] = False
                self.device_pair_list.append(dev_stack)
            else:
                if svlPair == pair:
                    if pair["numberofswitches"] != len(pair["switchs"]): 
                        Logger.error(
                            "Testbed File Validation Error: The number of devices {}, an count devices provided {} does not match".format(
                                        pair["numberofswitches"],pair["switchs"]))
                        raise
                    dev_stack={}
                    count=1
                    for switch in pair["switchs"]:
                        dev_stack["switch{}".format(count)] = switch
                        count=count+1
                        dev_stack['pairinfo'] = pair
                    if self.testbed.devices[dev_stack["switch1"]].custom.switchnumber == 1:
                        switch1 = "switch1"
                        switch2 = "switch2"
                    else:
                        switch1 = "switch2"
                        switch2 = "switch1"
                    dev_stack['stackwiseVirtualDev'] =  Device(name=self.testbed.devices[dev_stack["switch1"]].name+"svl",
                                type=self.testbed.devices[dev_stack[switch1]].type,
                                os=self.testbed.devices[dev_stack[switch1]].os,
                                testbed=self.testbed.devices[dev_stack[switch1]].testbed,
                                passwords=self.testbed.devices[dev_stack[switch1]].passwords,
                                credentials=self.testbed.devices[dev_stack[switch1]].credentials,
                                tacacs=self.testbed.devices[dev_stack[switch1]].tacacs,
                                custom=self.testbed.devices[dev_stack[switch1]].custom,
                                connections=self.testbed.devices[dev_stack[switch1]].connections)
                    for key in list(self.testbed.devices[dev_stack[switch2]].connections.keys()):
                        if key in SKIPCONLIST:
                            continue
                        else:
                            for k in CONNECTIONKEYS:
                                if k in list(self.testbed.devices[dev_stack[switch1]].connections.keys()):
                                    continue
                                else:
                                    print(self.testbed.devices[dev_stack[switch2]].connections[key])
                                    if self.testbed.devices[dev_stack[switch2]].connections[key]["protocol"] == "ssh":
                                        continue
                                    else:
                                        dev_stack['stackwiseVirtualDev'].connections[k] = self.testbed.devices[dev_stack[switch2]].connections[key]
                                        break

                    Logger.info(dev_stack['stackwiseVirtualDev'].connections)
                    dev_stack["status"] = False
                    self.device_pair_list.append(dev_stack)
                    break

    def get_device_version(self, dev):
        '''
            USAGES: This function 
                    1. Subroutine gets the device software version and Platform model number
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        output=self.testbed.devices[dev].execute("show version")
        version = re.findall("Cisco IOS XE Software, Version\s+(\S+)",str(output))[0]
        model_number = re.findall("Model Number\s+:\s+(\S+)",str(output))[0]
        return dict(version=version,model=model_number)

    def check_links(self, stackpair):
        '''
            USAGES: This function 
                    1. Performs pre-check if the links defined has a remote endpoint for all links types.
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        links_count=0
        for links in self.testbed.devices[stackpair["switch1"]]:
            if self.testbed.devices[stackpair["switch2"]] in links.remote_devices:
                links_count = links_count + 1
        Logger.info("Number of links found between the switches:{}".format(links_count))
        if links_count:
            return True
        else:
            Logger.info("No Links present between the devices, not good for forming the SVL")
            return False    

    def check_min_version_req(self, stackpair):
        '''
            USAGES: This function 
                    1. Performs pre-check if the stack members has minimum required Software version
                    2. If the platform types of the stackmember are matching.
                    3. if the software version on both stackmembers are same.
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        #Check for switch 1.
        if not self.connect_to_stackpair(stackpair):
            Logger.error("Could not connect to devices, Can not proceed.")
            return False
        if stackpair["status"]:
            Logger.warning("The switch is already a stackwise Virtual. Remove the existing stackwise virtual configs to run this script.")
            #return False
        else:
            switches=[stackpair["switch1"], stackpair["switch2"]]
            dev_details=[]
            for dev in switches:
                device_details = self.get_device_version(dev)
                dev_details.append(device_details)
                found=False
                for item in PLATFORMVERSIONREFERENCE:
                    if device_details['model'] in item["platform"]:
                        found = True
                        if device_details['version'] < item["ref_version"]:
                            Logger.error("The Device Version is below minimum supported version for Stackwise Virtual,"+
                                         " First upgrade the device to minimum supported version:{}".forma(item["ref_version"]))
                            return False
                        else:
                            Logger.info("Device Version:{} is higher then minimum required version:{}".format(
                                    device_details['version'] ,item["ref_version"]))
                if not found:
                    Logger.warning("The Platform not found in reference list, this may not support Stackwise Virtual")
                    return False

            #check for platform and version is same for bothe switches
            dd=dev_details[0]
            for devdetail in dev_details:
                if dd != devdetail:
                    Logger.error("The device version or Platform does not match for the two stack members")
                    Logger.error("\t Switch1 Details: {}\n Switch2 Details: {}".format(dd,devdetail))
                    return False
        return True

    def check_valid_link_types(self, stackpair):
        pass

    def connect_to_stackpair(self,stackpair, retry=2):
        '''
            USAGES: This function 
                    1. Connect the console connections to Stack after stack is formed
                    2. If Stack is not yet formed, it will login to indivisual StackMember
                    3. It will mark the stackpair["status"] to True or False based on if the stack is formed or not. 
                       If stackpair["status"] is set to true, the console connection is connected to Stach chassis in HA mode and not
                       to indivisual members.
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        result=True
        if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST: 
            try:
                if stackpair['stackwiseVirtualDev'].connected or (self.testbed.devices[stackpair["switch1"]].connected and self.testbed.devices[stackpair["switch2"]].connected):
                    return True
                else:
                    self.disconnect_from_stackpair(stackpair)
                if not self.testbed.devices[stackpair["switch1"]].connected:
                    dev_detail = uni_connect(self.testbed.devices[stackpair["switch1"]])
                output = self.testbed.devices[stackpair["switch1"]].execute("show stackwise-virtual neighbors")
                output1 = self.testbed.devices[stackpair["switch1"]].execute("show stackwise-virtual")
                stackstatus = re.findall('Stackwise Virtual : Enabled',output1)
                stackpair["status"]=False
                if stackstatus:
                    output2 = output.split("\n")
                    for line in output2:
                        print(line)
                        stackstatus1 = re.findall('\d[\s\t]+\d[\s\t]+[\w/]+[\s\t]+[\w/]+',line)
                        if stackstatus1:
                            stackpair["status"]=True
                            break
                    print(stackpair["status"])
                    if stackpair["status"]:
                        print("Setting stackwise virtual to True")
                        self.testbed.devices[stackpair["switch1"]].disconnect()
                        self.testbed.devices[stackpair["switch2"]].disconnect()
                        uni_connect(stackpair['stackwiseVirtualDev'])
                        return True
                    else:
                        Logger.info("The Switch does not have in Stackwise Virtual link. Treat it as 2 single nodes")
                else:
                    Logger.info("The Switch is does not in Stackwise Virtual enabled. Treat it as 2 single nodes")
                if not stackpair["status"]:
                    if not self.testbed.devices[stackpair["switch2"]].connected:
                        dev_detail = self.testbed.devices[stackpair["switch2"]].connect()
                    stackpair["status"] = False
                    return True
            except:
                try:
                    Logger.error(traceback.format_exc())
                    uni_connect(stackpair['stackwiseVirtualDev'])
                    #.connect()
                    stackpair["status"] = True
                    return True
                except:
                    Logger.error("Could not connect to the device")
                    Logger.error(traceback.format_exc())
                    result=False
        else:
            try:
                if not self.testbed.devices[stackpair["switch1"]].connected:
                    dev_detail = uni_connect(self.testbed.devices[stackpair["switch1"]])
                    #.connect()
                if not self.testbed.devices[stackpair["switch2"]].connected:
                    dev_detail = uni_connect(self.testbed.devices[stackpair["switch2"]])
                    #.connect()
            except:
                Logger.error("Could not connect to the device")
                Logger.error(traceback.format_exc())
                result=False
        if not result and retry > 0:
            time.sleep(120)
            self.disconnect_from_stackpair(stackpair)
            self.testbed.devices[stackpair["switch1"]].disconnect()
            self.testbed.devices[stackpair["switch2"]].disconnect()
            time.sleep(10)
            stackpair['stackwiseVirtualDev'].connected = False
            return self.connect_to_stackpair(stackpair, retry=retry-1)
        return result

    def connect_to_stackwiseVirtual(self,stackpair):
        '''
            USAGES: This function 
                    1. Connect the console connections to Stack after stack is formed
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        if not stackpair["stackwiseVirtualDev"].connected:
            stackpair["stackwiseVirtualDev"].connect()
        return True

    def disconnect_from_stackpair(self,stackpair):
        '''
            USAGES: This function 
                    1. Disconnect the console connections to Stack or its Members
            INPUT:  Stackpair
            Returns: True if success, False if Fails
        '''
        if stackpair['stackwiseVirtualDev'].connected:
            stackpair['stackwiseVirtualDev'].disconnect()
        if self.testbed.devices[stackpair["switch1"]].connected:
            self.testbed.devices[stackpair["switch1"]].disconnect()
        if self.testbed.devices[stackpair["switch2"]].connected:
            self.testbed.devices[stackpair["switch2"]].disconnect()
        return True

    def save_config_and_reload(self, stackpair, reloadAsync=False,timeout=MAXRELOADTIMEOUT):
        '''
            USAGES: This function 
                    1. Saves the config on stack member if the stack is not formed, or on the stack if stack is already formed.
                    2. Reload the switch.
            INPUT:  Stackpair, reloadAsync =(True or False) if the stack member to be reloaded in parallel or sequential
            Returns: True if success, False if Fails
        '''
        #Reload bothe switches
        if reloadAsync:
            if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]: 
                reload_switch_asynchronously(stackpair['stackwiseVirtualDev'])
            else:
                reload_switch_asynchronously(self.testbed.devices[stackpair["switch1"]])
                reload_switch_asynchronously(self.testbed.devices[stackpair["switch2"]])
            wait_for_reload_to_complete(timeout)
        else:
            if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
                stackpair['stackwiseVirtualDev'].execute("write memory")
            else:
                self.testbed.devices[stackpair["switch1"]].execute("write memory")
                self.testbed.devices[stackpair["switch2"]].execute("write memory")
            if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
                stackpair['stackwiseVirtualDev'].reload(timeout=timeout)
                stackpair['stackwiseVirtualDev'].disconnect()
            else:
                try:
                    self.testbed.devices[stackpair["switch1"]].reload(timeout=timeout)
                except:
                    time.sleep(EXCEPTIONRELOADTIMEWAIT)
                    Logger.error(traceback.format_exc())
                    self.testbed.devices[stackpair["switch1"]].disconnect()
                try:
                    self.testbed.devices[stackpair["switch2"]].reload(timeout=timeout)
                except:
                    time.sleep(EXCEPTIONRELOADTIMEWAIT)
                    Logger.error(traceback.format_exc())
                    self.testbed.devices[stackpair["switch2"]].disconnect()
        self.disconnect_from_stackpair(stackpair)
        return True

    def configure_svl_step1(self, stackpair):
        '''
            USAGES:This function Configures:
                   1. Switch number
                   2. Switch Priority
                   3. Stackwise Virtual Domain
            INPUT: Stackpair
            Returns: True if success, False if Fails
        '''
        if "domainNumber" in stackpair['pairinfo'].keys():
            domainNumber = stackpair['pairinfo']["domainNumber"]
        else:
            Logger.warning("DomainNumber not provided in the testbed yaml file. Assuming dimain number: 2")
            domainNumber = 2
        config="""stackwise-virtual
                    domain {}
                """.format(domainNumber)
        if not self.connect_to_stackpair(stackpair):
            Logger.error("Could not connect to devices, Can not proceed.")
            return False
        if stackpair['pairinfo']["platformType"] in [9500, "9500"]: 
             #On Switch1
            self.testbed.devices[stackpair["switch1"]].execute("switch 1 renumber  {}".format(
                self.testbed.devices[stackpair["switch1"]].custom["switchnumber"]),reply=DIALOG_CONFIRM)
            self.testbed.devices[stackpair["switch1"]].execute("switch {} priority {}".format(
                    self.testbed.devices[stackpair["switch1"]].custom["switchnumber"],
                    self.testbed.devices[stackpair["switch1"]].custom["switchpriority"]),reply=DIALOG_CONFIRM)
            #On Switch2
            self.testbed.devices[stackpair["switch2"]].execute("switch 2 renumber  {}".format(
                self.testbed.devices[stackpair["switch2"]].custom["switchnumber"]),reply=DIALOG_CONFIRM)
            self.testbed.devices[stackpair["switch2"]].execute("switch {} priority {}".format(
                    self.testbed.devices[stackpair["switch2"]].custom["switchnumber"],
                    self.testbed.devices[stackpair["switch2"]].custom["switchpriority"]),reply=DIALOG_CONFIRM)
        elif stackpair['pairinfo']["platformType"] in [9400, 9600, "9400", "9600"]:
            try: 
                self.testbed.devices[stackpair["switch1"]].execute("switch renumber  {}".format(
                    self.testbed.devices[stackpair["switch1"]].custom["switchnumber"]),reply=DIALOG_CONFIRM)
                self.testbed.devices[stackpair["switch1"]].execute("switch priority {}".format(
                    self.testbed.devices[stackpair["switch1"]].custom["switchpriority"]),reply=DIALOG_CONFIRM)
            except:
                 #On Switch1
                self.testbed.devices[stackpair["switch1"]].execute("switch 1 renumber  {}".format(
                    self.testbed.devices[stackpair["switch1"]].custom["switchnumber"]),reply=DIALOG_CONFIRM)
                self.testbed.devices[stackpair["switch1"]].execute("switch {} priority {}".format(
                        self.testbed.devices[stackpair["switch1"]].custom["switchnumber"],
                        self.testbed.devices[stackpair["switch1"]].custom["switchpriority"]),reply=DIALOG_CONFIRM)
            try:
                #On Switch2
                self.testbed.devices[stackpair["switch2"]].execute("switch renumber {}".format(
                    self.testbed.devices[stackpair["switch2"]].custom["switchnumber"]),reply=DIALOG_CONFIRM)
                self.testbed.devices[stackpair["switch2"]].execute("switch priority {}".format(
                    self.testbed.devices[stackpair["switch2"]].custom["switchpriority"]),reply=DIALOG_CONFIRM)
            except:
                self.testbed.devices[stackpair["switch2"]].execute("switch 2 renumber  {}".format(
                    self.testbed.devices[stackpair["switch2"]].custom["switchnumber"]),reply=DIALOG_CONFIRM)
                self.testbed.devices[stackpair["switch2"]].execute("switch {} priority {}".format(
                        self.testbed.devices[stackpair["switch2"]].custom["switchnumber"],
                        self.testbed.devices[stackpair["switch2"]].custom["switchpriority"]),reply=DIALOG_CONFIRM)
        else:
            Logger.error("Unsupported Platform Type provided in the yaml")
            return False
        self.testbed.devices[stackpair["switch1"]].configure(config,reply=DIALOG_CONFIRM1)
        self.testbed.devices[stackpair["switch1"]].execute("show stackwise-virtual")
        #On Switch2
        self.testbed.devices[stackpair["switch2"]].configure(config,reply=DIALOG_CONFIRM1)
        self.testbed.devices[stackpair["switch2"]].execute("show stackwise-virtual")
        return True

    def configure_svl_step2_svllinkconfig(self, stackpair):
        '''
            USAGES:This function Configures the stackwise-virtual link config on the stack.
            INPUT: Stackpair
            Returns: True if success, False if Fails
        '''
        if not self.connect_to_stackpair(stackpair):
            Logger.error("Could not connect to devices, Can not proceed.")
            return False
        #On Switch1
        config1=""
        config2=""
        for link in self.testbed.devices[stackpair["switch1"]]:
            if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                config1 += """
                            interface {}
                                stackwise-virtual link 1""".format(link.name)

        for link in self.testbed.devices[stackpair["switch2"]]:
            if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                config2 += """
                            interface {}
                                stackwise-virtual link 1""".format(link.name)
        Logger.info(config1)
        Logger.info(config2)

        if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
            stackpair['stackwiseVirtualDev'].configure(config1)
            stackpair['stackwiseVirtualDev'].configure(config2)
            stackpair['stackwiseVirtualDev'].execute("show stackwise-virtual")
            stackpair['stackwiseVirtualDev'].execute("write memory")
        else:
            self.testbed.devices[stackpair["switch1"]].configure(config1)
            self.testbed.devices[stackpair["switch2"]].configure(config2)

            self.testbed.devices[stackpair["switch1"]].execute("show stackwise-virtual")
            self.testbed.devices[stackpair["switch2"]].execute("show stackwise-virtual")

            self.testbed.devices[stackpair["switch1"]].execute("write memory")
            self.testbed.devices[stackpair["switch2"]].execute("write memory")
        return True

    def configure_svl_step3_dad_linkconfig(self, stackpair):
        '''
            USAGES:This function Configures the DAD link config on the stack.
            INPUT: Stackpair
            Returns: True if success, False if Fails
        '''
        if not self.connect_to_stackpair(stackpair):
            Logger.error("Could not connect to devices, Can not proceed.")
            return False
        #On Switch1
        config1=""
        config2=""
        for link in self.testbed.devices[stackpair["switch1"]]:
            if link.link.name.upper().find('DAD-LINK') != -1:
                config1 += """interface {}
                                stackwise-virtual dual-active-detection
                                """.format(link.name)

        for link in self.testbed.devices[stackpair["switch2"]]:
            if link.link.name.upper().find('DAD-LINK') != -1:
                config2 += """interface {}
                                stackwise-virtual dual-active-detection
                                """.format(link.name)
        if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
            stackpair['stackwiseVirtualDev'].configure(config1)
            stackpair['stackwiseVirtualDev'].configure(config2)
            stackpair['stackwiseVirtualDev'].execute("show stackwise-virtual")
            stackpair['stackwiseVirtualDev'].execute("write memory")
        else:
            self.testbed.devices[stackpair["switch1"]].configure(config1)
            self.testbed.devices[stackpair["switch2"]].configure(config2)

            self.testbed.devices[stackpair["switch1"]].execute("show stackwise-virtual")
            self.testbed.devices[stackpair["switch2"]].execute("show stackwise-virtual")

            self.testbed.devices[stackpair["switch1"]].execute("write memory")
            self.testbed.devices[stackpair["switch2"]].execute("write memory")
        return True

    def disable_svl_config(self, stackpair):
        '''
            USAGES:This function removes the SVL configs from stackwise virtual switches. 
                    1. Step1: Remove Dual Active detection configs.
                    2. Step2: Remove stackwise Virtual link configs.
                    3. Step3: Remove stackwise Virtual  config.
            INPUT: Stackpair
            Returns: True if success, False if Fails
        '''
        if not self.connect_to_stackpair(stackpair):
            Logger.error("Could not connect to devices, Can not proceed.")
            return False
        #On Switch1
        config1=""
        config2=""
        for link in self.testbed.devices[stackpair["switch1"]]:
            if link.link.name.lower().find('DAD-LINK') != -1:
                config1 += """interface {}
                                no stackwise-virtual dual-active-detection""".format(link.name)

        for link in self.testbed.devices[stackpair["switch2"]]:
            if link.link.name.lower().find('DAD-LINK') != -1:
                config1 += """interface {}
                                no stackwise-virtual dual-active-detection""".format(link.name)

        for link in self.testbed.devices[stackpair["switch1"]]:
            if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                config1 += """
                            interface {}
                                no stackwise-virtual link 1""".format(link.name)

        for link in self.testbed.devices[stackpair["switch2"]]:
            if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                config2 += """
                            interface {}
                                no stackwise-virtual link 1""".format(link.name)
        if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
            self.default_svl_dad_interfaces(stackpair['stackwiseVirtualDev'])
            stackpair['stackwiseVirtualDev'].configure("no stackwise-virtual")
        else:
            self.default_svl_dad_interfaces(self.testbed.devices[stackpair["switch1"]])
            self.default_svl_dad_interfaces(self.testbed.devices[stackpair["switch2"]])
            self.testbed.devices[stackpair["switch1"]].configure("no stackwise-virtual")
            self.testbed.devices[stackpair["switch2"]].configure("no stackwise-virtual")
            self.testbed.devices[stackpair["switch1"]].execute("write memory")
            self.testbed.devices[stackpair["switch2"]].execute("write memory")
        return True

    def validate_stackwise_SVL_and_DAD_links_status(self,stackpair,retry=10):
        '''
            USAGES: Validate the link status in the Stackwise Virtual and Dual Active detection
            INPUT: Stackpair
            Returns: True if success, False if Fails
        '''
        result=True
        if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
            output = stackpair['stackwiseVirtualDev'].execute("show stackwise-virtual")
            output1 = stackpair['stackwiseVirtualDev'].execute("show stackwise-virtual neighbors")
            output2 = stackpair['stackwiseVirtualDev'].execute("show stackwise-virtual dual-active-detection")
            if re.findall("Stackwise Virtual : Enabled", output):
                Logger.info("Stackwise Virtual Enabled")
            else:
                Logger.error("Stackwise Virtual not Enabled")
                result=False
            for link in self.testbed.devices[stackpair["switch1"]]:
                if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                    a=re.findall(link.name, output1)
                    if len(a) >= 2:
                        Logger.info("Link {} from switch {} is available in the links for stackwise Virtual!".format(link.name,stackpair["switch1"]))
                    else:
                        Logger.error("Link {} from switch {} is not available in the links for stackwise Virtual".format(link.name,stackpair["switch1"]))
                        result=False
            for link in self.testbed.devices[stackpair["switch2"]]:
                if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                    a=re.findall(link.name, output1)
                    if len(a) >= 2:
                        Logger.info("Link {} from switch {} is available in the links for stackwise Virtual!".format(link.name,stackpair["switch2"]))
                    else:
                        Logger.error("Link {} from switch {} is not available in the links for stackwise Virtual".format(link.name,stackpair["switch2"]))
                        result=False
            for link in self.testbed.devices[stackpair["switch1"]]:
                if link.link.name.upper().find('DAD-LINK') != -1:
                    a=re.findall("\d+\s+{}\s+up".format(link.name), output2)
                    if len(a) >= 1:
                        Logger.info("Link {} from switch {} is available in DAD links!".format(link.name,stackpair["switch1"]))
                    else:
                        Logger.error("Link {} from switch {} is not available in DAD links!".format(link.name,stackpair["switch1"]))
                        result=False
            for link in self.testbed.devices[stackpair["switch2"]]:
                if link.link.name.upper().find('DAD-LINK') != -1:
                    a=re.findall("\d+\s+{}\s+up".format(link.name), output2)
                    if len(a) >= 1:
                        Logger.info("Link {} from switch {} is available in DAD links!!".format(link.name,stackpair["switch2"]))
                    else:
                        Logger.error("Link {} from switch {} is not available in DAD links!".format(link.name,stackpair["switch2"]))
                        result=False
        else:
            switches=[stackpair["switch1"], stackpair["switch2"]]
            dev_details=[]
            for dev in switches:
                output = self.testbed.devices[dev].execute("show stackwise-virtual")
                output1 = self.testbed.devices[dev].execute("show stackwise-virtual neighbors")
                output2 = self.testbed.devices[dev].execute("show stackwise-virtual dual-active-detection")
                if re.findall("Stackwise Virtual : Enabled", output):
                    Logger.info("Stackwise Virtual Enabled")
                else:
                    Logger.error("Stackwise Virtual not Enabled")
                    result=False
                for link in self.testbed.devices[stackpair["switch1"]]:
                    if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                        a=re.findall(link.name, output1)
                        if len(a) >= 2:
                            Logger.info("Link {} from switch {} is available in the links for stackwise Virtual!".format(link.name,stackpair["switch1"]))
                        else:
                            Logger.error("Link {} from switch {} is not available in the links for stackwise Virtual".format(link.name,stackpair["switch1"]))
                            result=False
                for link in self.testbed.devices[stackpair["switch2"]]:
                    if link.link.name.upper().find('STACKWISEVIRTUAL-LINK') != -1:
                        a=re.findall(link.name, output1)
                        if len(a) >= 2:
                            Logger.info("Link {} from switch {} is available in the links for stackwise Virtual!".format(link.name,stackpair["switch2"]))
                        else:
                            Logger.error("Link {} from switch {} is not available in the links for stackwise Virtual".format(link.name,stackpair["switch2"]))
                            result=False
                for link in self.testbed.devices[stackpair["switch1"]]:
                    if link.link.name.upper().find('DAD-LINK') != -1:
                        a=re.findall("\d+\s+{}\s+up".format(link.name), output2)
                        if len(a) >= 1:
                            Logger.info("Link {} from switch {} is available in DAD links!".format(link.name,stackpair["switch1"]))
                        else:
                            Logger.error("Link {} from switch {} is not available in DAD links!".format(link.name,stackpair["switch1"]))
                            result=False
                for link in self.testbed.devices[stackpair["switch2"]]:
                    if link.link.name.upper().find('DAD-LINK') != -1:
                        a=re.findall("\d+\s+{}\s+up".format(link.name), output2)
                        if len(a) >= 1:
                            Logger.info("Link {} from switch {} is available in DAD links!!".format(link.name,stackpair["switch2"]))
                        else:
                            Logger.error("Link {} from switch {} is not available in DAD links!".format(link.name,stackpair["switch2"]))
                            result=False
        if not result and retry > 0:
            time.sleep(30)
            return self.validate_stackwise_SVL_and_DAD_links_status(stackpair,retry=retry-1)
        return result

    def check_stackwise_virtual_confgured(self,stackpair):
        '''
            USAGES: Validate if the device has stackwise-virtual config present on the stack devices or indivisul switches
            INPUT: Stackpair
            Returns: True if success, False if Fails
        '''
        result=True
        if stackpair['pairinfo']["platformType"] in SUPPORTED_PLATFORMS_LIST and stackpair["status"]:
            output1 = stackpair['stackwiseVirtualDev'].execute("show run | sec stackwise-virtual")
            if re.findall("stackwise-virtual", output1):
                Logger.info("Stackwise Virtual configs are present")
            else:
                Logger.error("Stackwise Virtual configs are not present on the switch: {}".format(stackpair))
                result=False
        else:
            switches=[stackpair["switch1"], stackpair["switch2"]]
            dev_details=[]
            for dev in switches:
                output1 = self.testbed.devices[dev].execute("show run | sec stackwise-virtual")
                if re.findall("stackwise-virtual", output1):
                    Logger.info("Stackwise Virtual configs are present")
                else:
                    Logger.error("Stackwise Virtual configs are not present on the switch: {}".format(dev))
                    result=False
        return result

    def configure_svl(self, stackpair):
        '''
            USAGES: Configure Stackwise SVL, All Steps in 1 API/Function good for multiple SVL config in parallel run.
            INPUT: Stackpair
            Output: Fully configured Stackwise-Virtual, 
            Returns: True if success, False if Fails
        '''
        if stackpair['switch1'] == stackpair['switch2']:
            Logger.error("The Device Pair has same name, invalid combination")
            return False

        if not self.check_links(stackpair):
            Logger.error("The devices provided to be paired into SVL does not have any links connected to eachothers")
            return False

        if not self.check_min_version_req(stackpair):
            Logger.info("Minimum Version check failed ")
            return False

        if not self.configure_svl_step1(stackpair):
            Logger.info("Step1 Config failed, Revover Mannuly.")
            return False
        self.save_config_and_reload(stackpair)

        if not self.configure_svl_step2_svllinkconfig(stackpair):
            Logger.info("Step2 Config failed, Revover Mannuly.")
            return False
        self.save_config_and_reload(stackpair)

        if not self.configure_svl_step3_dad_linkconfig(stackpair):
            Logger.info("Step3 Config failed, Revover Mannuly.")
            return False
        self.save_config_and_reload(stackpair)

        if not self.validate_stackwise_SVL_and_DAD_links_status(stackpair):
            Logger.info("Step4 Config failed, Revover Mannuly.")
            return False
        return True

    def default_svl_dad_interfaces(self, oRtr):
        '''
            USAGES: This Function removes the existing stackwise-virtual link and Dual-active-detection links configs.
            INPUT: It needs the Stackwise-Virtual switch as Device object on which links configs to be removed.
            OUTPUT: The Stackwise-Virtual and Dual Active Detection link configs will be reset on interfaces.
            Returns: True if success, False if Fails
        '''
        pattern1='interface (\S+)[\n\r][^\/]+\s+stackwise-virtual link 1'
        pattern2='interface (\S+)[\n\r][^\/]+\s+stackwise-virtual dual-active-detection'
        cmd = "show running-config  | sec interface "
        output = oRtr.execute(cmd, prompt_recovery=True)
        svllinks = re.findall(pattern1,output)
        dadlinks = re.findall(pattern2,output)
        Logger.info(svllinks)
        for cmd in svllinks:
            Logger.info("\nDefaulting the SVL Interface {}".format(cmd))
            oRtr.configure("interface {0} \n no stackwise-virtual link 1".format(cmd))
        Logger.info(dadlinks)
        for cmd in dadlinks:
            Logger.info("\nDefaulting the SVL Interface {}".format(cmd))
            oRtr.configure("interface {0} \n no stackwise-virtual dual-active-detection".format(cmd))
        return True

#==========================================================
#   sub name: reload device asynchronously so both switches reload in parallel
#   Return: pass/fail (1/0)
#==========================================================
def reload_switch_asynchronously(oRtr):
    '''
        USAGES: SAVE config on a switch or stack and reloads but does not wait for it to comeback up.
                Use other wait or retry method to reconnect after device is up.
        INPUT: switch/Stack Device object
        OUTPUT: Device is reloaded
        Returns: True if success, False if Fails
    '''
    try:
        dialog = Dialog([
            Statement(pattern=r"\[yes/no\]:",
                        action= "sendline(yes)",
                        loop_continue=True,
                        continue_timer=False)
            ])
        oRtr.execute("write memory",reply=dialog)
        output = oRtr.transmit("reload\r")
        oRtr.receive("Proceed with reload? [confirm]",timeout=5)
        output = oRtr.transmit("\r")
        oRtr.disconnect()
        Logger.info("Reloaded and disconnected, Wait for reload to complete")
        return True
    except:
        Logger.error(traceback.format_exc())
        Logger.error("Error in reloading the device asynchronously.")
        return False
