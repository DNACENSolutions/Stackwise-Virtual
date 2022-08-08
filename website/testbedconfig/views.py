from email.mime import base
from multiprocessing.dummy import active_children
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ConfigForm, LinksConfigForm
from django.forms import formset_factory
from pathlib import Path
import yaml
from .models import TestbedFiles
from multiprocessing import Process, current_process, active_children
from . import tasks

def testbed_yaml_preview(request):
    base_dir = Path(__file__).resolve().parent
    if 'savebtn' in request.POST:
        with open(base_dir / "testbed-file.yaml", "w") as f:
            yaml.dump(request.session["current-testbed"], f, sort_keys=True, default_flow_style=False)

        new_testbed = TestbedFiles()
        total_files = TestbedFiles.objects.count()
        new_testbed.save_file(f"testbed-{total_files}.yaml")
        new_testbed.save()
        return redirect('saved-files')

    return render(request, 'testbed_yaml_preview.html')

def testbed_file(request):
    base_dir = Path(__file__).resolve().parent
    with open(base_dir / "file.txt") as g:
        response = HttpResponse(g)
        response["Content-Type"] = 'text/plain'
        response['Content-Disposition'] = 'inline;filename=file.txt'   
    return response

def form_view(request):
    base_dir = Path(__file__).resolve().parent

    form = formset_factory(LinksConfigForm, extra=0)
    formset = form(request.POST or None)
    form = ConfigForm(request.POST or None)
    if form.is_valid() and formset.is_valid():
        with open(base_dir / "9600_sv_tb.yaml") as f:
            testbed = yaml.safe_load(f)
            testbed["testbed"]["tacacs"]["username"] = form.cleaned_data["username"]
            testbed["testbed"]["passwords"]["tacacs"] = form.cleaned_data["password"]
            testbed["testbed"]["passwords"]["enable"] = form.cleaned_data["enablepassword"]
            testbed["testbed"]["passwords"]["line"] = form.cleaned_data["enablepassword"]

            if (form.cleaned_data["username2"]):
                cred2_dict = {"tacacs2": 
                            {
                                "login_prompt": "Username:", 
                                "password_prompt": "Password:"
                            }, 
                         "passwords2": {}}

                cred2_dict["tacacs2"]["username"] = form.cleaned_data["username2"]
                cred2_dict["passwords2"]["tacacs"] = form.cleaned_data["password2"]
                cred2_dict["passwords2"]["enable"] = form.cleaned_data["enablepassword2"]
                cred2_dict["passwords2"]["line"] = form.cleaned_data["enablepassword2"]

                testbed["testbed"].update(cred2_dict)
                testbed["devices"]["SWITCH-2"]["tacacs"] = "%{testbed.tacacs2}"
                testbed["devices"]["SWITCH-2"]["passwords"] = "%{testbed.passwords2}"

            testbed["devices"]["SWITCH-1"]["alias"] = form.cleaned_data["hostname1"]
            testbed["devices"]["SWITCH-1"]["custom"]["switchnumber"] = form.cleaned_data["number1"]
            testbed["devices"]["SWITCH-1"]["custom"]["switchpriority"] = form.cleaned_data["priority1"]
            testbed["devices"]["SWITCH-1"]["connections"]["a"]["protocol"] = form.cleaned_data["protocol1"]
            testbed["devices"]["SWITCH-1"]["connections"]["a"]["ip"] = form.cleaned_data["ipaddress1"]
            testbed["devices"]["SWITCH-1"]["connections"]["a"]["port"] = form.cleaned_data["port1"]

            testbed["devices"]["SWITCH-2"]["alias"] = form.cleaned_data["hostname2"]
            testbed["devices"]["SWITCH-2"]["custom"]["switchnumber"] = form.cleaned_data["number2"]
            testbed["devices"]["SWITCH-2"]["custom"]["switchpriority"] = form.cleaned_data["priority2"]
            testbed["devices"]["SWITCH-2"]["connections"]["a"]["protocol"] = form.cleaned_data["protocol2"]
            testbed["devices"]["SWITCH-2"]["connections"]["a"]["ip"] = form.cleaned_data["ipaddress2"] 
            testbed["devices"]["SWITCH-2"]["connections"]["a"]["port"] = form.cleaned_data["port2"]

            interfaces1 = {}
            interfaces2 = {}
            sv_links = 1
            dad_links = 1
            for forms in formset:
                interfaceprefix1 = forms.cleaned_data["interfaceprefix1"]
                interfaceprefix2 = forms.cleaned_data["interfaceprefix2"]
                interface1 = forms.cleaned_data["interfacechoice"] + interfaceprefix1 + forms.cleaned_data["interface1"]
                interface2 = forms.cleaned_data["interfacechoice"] + interfaceprefix2 + forms.cleaned_data["interface2"]

                if (forms.cleaned_data["linktype"] == 'SV'):
                    interfaces1[interface1] = {'link': f"STACKWISEVIRTUAL-LINK-{sv_links}", 'type': 'ethernet'}
                    interfaces2[interface2] = {'link': f"STACKWISEVIRTUAL-LINK-{sv_links}", 'type': 'ethernet'}
                    sv_links += 1
                elif (forms.cleaned_data["linktype"] == 'DAD'):
                    interfaces1[interface1] = {'link': f"DAD-LINK-{dad_links}", 'type': 'ethernet'}
                    interfaces2[interface2] = {'link': f"DAD-LINK-{dad_links}", 'type': 'ethernet'}
                    dad_links += 1

            testbed["topology"]["SWITCH-1"]["interfaces"].clear()
            testbed["topology"]["SWITCH-1"]["interfaces"].update(interfaces1)
            testbed["topology"]["SWITCH-2"]["interfaces"].clear()
            testbed["topology"]["SWITCH-2"]["interfaces"].update(interfaces2)

            request.session['current-testbed'] = testbed

        with open(base_dir / "file.txt", "w") as g:
            yaml.dump(testbed, g, sort_keys=True, default_flow_style=False)

        return redirect("testbed-preview")

    context = {'form': form, 'formset': formset}
    return render(request, 'form_view.html', context)

def saved_files_view(request):
    list = TestbedFiles.objects.all()
    files_list = []
    for object in list:
        name = object.file.name
        files_list.append(name.split("/")[1])

    # delete_SWV = Process(target=tasks.delete_SWV())
    # update_SWV = Process(target=tasks.update_SWV())

    running = None

    if 'create' in request.POST:
        file = f"./website/files/testbeds/{request.POST.get('file')}"
        create_SWV = Process(target=tasks.create_SWV, args=(file,))
        # create_SWV.start()
        # create_SWV.id = f'SVLTask-create-{request.POST.get("file")}'
        running = f'SVLTask-create-{request.POST.get("file")}'

    if 'delete' in request.POST:
        file = f"./website/files/testbeds/{request.POST.get('file')}"
        delete_SWV = Process(target=tasks.delete_SWV, args=(file,))

    if 'update' in request.POST:
        file = f"./website/files/testbeds/{request.POST.get('file')}"
        update_SWV = Process(target=tasks.update_SWV, args=(file,))

    active = current_process()
    print(active)

    print(running)
    context = {'files': files_list, 'running': running}
    return render(request, 'saved_files_view.html', context)