from django.urls import path
from . import views

urlpatterns = [
    # Главная панель
    path('', views.dashboard, name='dashboard'),
    
    # Пользователи
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/import/', views.import_users, name='import_users'),
    path('users/bulk-action/', views.bulk_action, name='bulk_action'),
    
    # Группы
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:group_id>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),
    
    # Сообщения
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/', views.message_create, name='message_create'),
    path('messages/<int:message_id>/send/', views.message_send, name='message_send'),
    
    # Логи
    path('logs/', views.logs, name='logs'),
]
