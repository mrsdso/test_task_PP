from django import forms
from django.core.exceptions import ValidationError
from .models import NotificationUser, UserGroup, NotificationMessage
import json
import re


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название группы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание группы'
            }),
        }
        labels = {
            'name': 'Название группы',
            'description': 'Описание',
        }


class NotificationUserForm(forms.ModelForm):
    class Meta:
        model = NotificationUser
        fields = ['external_id', 'email', 'phone', 'telegram', 'group', 'is_active']
        widgets = {
            'external_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID пользователя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'telegram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'group': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'external_id': 'ID пользователя',
            'email': 'Email',
            'phone': 'Телефон',
            'telegram': 'Telegram',
            'group': 'Группа',
            'is_active': 'Активен',
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Проверяем формат телефона
            phone_pattern = r'^\+?[1-9]\d{1,14}$'
            if not re.match(phone_pattern, phone):
                raise ValidationError('Неверный формат телефона. Используйте формат: +1234567890')
        return phone
    
    def clean_telegram(self):
        telegram = self.cleaned_data.get('telegram')
        if telegram:
            # Убираем @ если есть и добавляем его обратно
            username = telegram.lstrip('@')
            if not re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
                raise ValidationError('Неверный формат Telegram username')
            return f'@{username}'
        return telegram


class NotificationMessageForm(forms.ModelForm):
    delivery_methods = forms.MultipleChoiceField(
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('telegram', 'Telegram'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Способы доставки',
        required=True
    )
    
    target_groups = forms.ModelMultipleChoiceField(
        queryset=UserGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Целевые группы',
        required=False
    )
    
    class Meta:
        model = NotificationMessage
        fields = ['title', 'content', 'target_groups', 'send_to_all', 'delivery_methods']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тема сообщения'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Текст сообщения'
            }),
            'send_to_all': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Тема сообщения',
            'content': 'Текст сообщения',
            'send_to_all': 'Отправить всем пользователям',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        send_to_all = cleaned_data.get('send_to_all')
        target_groups = cleaned_data.get('target_groups')
        
        if not send_to_all and not target_groups:
            raise ValidationError('Выберите целевые группы или отметьте "Отправить всем пользователям"')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.delivery_methods = self.cleaned_data['delivery_methods']
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class JsonUploadForm(forms.Form):
    json_file = forms.FileField(
        label='JSON файл с пользователями',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json'
        })
    )
    
    def clean_json_file(self):
        file = self.cleaned_data.get('json_file')
        if file:
            if not file.name.endswith('.json'):
                raise ValidationError('Файл должен иметь расширение .json')
            
            try:
                content = file.read().decode('utf-8')
                file.seek(0)  # Сбрасываем указатель файла
                data = json.loads(content)
                
                if not isinstance(data, list):
                    raise ValidationError('JSON файл должен содержать массив пользователей')
                
                # Проверяем структуру данных
                required_fields = ['id', 'email', 'phone', 'telegram', 'group']
                for i, user in enumerate(data):
                    if not isinstance(user, dict):
                        raise ValidationError(f'Элемент {i+1} должен быть объектом')
                    
                    for field in required_fields:
                        if field not in user:
                            raise ValidationError(f'Элемент {i+1}: отсутствует поле "{field}"')
                
            except json.JSONDecodeError:
                raise ValidationError('Неверный формат JSON файла')
            except UnicodeDecodeError:
                raise ValidationError('Файл должен быть в кодировке UTF-8')
        
        return file


class BulkActionForm(forms.Form):
    ACTION_CHOICES = [
        ('activate', 'Активировать'),
        ('deactivate', 'Деактивировать'),
        ('delete', 'Удалить'),
        ('change_group', 'Изменить группу'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Действие'
    )
    
    new_group = forms.ModelChoiceField(
        queryset=UserGroup.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Новая группа',
        required=False
    )
    
    selected_users = forms.CharField(widget=forms.HiddenInput())
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        new_group = cleaned_data.get('new_group')
        
        if action == 'change_group' and not new_group:
            raise ValidationError('Для смены группы необходимо выбрать новую группу')
        
        return cleaned_data
