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
1.  Go to the below link and download the docker image.
      https://hub.docker.com/repository/docker/maranjega/docker_images
2.  Find "Installing Docker Engine in CENTOS 7" from the below link for installing docker engine.
      https://wiki.cisco.com/display/EDPEIXOT/Solutions+PyatsDocker+Build+procedure    
3. Once installed the docker engine,run the below command from your linux machine.
    " docker run --rm maranjega/docker_images:solution-eng-stackwise-jun15 pyats run job /pyats/sol_eng_stackwise_virtual/job/svl_update_job.py --testbed-file /pyats/sol_eng_stackwise_virtual/testbed/9500_sv_tb.yaml "
    
STEPS to add new testbed file to existing docker image:

1. From the below command check your docker images detail and current docker instances detail.

[maran@maran ~]$ docker images
REPOSITORY                TAG                            IMAGE ID       CREATED         SIZE
maranjega/docker_images   solution-eng-stackwise-jun15   62a9693176e2   5 days ago      792MB
maranjega/docker_images   solution-eng-stackwise-new     73d1c48e486b   2 weeks ago     732MB
maranjega/docker_images   solution-eng-stackwise         15c1768a735c   4 weeks ago     659MB
maranjega/docker_images   guardian                       c8cd56d728c5   2 months ago    1.61GB
python                    3.8.7-slim                     20b06bd8f030   16 months ago   114MB
[maran@maran ~]$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

2. Create docker instance from the below command by specifying required repo name and tag.

[maran@maran ~]$ docker run -t -d maranjega/docker_images:solution-eng-stackwise-jun15
8696ec31d81cb84f3662f2003fe6a4ef7142cd138d4e609a73e6188fc08b1960

3. Check the docker instance name or container ID from the below command.

[maran@maran ~]$ docker ps
CONTAINER ID   IMAGE                                                  COMMAND                  CREATED         STATUS         PORTS     NAMES
8696ec31d81c   maranjega/docker_images:solution-eng-stackwise-jun15   "/bin/tini -- /pyats…"   5 seconds ago   Up 4 seconds             nifty_turing

4. Get into docker bash prompt from the below command and create new testbed file.

[maran@maran ~]$ docker exec -it nifty_turing sh
# pwd
/pyats
# ls
bin  installation  lib	pip.conf  pyvenv.cfg  sol_eng_stackwise_virtual
# cd sol_eng_stackwise_virtual
# ls
LICENSE  README.md  README.rst	job  requirements.txt  scripts	setup.cfg  setup.py  setup.sh  stackwisevirtual.sh  svlservices  testbed
# cd testbed
# ls
9500_9600_sv_tb.yaml  9500_sv_tb.yaml  9600_sv_tb.yaml
# cp 9600_sv_tb.yaml test_new.yaml
# ls
9500_9600_sv_tb.yaml  9500_sv_tb.yaml  9600_sv_tb.yaml	test_new.yaml
# exit

5. Commit the changes by mentioning the correct container id of the instance created.

[maran@maran ~]$ docker commit 8696ec31d81c maranjega/docker_images:solution-eng-stackwise-jun15
sha256:b252390e2d84a4d68895624bf45e1b64b1f4c66300a9bf790a95a8c05ccbd520

6. STOP the container instance from the below command.

[maran@maran ~]$ 
[maran@maran ~]$ docker stop 8696ec31d81c
8696ec31d81c

7. PUSH the commited changes to the remote repo using the below command.
 
[maran@maran ~]$ docker push maranjega/docker_images:solution-eng-stackwise-jun15
The push refers to repository [docker.io/maranjega/docker_images]
516ad2704643: Pushed 
2494bc902331: Layer already exists 
ccc090f460c2: Layer already exists 
164669a3bfc2: Layer already exists 
bc8ed43b63ca: Layer already exists 
7ab432b99270: Layer already exists 
e21f2b576bf8: Layer already exists 
2ce3ee9fabd8: Layer already exists 
9b3434966ee1: Layer already exists 
8711af342595: Layer already exists 
9eb82f04c782: Layer already exists 
solution-eng-stackwise-jun15: digest: sha256:3fa32fd05921c541f28cf44e4cadf4abb5117dbcdf59d031be5dee081a65b7cb size: 2632

8. To verify the changes create new docker instance and login to bash prompt of docker instance and check the file exist or not.

[maran@maran ~]$ docker run -t -d maranjega/docker_images:solution-eng-stackwise-jun15
f7bad525c4974b096c7cf15c59197832ba83d3a6bc889772be2a9084befd4d32

[maran@maran ~]$ docker ps
CONTAINER ID   IMAGE                                                  COMMAND                  CREATED         STATUS         PORTS     NAMES
f7bad525c497   maranjega/docker_images:solution-eng-stackwise-jun15   "/bin/tini -- /pyats…"   5 seconds ago   Up 4 seconds             festive_turing

[maran@maran ~]$ docker exec -it festive_turing sh
# ls
bin  installation  lib	pip.conf  pyvenv.cfg  sol_eng_stackwise_virtual
# cd sol_eng_stackwise_virtual/testbed	
# ls
9500_9600_sv_tb.yaml  9500_sv_tb.yaml  9600_sv_tb.yaml	test_new.yaml
# exit

[maran@maran api]$ docker stop f7bad525c497
f7bad525c497

9. Use the below command to run the job file with new testbed file.
   "docker run --rm maranjega/docker_images:solution-eng-stackwise-jun15 pyats run job /pyats/sol_eng_stackwise_virtual/job/svl_update_job.py --testbed-file /pyats/sol_eng_stackwise_virtual/testbed/test_new.yaml"
    
