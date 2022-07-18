import os
import subprocess
from termios import CRDLY
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import ConfigForm, LinksConfigForm
from django.forms import formset_factory
from .run_SWV import RunSWV
from pathlib import Path

# Create your views here.
def form_entry_view(request):
    # form = ConfigForm(request.POST or None)
    # formset1 = formset_factory(LinksConfigForm, extra=0)
    # formset2 = formset_factory(LinksConfigForm)
    # formset3 = formset_factory(LinksConfigForm)
    # context = {'form': form, 'formset1': formset1, 'formset2': formset2, 'formset3': formset3}
    return render(request, 'pagetwo.html')

def test_view(request):
    form = ConfigForm(request.POST or None)
    formset_fact = formset_factory(LinksConfigForm, extra=0)
    formset = formset_fact(request.POST or None)
    config = RunSWV()

    # get data from form and put into dict
    if form.is_valid() and formset.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        enablepassword = form.cleaned_data["enablepassword"]

        cred2_dict = {}
        if (form.cleaned_data["username2"]):
            username2 = form.cleaned_data["username2"]
            password2 = form.cleaned_data["password2"]
            enablepassword2 = form.cleaned_data["enablepassword2"]
            cred2_dict["tacacs2"] = {}
            cred2_dict["passwords2"] = {}
            cred2_dict["tacacs2"]["login_prompt"] = "Username:"
            cred2_dict["tacacs2"]["password_prompt"] = "Password:"
            cred2_dict["tacacs2"]["username"] = username2
            cred2_dict["passwords2"]["tacacs"] = password2
            cred2_dict["passwords2"]["enable"] = enablepassword2
            cred2_dict["passwords2"]["line"] = enablepassword2

        else:
            cred2_dict = None

        hostname1  = form.cleaned_data["hostname1"]
        number1  = form.cleaned_data["number1"]
        priority1 = form.cleaned_data["priority1"]
        ipaddress1  = form.cleaned_data["ipaddress1"]
        port1  = form.cleaned_data["port1"]
        protocol1  = form.cleaned_data["protocol1"]
    
        hostname2  = form.cleaned_data["hostname2"]
        number2  = form.cleaned_data["number2"]
        priority2  = form.cleaned_data["priority2"]
        ipaddress2  = form.cleaned_data["ipaddress2"]
        port2  = form.cleaned_data["port2"]
        protocol2 = form.cleaned_data["protocol2"]

        interfaces1 = {}
        interfaces2 = {}
        sv_links = 1
        dad_links = 1
        for forms in formset:
            interface1 = forms.cleaned_data["interfacechoice"] + "1/" + forms.cleaned_data["interface1"]
            interface2 = forms.cleaned_data["interfacechoice"] + "2/" + forms.cleaned_data["interface2"]

            if (forms.cleaned_data["linktype"] == 'SV'):
                interfaces1[interface1] = {'link': f"STACKWISEVIRTUAL-LINK-{sv_links}", 'type': 'ethernet'}
                interfaces2[interface2] = {'link': f"STACKWISEVIRTUAL-LINK-{sv_links}", 'type': 'ethernet'}
                sv_links += 1
            elif (forms.cleaned_data["linktype"] == 'DAD'):
                interfaces1[interface1] = {'link': f"DAD-LINK-{dad_links}", 'type': 'ethernet'}
                interfaces2[interface2] = {'link': f"DAD-LINK-{dad_links}", 'type': 'ethernet'}
                dad_links += 1
        
        form = ConfigForm()
        data = {
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
            }
        formset = formset_fact(data)

        config.username = username
        config.password = password
        config.enablepassword = enablepassword
        config.cred2 = cred2_dict
        config.hostname1 = hostname1
        config.number1 = number1
        config.priority1 = priority1
        config.ipaddress1 = ipaddress1
        config.port1 = port1
        config.protocol1 = protocol1
        config.hostname2 = hostname2
        config.number2 = number2
        config.priority2 = priority2
        config.ipaddress2 = ipaddress2
        config.port2 = port2
        config.protocol2 = protocol2
        config.interfaces1 = interfaces1
        config.interfaces2 = interfaces2

        config.create_yaml()
        config.txt_file()
        return redirect('yaml-preview')

    context = {'form': form, 'formset': formset}

    return render(request, 'pagetwo.html', context)
    #  configure yaml file

def yaml_view(request):
    base_dir = Path(__file__).resolve().parent
    with open(base_dir / "testbed" / "SV_testbed.txt") as g:
        response = HttpResponse(g)
        response["Content-Type"] = 'text/plain'
        response['Content-Disposition'] = 'inline;filename=yaml_preview.txt'
        
    return response

def yaml_preview(request):
    if 'runbtn' in request.POST:
        # base_dir = Path(__file__).resolve().parent.parent.parent.parent
        # os.chdir(base_dir)
        # process = subprocess.run(["./stackwisevirtual.sh", "-c", "./src/stackwise_virtual/testbed_config/testbed/SV_testbed.yaml"], shell=True)
        config = RunSWV()
        config.run_script()
        return redirect('run-tests')
    return render(request, 'pagethree.html')

def tests_view(request):
    config = RunSWV()
    config.get_logs()
    return render(request, 'pagefour.html')