from django import forms

class ConfigForm(forms.Form):
    num_choices = [(i,i) for i in range(1,3,1)]
    priority_choices = [(i,i) for i in range(1,16,1)]
    protocol_choices = [
        ('telnet', 'Telnet'),
        ('SSH', 'SSH')
    ]
    
    # should be the same for both switches
    # but add option to have separate username/passwords for each switch
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'username', 'autocomplete': 'off'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'password', 'autocomplete': 'off'}))
    enablepassword = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'enablepassword', 'autocomplete': 'off'}))

    username2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'username2', 'autocomplete': 'off',}))
    password2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'password2', 'autocomplete': 'off'}))
    enablepassword2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'enablepassword2', 'autocomplete': 'off'}))

    # separate switch forms
    hostname1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'hostname1', 'autocomplete': 'off'}))
    number1 = forms.ChoiceField(choices=num_choices, initial=1, widget=forms.Select(attrs={'placeholder': ' ','class': 'form_choice', 'id': 'number1'}))
    priority1 = forms.ChoiceField(choices=priority_choices, initial=15, widget=forms.Select(attrs={'placeholder': ' ','class': 'form_choice', 'id': 'priority1'}))
    ipaddress1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'ipaddress1', 'autocomplete': 'off'}))
    port1 = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'port1', 'autocomplete': 'off'}))
    protocol1 = forms.ChoiceField(choices=protocol_choices, initial="telnet", widget=forms.Select(attrs={'placeholder': ' ','class': 'form_choice', 'id': 'protocol1'}))

    hostname2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'hostname2', 'autocomplete': 'off'}))
    number2 = forms.ChoiceField(choices=num_choices, initial= 2, widget=forms.Select(attrs={'placeholder': ' ','class': 'form_choice', 'id': 'number2'}))
    priority2 = forms.ChoiceField(choices=priority_choices, initial=10, widget=forms.Select(attrs={'placeholder': ' ','class': 'form_choice', 'id': 'priority2'}))
    ipaddress2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'ipaddress2', 'autocomplete': 'off'}))
    port2 = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'port2', 'autocomplete': 'off'}))
    protocol2 = forms.ChoiceField(choices=protocol_choices, initial="telnet", widget=forms.Select(attrs={'placeholder': ' ','class': 'form_choice', 'id': 'protocol2'}))

    # add up to three links

class LinksConfigForm(forms.Form):
    linktype_choices = [
        ('DAD', 'DAD'),
        ('SV', 'SV')
    ]
    interface_choices = [
        ('TwentyFiveGigE', 'TwentyFiveGigE'),
        ('TenGigE', 'TenGigE'),
        ('HundredGigE', 'HundredGigE')
    ]
    linktype = forms.ChoiceField(choices=linktype_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form_choice', 'id': 'linktype', 'style': 'width:5rem;'}))
    interfacechoice = forms.ChoiceField(choices=interface_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form_choice', 'id': 'interfacechoice', 'style': 'width:10rem;'}))
    interface1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'interface1', 'autocomplete': 'off', 'style': 'width:5rem;'}))
    interface2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form_input', 'id': 'interface2', 'autocomplete': 'off', 'style': 'width:5rem;'}))


