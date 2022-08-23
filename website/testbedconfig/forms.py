from xml.dom import ValidationErr
from django import forms
from django.core import validators
class ConfigForm(forms.Form):
    num_choices = [(i,i) for i in range(1,3,1)]
    priority_choices = [(i,i) for i in range(1,16,1)]
    protocol_choices = [
        ('ssh', 'ssh'),
        ('telnet', 'telnet')
    ]
    platform_choices = [
        ('9600', '9600'),
        ('9400', '9400'),
        ('9500', '9500')
    ]
    # should be the same for both switches
    # but add option to have separate username/passwords for each switch
    platform = forms.ChoiceField(choices=platform_choices, initial="9600", widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'platform'}),
                                  required=True)
    username = forms.CharField(required=True,widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'username', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(3)])
    password = forms.CharField(required=True,widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'password', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(3)])
    enablepassword = forms.CharField(required=True,widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'enablepassword', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(3)])

    username2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'username2', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(3)])
    password2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'password2', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(3)])
    enablepassword2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'enablepassword2', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(3)])

    # separate switch forms
    hostname1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'hostname1', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(1)],required=True)
    number1 = forms.ChoiceField(choices=num_choices, initial=1, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'number1'}),
                               validators=[validators.integer_validator],required=True)
    priority1 = forms.ChoiceField(choices=priority_choices, initial=15, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'priority1'}),
                                validators=[validators.integer_validator],required=True)
    ipaddress1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'ipaddress1', 'autocomplete': 'off'}),
                                 validators=[validators.validate_ipv46_address],required=True)
    port1 = forms.IntegerField(initial=22, widget=forms.NumberInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'port1', 'autocomplete': 'off'}),
                                validators=[validators.integer_validator],required=True)
    protocol1 = forms.ChoiceField(choices=protocol_choices, initial="ssh", widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'protocol1'}),
                                  required=True)

    hostname2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'hostname2', 'autocomplete': 'off'}),
                               validators=[validators.MaxLengthValidator(32),validators.MinLengthValidator(1)],required=True)
    number2 = forms.ChoiceField(choices=num_choices, initial= 2, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'number2'}),
                                validators=[validators.integer_validator],required=True)
    priority2 = forms.ChoiceField(choices=priority_choices, initial=10, widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'priority2'}),
                                validators=[validators.integer_validator],required=True)
    ipaddress2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'ipaddress2', 'autocomplete': 'off'}),
                                 validators=[validators.validate_ipv46_address],required=True)
    port2 = forms.IntegerField(initial=22, widget=forms.NumberInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'port2', 'autocomplete': 'off'}),
                                validators=[validators.integer_validator],required=True)
    protocol2 = forms.ChoiceField(choices=protocol_choices, initial="ssh", widget=forms.Select(attrs={'placeholder': ' ','class': 'form__choice', 'id': 'protocol2'}))
class LinksConfigForm(forms.Form):
    linktype_choices = [
        ('DAD', 'DAD'),
        ('SVL', 'SVL')
    ]
    interface_choices = [
        ('FortyGigE', 'FortyGigE'),
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
    interfacechoice1 = forms.ChoiceField(choices=interface_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'interfacechoice1', 'style': 'width:9.3rem; margin:0;'}))
    interfaceprefix1 = forms.ChoiceField(choices=prefix_choices, widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'interfaceprefix1', 'style': 'width:3rem; margin:0;'}))
    interfaceprefix2 = forms.ChoiceField(choices=prefix_choices, initial='2/', widget=forms.Select(attrs={'placeholder': ' ', 'class': 'form__choice', 'id': 'interfaceprefix2', 'style': 'width:3rem; margin:0;'}))
    interface1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'interface1', 'autocomplete': 'on', 'style': 'width:4rem; margin:0;'}))
    interface2 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': ' ', 'class': 'form__input', 'id': 'interface2', 'autocomplete': 'on', 'style': 'width:4rem; margin:0;'}))