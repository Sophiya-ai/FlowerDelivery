from django.forms import ModelForm, TextInput, Select
from phonenumber_field.formfields import PhoneNumberField
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


class UserProfileCreationForm(UserCreationForm):
    phone_number = PhoneNumberField(
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}))
    address = forms.CharField(widget=forms.Textarea, required=False, label="Адрес")
    type_of_user = forms.ChoiceField(
        choices=[
            ('company', 'Компания'),
            ('individual', 'Частное лицо')
        ],
        label="Тип пользователя"
    )

    class Meta(UserCreationForm.Meta):
        model = UserProfile
        fields = UserCreationForm.Meta.fields + (
            'phone_number', 'address', 'type_of_user', 'first_name', 'last_name')  # Добавляем поля в форму

    def save(self, commit=True):
        user = super().save(commit=False)  # Сначала сохраняем User
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        user.type_of_user = self.cleaned_data['type_of_user']
        if commit:
            user.save()
        return user


class UserFormInOrderHistory(ModelForm):
    phone_number = PhoneNumberField(
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Телефон'}))
    first_name = forms.CharField(max_length=150, label='Имя')
    last_name = forms.CharField(max_length=150, label='Фамилия')

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'phone_number', 'address', 'type_of_user']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if kwargs.get('instance'):
                self.initial['first_name'] = kwargs['instance'].first_name
                self.initial['last_name'] = kwargs['instance'].last_name

        def save(self, commit=True):
            user = super().save(commit=False)  # Сначала сохраняем UserProfile
            user.first_name = self.cleaned_data['first_name']  # Обновляем имя
            user.last_name = self.cleaned_data['last_name']  # Обновляем фамилию
            if commit:
                user.save()  # Сохраняем UserProfile с обновленными именем и фамилией
            return user

        widgets = {
            'first_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'address': TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес'}),
            'type_of_user': Select(attrs={'class': 'form-control'}, choices=[
                ('company', 'Компания'),
                ('individual', 'Частное лицо'),
            ]),
        }
