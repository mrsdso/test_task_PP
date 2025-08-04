from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.utils import timezone
import json
import os
from .models import NotificationUser, UserGroup, NotificationMessage, NotificationLog
from .forms import (
    NotificationUserForm, UserGroupForm, NotificationMessageForm,
    JsonUploadForm, BulkActionForm
)
from .services import (
    NotificationDeliveryService, load_users_from_json, 
    save_users_to_json, create_notification_log
)


@login_required
def dashboard(request):
    """Главная панель управления"""
    context = {
        'total_users': NotificationUser.objects.filter(is_active=True).count(),
        'total_groups': UserGroup.objects.count(),
        'total_messages': NotificationMessage.objects.count(),
        'recent_messages': NotificationMessage.objects.all()[:5],
        'recent_logs': NotificationLog.objects.all()[:10],
    }
    return render(request, 'notifications/dashboard.html', context)


@login_required
def user_list(request):
    """Список пользователей"""
    users = NotificationUser.objects.select_related('group').all()
    
    # Фильтрация
    group_filter = request.GET.get('group')
    if group_filter:
        users = users.filter(group_id=group_filter)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(email__icontains=search) |
            models.Q(phone__icontains=search) |
            models.Q(telegram__icontains=search)
        )
    
    # Пагинация
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'groups': UserGroup.objects.all(),
        'bulk_form': BulkActionForm(),
    }
    return render(request, 'notifications/user_list.html', context)


@login_required
def user_create(request):
    """Создание пользователя"""
    if request.method == 'POST':
        form = NotificationUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пользователь успешно создан')
            return redirect('user_list')
    else:
        form = NotificationUserForm()
    
    return render(request, 'notifications/user_form.html', {
        'form': form,
        'title': 'Создать пользователя'
    })


@login_required
def user_edit(request, user_id):
    """Редактирование пользователя"""
    user = get_object_or_404(NotificationUser, id=user_id)
    
    if request.method == 'POST':
        form = NotificationUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пользователь успешно обновлен')
            return redirect('user_list')
    else:
        form = NotificationUserForm(instance=user)
    
    return render(request, 'notifications/user_form.html', {
        'form': form,
        'title': 'Редактировать пользователя',
        'user': user
    })


@login_required
def user_delete(request, user_id):
    """Удаление пользователя"""
    user = get_object_or_404(NotificationUser, id=user_id)
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Пользователь успешно удален')
        return redirect('user_list')
    
    return render(request, 'notifications/user_delete.html', {'user': user})


@login_required
def group_list(request):
    """Список групп"""
    groups = UserGroup.objects.all()
    
    # Добавляем количество пользователей в каждой группе
    for group in groups:
        group.user_count = group.users.filter(is_active=True).count()
    
    return render(request, 'notifications/group_list.html', {'groups': groups})


@login_required
def group_create(request):
    """Создание группы"""
    if request.method == 'POST':
        form = UserGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Группа успешно создана')
            return redirect('group_list')
    else:
        form = UserGroupForm()
    
    return render(request, 'notifications/group_form.html', {
        'form': form,
        'title': 'Создать группу'
    })


@login_required
def group_edit(request, group_id):
    """Редактирование группы"""
    group = get_object_or_404(UserGroup, id=group_id)
    
    if request.method == 'POST':
        form = UserGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Группа успешно обновлена')
            return redirect('group_list')
    else:
        form = UserGroupForm(instance=group)
    
    return render(request, 'notifications/group_form.html', {
        'form': form,
        'title': 'Редактировать группу',
        'group': group
    })


@login_required
def group_delete(request, group_id):
    """Удаление группы"""
    group = get_object_or_404(UserGroup, id=group_id)
    
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Группа успешно удалена')
        return redirect('group_list')
    
    return render(request, 'notifications/group_delete.html', {'group': group})


@login_required
def message_create(request):
    """Создание и отправка сообщения"""
    if request.method == 'POST':
        form = NotificationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.created_by = request.user
            message.save()
            form.save_m2m()
            
            messages.success(request, 'Сообщение создано')
            return redirect('message_send', message_id=message.id)
    else:
        form = NotificationMessageForm()
    
    return render(request, 'notifications/message_form.html', {
        'form': form,
        'title': 'Создать сообщение'
    })


