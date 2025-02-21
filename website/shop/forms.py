from django.forms import ModelForm, TextInput, Select
from phonenumber_field.formfields import PhoneNumberField
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password

from .models import UserProfile, Review


class UserProfileCreationForm(UserCreationForm):
    phone_number = PhoneNumberField(
        widget=TextInput(attrs={'class': 'form-control'}), required=False, label="Телефон")
    address = forms.CharField(widget=
                              forms.Textarea(attrs={'rows': 2, 'cols': 10, 'class': 'form-control'}),
                              # размер текстового поля в attrs
                              required=False, label="Адрес")
    type_of_user = forms.ChoiceField(
        choices=[
            ('company', 'Компания'),
            ('individual', 'Частное лицо')
        ], required=False,
        label="Тип пользователя",
        widget=forms.Select(attrs={
            'class': 'form-control',  # Класс для стилизации
            'style': 'width: 300px; height: 40px; font-size: 12px'  # Устанавливаем ширину и размер шрифта
        })
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
        widget=TextInput(attrs={'class': 'form-control'}), required=False, label="Телефон")
    address = forms.CharField(widget=
                              forms.Textarea(attrs={'rows': 2, 'cols': 10, 'class': 'form-control'}),
                              # размер текстового поля в attrs
                              required=False, label="Адрес")
    type_of_user = forms.ChoiceField(
        choices=[
            ('company', 'Компания'),
            ('individual', 'Частное лицо')
        ], required=False,
        label="Тип пользователя",
        widget=forms.Select(attrs={
            'class': 'form-control',  # Класс для стилизации
            'style': 'width: 300px; height: 40px; font-size: 12px'  # Устанавливаем ширину и размер шрифта
        })
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


class AdminForm(ModelForm):
    phone_number = PhoneNumberField(
        widget=TextInput(attrs={'class': 'form-control'}), required=False, label="Телефон")
    address = forms.CharField(widget=
                              forms.Textarea(attrs={'rows': 2, 'cols': 10, 'class': 'form-control'}),
                              # размер текстового поля в attrs
                              required=False, label="Адрес")
    type_of_user = forms.ChoiceField(
        choices=[
            ('company', 'Компания'),
            ('individual', 'Частное лицо')
        ], required=False,
        label="Тип пользователя",
        widget=forms.Select(attrs={
            'class': 'form-control',  # Класс для стилизации
            'style': 'width: 300px; height: 40px; font-size: 12px'  # Устанавливаем ширину и размер шрифта
        })
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


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
