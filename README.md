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

Steps to run job from docker image:

1.  Find "Installing Docker Engine in CENTOS 7/Ubuntoo/RHEL" from the below link for installing docker engine.
      https://docs.docker.com/engine/install/centos/   
3. Once installed the docker engine,run the below command from your linux machine.

   3.1  Go to the below link and download the latest docker image. (Latest Docker image: https://hub.docker.com/r/maranjega/docker_images/tags)
   docker pull maranjega/docker_images:solution-eng-stackwise-aug19-djang

   3.2  Run the docker image:
   docker run -it -d maranjega/docker_images:solution-eng-stackwise-aug19-django

   3.3 run command "docker ps solution-eng-stackwise-aug19-django" and get the dockerid
   ```bash
   docker ps | grep stackwise
   cfe3f1ce3716        maranjega/docker_images:solution-eng-stackwise-aug19-django      "/bin/tini -- /pyats…"   About a minute ago   Up About a minute                       quizzical_chebyshev
   ```
   3.4 Attach to docker 
   docker run -it -e 8000 maranjega/docker_images:solution-eng-stackwise-aug19-django

   3.3  source the python environment
      source bin/activate
      cd sol_eng_stackwise_virtual

   3.4 update the interface ip in settings
      ALLOWED_HOSTS = ['*', "localhost", "127.0.0.1"]
      Add vm interface ip to the list.
   
   3.5 to run UI application start server using
         ```bash
            python website/manage.py runserver <ipaddress>:8000
            sample: python website/manage.py runserver 127.0.0.1:8000
            (pyatsenv) PAWANSI-M-5DCS:Stackwise-Virtual pawansingh$ python website/manage.py runserver 
               Watching for file changes with StatReloader
               Performing system checks...

               System check identified no issues (0 silenced).
               August 24, 2022 - 05:26:35
               Django version 3.2.15, using settings 'website.settings'
               Starting development server at http://127.0.0.1:8000/
               Quit the server with CONTROL-C.
         ```
   3.6 Open a browser and use url: http://127.0.0.1:8000/ to generate testbed file.
   3.7 Once the testbed file is saved.  from the docker run script to configure stackwise virtual.
   ./stackwisevirtual.sh -c ./testbed/generated_testbed_file.yaml

STEPS to add new testbed file to existing docker image and run :

1. Mount the local testbed directory in docker with the below command 
[maran@maran Stackwise-Virtual]$ docker run -d -it --name devtest1 --mount type=bind,source=/home/maran/Stackwise-Virtual/testbed,target=/pyats/sol_eng_stackwise_virtual/testbed maranjega/docker_images:solution-eng-stackwise-jun15
63d007b1b2cf8e65431516fe6647b07afae8647e78b1e4b75b1af42487ec6fbf

2. To run the job from the container bash follow the below steps.
[maran@maran Stackwise-Virtual]$ docker exec -it devtest1 bash
root@812e50740447:/pyats#
root@812e50740447:/pyats# source bin/activate
(pyats) root@812e50740447:/pyats# cd sol_eng_stackwise_virtual
(pyats) root@812e50740447:/pyats/sol_eng_stackwise_virtual# pyats run job /pyats/sol_eng_stackwise_virtual/job/svl_update_job.py --testbed-file /pyats/sol_eng_stackwise_virtual/testbed/test.yaml