@login_required
def message_send(request, message_id):
    """Отправка сообщения"""
    message = get_object_or_404(NotificationMessage, id=message_id)
    
    if request.method == 'POST':
        # Получаем целевых пользователей
        if message.send_to_all:
            target_users = NotificationUser.objects.filter(is_active=True)
        else:
            target_users = NotificationUser.objects.filter(
                group__in=message.target_groups.all(),
                is_active=True
            )
        
        # Инициализируем сервис доставки
        delivery_service = NotificationDeliveryService()
        
        # Список для логирования
        log_data = []
        success_count = 0
        total_count = target_users.count()
        
        # Отправляем сообщения
        for user in target_users:
            user_data = {
                'email': user.email,
                'phone': user.phone,
                'telegram': user.telegram,
            }
            
            delivery_method, status, error_message = delivery_service.send_notification(
                user_data=user_data,
                message=message.content,
                subject=message.title,
                delivery_methods=message.delivery_methods
            )
            
            # Сохраняем лог в базу данных
            NotificationLog.objects.create(
                message=message,
                user=user,
                delivery_method=delivery_method if delivery_method != 'none' else 'failed',
                status=status,
                error_message=error_message
            )
            
            # Добавляем в лог файл
            log_data.append({
                'user_id': user.external_id,
                'email': user.email,
                'delivery_method': delivery_method,
                'status': status,
                'error_message': error_message,
                'timestamp': timezone.now().isoformat()
            })
            
            if status == 'success':
                success_count += 1
        
        # Создаем лог файл
        log_file = create_notification_log(log_data)
        
        # Обновляем статус сообщения
        message.is_sent = True
        message.sent_at = timezone.now()
        message.save()
        
        messages.success(
            request,
            f'Сообщение отправлено! Успешно: {success_count}/{total_count}. '
            f'Лог файл: {log_file}'
        )
        
        return redirect('message_list')
    
    # Показываем превью
    if message.send_to_all:
        target_users = NotificationUser.objects.filter(is_active=True)
    else:
        target_users = NotificationUser.objects.filter(
            group__in=message.target_groups.all(),
            is_active=True
        )
    
    context = {
        'message': message,
        'target_users': target_users,
        'total_recipients': target_users.count(),
    }
    
    return render(request, 'notifications/message_send.html', context)


@login_required
def message_list(request):
    """Список сообщений"""
    messages_qs = NotificationMessage.objects.select_related('created_by').all()
    
    paginator = Paginator(messages_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notifications/message_list.html', {'page_obj': page_obj})


@login_required
def import_users(request):
    """Импорт пользователей из JSON"""
    if request.method == 'POST':
        form = JsonUploadForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = form.cleaned_data['json_file']
            
            try:
                content = json_file.read().decode('utf-8')
                users_data = json.loads(content)
                
                imported_count = 0
                errors = []
                
                with transaction.atomic():
                    for user_data in users_data:
                        try:
                            # Получаем или создаем группу
                            group, created = UserGroup.objects.get_or_create(
                                name=user_data['group'],
                                defaults={'description': f'Группа {user_data["group"]}'}
                            )
                            
                            # Создаем или обновляем пользователя
                            user, created = NotificationUser.objects.update_or_create(
                                external_id=user_data['id'],
                                defaults={
                                    'email': user_data['email'],
                                    'phone': user_data['phone'],
                                    'telegram': user_data['telegram'],
                                    'group': group,
                                    'is_active': True,
                                }
                            )
                            imported_count += 1
                            
                        except Exception as e:
                            errors.append(f"Пользователь ID {user_data.get('id', '?')}: {str(e)}")
                
                if errors:
                    messages.warning(
                        request,
                        f'Импортировано {imported_count} пользователей. Ошибки: {"; ".join(errors[:5])}'
                    )
                else:
                    messages.success(request, f'Успешно импортировано {imported_count} пользователей')
                
                return redirect('user_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка импорта: {str(e)}')
    else:
        form = JsonUploadForm()
    
    return render(request, 'notifications/import_users.html', {'form': form})


@login_required
def bulk_action(request):
    """Массовые операции над пользователями"""
    if request.method == 'POST':
        form = BulkActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            selected_users = form.cleaned_data['selected_users'].split(',')
            selected_users = [int(id) for id in selected_users if id.isdigit()]
            
            users = NotificationUser.objects.filter(id__in=selected_users)
            
            if action == 'activate':
                users.update(is_active=True)
                messages.success(request, f'Активировано {users.count()} пользователей')
            elif action == 'deactivate':
                users.update(is_active=False)
                messages.success(request, f'Деактивировано {users.count()} пользователей')
            elif action == 'delete':
                count = users.count()
                users.delete()
                messages.success(request, f'Удалено {count} пользователей')
            elif action == 'change_group':
                new_group = form.cleaned_data['new_group']
                users.update(group=new_group)
                messages.success(request, f'Изменена группа для {users.count()} пользователей')
    
    return redirect('user_list')


@login_required
def logs(request):
    """Просмотр логов"""
    logs = NotificationLog.objects.select_related('message', 'user').all()
    
    # Фильтрация
    status_filter = request.GET.get('status')
    if status_filter:
        logs = logs.filter(status=status_filter)
    
    method_filter = request.GET.get('method')
    if method_filter:
        logs = logs.filter(delivery_method=method_filter)
    
    # Пагинация
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': NotificationLog.STATUS_CHOICES,
        'method_choices': NotificationLog.DELIVERY_METHOD_CHOICES,
    }
    
    return render(request, 'notifications/logs.html', context)
