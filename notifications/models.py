from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Группа пользователей"
        verbose_name_plural = "Группы пользователей"


class NotificationUser(models.Model):
    external_id = models.IntegerField(unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    telegram = models.CharField(max_length=100)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='users')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"User {self.external_id} ({self.email})"
    
    class Meta:
        verbose_name = "Пользователь уведомлений"
        verbose_name_plural = "Пользователи уведомлений"


class NotificationMessage(models.Model):
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('telegram', 'Telegram'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    target_groups = models.ManyToManyField(UserGroup, blank=True)
    send_to_all = models.BooleanField(default=False)
    delivery_methods = models.JSONField(default=list)  # ['email', 'sms', 'telegram']
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} ({self.created_at})"
    
    class Meta:
        verbose_name = "Сообщение уведомления"
        verbose_name_plural = "Сообщения уведомлений"
        ordering = ['-created_at']


class NotificationLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Неудачно'),
        ('partial', 'Частично успешно'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('telegram', 'Telegram'),
    ]
    
    message = models.ForeignKey(NotificationMessage, on_delete=models.CASCADE)
    user = models.ForeignKey(NotificationUser, on_delete=models.CASCADE)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.external_id} - {self.delivery_method} - {self.status}"
    
    class Meta:
        verbose_name = "Лог уведомления"
        verbose_name_plural = "Логи уведомлений"
        ordering = ['-sent_at']
