#Version: 1.0

#Status: Working.

#Help: pawansi@cisco.com

Topology reference: https://www.cisco.com/c/dam/en/us/td/i/300001-400000/350001-360000/354001-355000/354879.eps/_jcr_content/renditions/354879.jpg

```bash
   
Topology:
       ||====================Fusion Router=====================================||
       ||                                                                      ||
       ||    (MultiChassis Linkgroup)                                          ||
       ||                                                                      ||
   |-------|                                                               |-------|
   |       |--------Dual Active Detection Link (DAD-LINK)------------------|       |
   |       |                                                               |       |
   |Switch1|----------Stackwise-Virtual link (STACKWISEVIRTUAL-LINK)-------|Switch2|      [Stackwise-Virtual Switch (9400/9500/9500H/9600/) Gateway (SEED)]
   |       |----------Stackwise-Virtual link (STACKWISEVIRTUAL-LINK)-------|       |
   |-------|\                                                           // |-------|
            \\                                                         //
             \\                                                       //
      (MultiChassis Linkgroup)                                       //
               \\                 --------------------------        //
                \\================|                        |=======//
                                  |  Distribution          |
                                  | StackWise-Virtual      |
                                  |------------------------|

    Each Dual Active Detection must have "DAD-LINK" keyword in link description text
    Each Dual Stackwise-virtual  must have "STACKWISEVIRTUAL-LINK" keyword in link description text
    Link number should switch index appended for each link: 1/0/48  --> for switch1 1/1/0/48
                                                                    --> for switch2 2/1/0/48

   https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9500/software/release/16-11/configuration_guide/ha/b_1611_ha_9500_cg/configuring_cisco_stackwise_virtual.html
```

#Description:
1. Creating a Stackwise Virtual from two 9K switches. Details provided in testbed yaml.
2. The project used Cisco pyats environment, or use it as a container on any linux machine.
3. To install the execution environment, first install the Python3.7 or above on the execution server and then run the setup.sh tool to install the pyats environment. 

#Code Checkout:
Checkout the code with git or download from github directly.
```bash
   git clone git@github.com:DNACENSolutions/Stackwise-Virtual.git
   cd Stackwise-Virtual
```
#to run the setup installer:
```bash
   ./stackwisevirtual.sh -i install

```

Create or Setup your testbed yaml file for the switch pair to be used for creating stackwise-virtual. Refer sample file: testbed/9600_sv_tb.yaml

#Running scripts
```bash
    ./stackwisevirtual.sh -<option>  <testbedlocation>
```
#Launch your svlbuilder script.
```bash
   ./stackwisevirtual.sh -c ./testbed/9600_sv_tb.yaml
```
#to Cleanup svlconfig from svl pair
```bash
  ./stackwisevirtual.sh -d ./testbed/9600_sv_tb.yaml
```

#to update stackwise-virtual links or dual-active detection link configs.
```bash
  ./stackwisevirtual.sh -u ./testbed/9600_sv_tb.yaml
```

#To use this as a library:
```bash
   from svlservices.svlservices import StackWiseVirtual
   svl_handle = StackWiseVirtual(testbed)
```

After Stackwise-virtual stacking is created.

```text
show stackwise-virtual
Stackwise Virtual Configuration:
--------------------------------
Stackwise Virtual : Enabled
Domain Number :   2  

Switch   Stackwise Virtual Link  Ports
------   ----------------------  ------
1     1                    TenGigabitEthernet1/0/33    
                           TenGigabitEthernet1/0/40    
2     1                    TenGigabitEthernet2/0/33    
                           TenGigabitEthernet2/0/40    

Switch# show stackwise-virtual neighbors
Stackwise Virtual Link(SVL) Neighbors Information:
--------------------------------------------------
Switch   SVL   Local Port                         Remote Port
------   ---   ----------                         -----------
1     1  TenGigabitEthernet1/0/33           TenGigabitEthernet2/0/33         
         TenGigabitEthernet1/0/40           TenGigabitEthernet2/0/40         
2     1  TenGigabitEthernet2/0/33           TenGigabitEthernet1/0/33         
         TenGigabitEthernet2/0/40           TenGigabitEthernet1/0/40         

Switch# show stackwise-virtual dual-active-detection
In dual-active recovery mode: No
Recovery Reload: Enabled

Dual-Active-Detection Configuration:
-------------------------------------
Switch   Dad port       Status
------   ------------         ---------
1  TenGigabitEthernet1/0/24   up     
2  TenGigabitEthernet2/0/24   up 
```
