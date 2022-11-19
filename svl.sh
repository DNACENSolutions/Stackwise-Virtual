#!/bin/bash
############################################################
# Help                                                     #
############################################################
Help()
{
   # Display Help
   echo
   echo "    Stackwise-Virtual tools is to create stackwise-virtual from two independent switches"
   echo "    This tool needs python3 on the host machine, install python3.6 or abve before running this."
   echo "    For new env, first run the tool with install option to install the required python environment."
   echo
   echo "First run the environment in the docker: ./svl.sh"
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
cd "/pyats/Stackwise-Virtual"
source /pyats/bin/activate
python3 svlservices/client_manager.py $@
echo


