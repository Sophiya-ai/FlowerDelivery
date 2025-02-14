from django.forms import ModelForm, TextInput, Select
from phonenumber_field.formfields import PhoneNumberField

from .models import User


class UserFormInOrderHistory(ModelForm):
    phone_number = PhoneNumberField(
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'address', 'type_of_user']
        widgets = {
            'first_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'address': TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес'}),
            'type_of_user': Select(attrs={'class': 'form-control'}, choices=[
                ('company', 'Компания'),
                ('individual', 'Частное лицо'),
            ]),
        }
