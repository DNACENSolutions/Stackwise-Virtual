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
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'username', 'autocomplete': 'off'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'password', 'autocomplete': 'off'}))
    enablepassword = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'enablepassword', 'autocomplete': 'off'}))

    username2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'username2', 'autocomplete': 'off',}))
    password2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'password2', 'autocomplete': 'off'}))
    enablepassword2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'enablepassword2', 'autocomplete': 'off'}))

    # separate switch forms
    hostname1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'hostname1', 'autocomplete': 'off'}))
    number1 = forms.ChoiceField(choices=num_choices, initial=1, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'number1'}))
    priority1 = forms.ChoiceField(choices=priority_choices, initial=15, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'priority1'}))
    ipaddress1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'ipaddress1', 'autocomplete': 'off'}))
    port1 = forms.IntegerField(initial=22, widget=forms.NumberInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'port1', 'autocomplete': 'off'}))
    protocol1 = forms.ChoiceField(choices=protocol_choices, initial="SSH", widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'protocol1'}))

    hostname2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'hostname2', 'autocomplete': 'off'}))
    number2 = forms.ChoiceField(choices=num_choices, initial= 2, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'number2'}))
    priority2 = forms.ChoiceField(choices=priority_choices, initial=10, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'priority2'}))
    ipaddress2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'ipaddress2', 'autocomplete': 'off'}))
    port2 = forms.IntegerField(initial=22, widget=forms.NumberInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'port2', 'autocomplete': 'off'}))
    protocol2 = forms.ChoiceField(choices=protocol_choices, initial="SSH", widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'protocol2'}))
    


class LinksConfigForm(forms.Form):
    linktype_choices = [
        ('DAD', 'DAD'),
        ('SVL', 'SVL')
    ]
    interface_choices = [
        ('TwentyFiveGigE', 'TwentyFiveGigE'),
        ('TenGigE', 'TenGigE'),
        ('HundredGigE', 'HundredGigE')
    ]
    prefix_choices = [
        ('1/', '1/'),
        ('2/', '2/')
    ]
    linktype = forms.ChoiceField(choices=linktype_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'linktype', 'style': 'width:5rem; margin:0;'}))
    interfacechoice = forms.ChoiceField(choices=interface_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'interfacechoice', 'style': 'width:9.3rem; margin:0;'}))
    interfaceprefix1 = forms.ChoiceField(choices=prefix_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'interfaceprefix1', 'style': 'width:3rem; margin:0;'}))
    interfaceprefix2 = forms.ChoiceField(choices=prefix_choices, initial='2/', widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'interfaceprefix2', 'style': 'width:3rem; margin:0;'}))
    interface1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'interface1', 'autocomplete': 'off', 'style': 'width:4rem; margin:0;'}))
    interface2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'interface2', 'autocomplete': 'off', 'style': 'width:4rem; margin:0;'}))
