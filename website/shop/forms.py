from .models import User
from django.forms import ModelForm, TextInput, Select


class UserFormInOrderHistory(ModelForm):
    class Meta:
        model = User
        fields = ['phone_number', 'address', 'type_of_user']
        widgets = {
            'phone_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон пользователя'}),
            'address': TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес пользователя'}),
            'type_of_user': Select(attrs={'class': 'form-control'}, choices=[
                ('company', 'Компания'),
                ('individual', 'Частное лицо'),
            ]),
        }
