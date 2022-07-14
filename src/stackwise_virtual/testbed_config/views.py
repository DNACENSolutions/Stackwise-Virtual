from django.shortcuts import render, redirect
from .forms import ConfigForm, LinksConfigForm
from django.forms import formset_factory
from .run_SWV import RunSWV

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
    formset1 = formset_factory(LinksConfigForm, extra=0)
    config = RunSWV()

    # get data from form and put into dict
    if form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        enablepassword = form.cleaned_data["enablepassword"]
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
        
        form = ConfigForm()

        config.username = username
        config.password = password
        config.enablepassword = enablepassword
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

        config.create_yaml()
        return redirect('yaml-preview')

    context = {'form': form, 'formset1': formset1}

    return render(request, 'pagetwo.html', context)
    #  configure yaml file

def yaml_view(request):
    config = RunSWV()
    parsed = config.txt_file()
    context = {'parsed': parsed}
    return render(request, "pagethree.html", context)
    