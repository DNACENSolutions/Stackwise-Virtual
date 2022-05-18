#!/bin/bash
############################################################
# Help                                                     #
############################################################
Help()
{
   # Display Help
   echo
   echo "    Stackwise-Virtual tools is to create/update/delete stackwise-virtual from two independent switches"
   echo "    This tool needs python3 on the host machine, install python3.6 or abve before running this."
   echo "    For new env, first run the tool with install option to install the required python environment."
   echo
   echo "First run the environment installation using: ./stackwise-virtual.sh -i install"
   echo "Syntax: stackwise-virtual.sh [-i|h|v|c|u|d]"
   echo "options:"
   echo "  i     install run environment.: -i install"
   echo "  c     create a StackwiseVirtual for devices in yaml.: -c ./testbed/9600_sv_tb.yaml"
   echo "  u     Update an existing StactwiseVirtual with new links configs: -d ./testbed/9600_sv_tb.yaml"
   echo "  d     Delete StackwiseVirtual configs and make switches independent."
   echo "  h     Print this Help."
   echo "  v     Verbose mode."
   echo
}
############################################################
############################################################
# Main program                                             #
############################################################
############################################################
echo
echo "Stackwise Virtual:"

while getopts ":hicud:" option; do
   case $option in
      h) # display Help
         Help
         exit;;
      i) #Install env
        ./setup.sh
        exit;;
      c) #Launch create job
         source "./pyatsenv/bin/activate"
         pyats run job ./job/svl_job.py --testbed $OPTARG
         exit;;
      u) #Launch update job
         source "./pyatsenv/bin/activate"
         pyats run job ./job/svl_update_job.py --testbed $OPTARG
         exit;;
      d) #Launch destroy job
         source "./pyatsenv/bin/activate"
         pyats run job ./job/svl_remove_job.py --testbed $OPTARG
         exit;;
      \?) # Invalid option
         echo "Error: Invalid option"
         exit;;
   esac
done

