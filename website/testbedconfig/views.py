from email.mime import base
from multiprocessing.dummy import active_children
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from .forms import ConfigForm, LinksConfigForm
from django.forms import formset_factory
from pathlib import Path
import yaml
from .models import TestbedFiles
from celery.result import AsyncResult
from .tasks import create_SWV
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

def testbed_yaml_preview(request):
    base_dir = Path(__file__).resolve().parent.parent
    if 'savebtn' in request.POST:
        with open(base_dir / "files" / "testbed_preview" / "testbed-file.yaml", "w") as f:
            yaml.dump(request.session["current-testbed"], f, sort_keys=True, default_flow_style=False)

        new_testbed = TestbedFiles()
        total_files = TestbedFiles.objects.count()
        new_testbed.save_file(f"testbed-{total_files}.yaml")
        new_testbed.save()
        return redirect('saved-files')

    return render(request, 'testbed_yaml_preview.html')

def testbed_file(request):
    base_dir = Path(__file__).resolve().parent.parent.parent
    with open(base_dir / "website" / "files" / "testbed_preview" / "preview.txt") as g:
        response = HttpResponse(g)
        response["Content-Type"] = 'text/plain'
        response['Content-Disposition'] = 'inline;filename=preview.txt'   
    return response

def form_view(request):
    base_dir = Path(__file__).resolve().parent.parent.parent

    form = formset_factory(LinksConfigForm, extra=0)
    formset = form(request.POST or None)
    form = ConfigForm(request.POST or None)
    if form.is_valid() and formset.is_valid():
        with open(base_dir / "testbed" / "9600_sv_tb.yaml") as f:
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

        with open(base_dir / "website" / "files" / "testbed_preview" / "preview.txt", "w") as g:
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
        
    context = {'files': files_list}
    return render(request, 'saved_files_view.html', context)

@csrf_exempt
def run_task(request):
    if request.POST:
        if request.POST.get('job') == 'create':
            id = f"SVLTask-{request.POST.get('job')}-{request.POST.get('file').replace('.yaml', '')}"
            task = create_SWV.apply_async(args=[request.POST.get('file'), id], task_id=id)
            return JsonResponse({'task_id': task.id}, status=200)

@csrf_exempt
def get_status(request, task_id):
    task_result = AsyncResult(task_id)
    file = task_id.split('-')[2:]
    file = "-".join(file)

    now = datetime.now()
    task_date = now.strftime("%d/%m/%Y %H:%M:%S")

    result = {
        "file": file + ".yaml", 
        "task_id": task_id,
        "task_status": task_result.status,
        "task_date": task_date,
        "task_result": task_id + '.txt',
    }

    return JsonResponse(result, status=200)

@csrf_exempt
def show_file(request, file):
    file_show = open(file)
    response = FileResponse(file_show)
    return response