#!/usr/bin/env python
"""
Скрипт для тестирования отправки уведомлений
Использует реальные настройки из config.py (если есть)
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_system.settings')
django.setup()

from notifications.services import NotificationDeliveryService
from notifications.models import NotificationUser, UserGroup

def test_notification_service():
    """Тест сервиса уведомлений"""
    print("=== Тестирование системы уведомлений ===\n")
    
    # Инициализируем сервис
    delivery_service = NotificationDeliveryService()
    
    # Тестовые данные пользователя
    test_user = {
        'email': 'test@example.com',
        'phone': '+1234567890',
        'telegram': '@testuser'
    }
    
    test_message = "Это тестовое сообщение для проверки работы системы уведомлений."
    test_subject = "Тестовое уведомление"
    
    print("Тестовые данные:")
    print(f"Email: {test_user['email']}")
    print(f"Телефон: {test_user['phone']}")
    print(f"Telegram: {test_user['telegram']}")
    print(f"Сообщение: {test_message}")
    print(f"Тема: {test_subject}\n")
    
    # Тестируем каждый способ доставки отдельно
    methods = ['email', 'sms', 'telegram']
    
    for method in methods:
        print(f"--- Тестирование {method.upper()} ---")
        
        delivery_method, status, error_message = delivery_service.send_notification(
            user_data=test_user,
            message=test_message,
            subject=test_subject,
            delivery_methods=[method]
        )
        
        if status == 'success':
            print(f"✅ {method.upper()}: Сообщение отправлено успешно")
        else:
            print(f"❌ {method.upper()}: Ошибка - {error_message}")
        
        print()
    
    # Тестируем fallback механизм
    print("--- Тестирование Fallback механизма ---")
    delivery_method, status, error_message = delivery_service.send_notification(
        user_data=test_user,
        message=test_message,
        subject=test_subject,
        delivery_methods=['email', 'sms', 'telegram']
    )
    
    print(f"Результат: {status}")
    print(f"Использован способ: {delivery_method}")
    if error_message:
        print(f"Ошибки: {error_message}")
    
    print("\n=== Статистика пользователей ===")
    total_users = NotificationUser.objects.filter(is_active=True).count()
    total_groups = UserGroup.objects.count()
    
    print(f"Всего активных пользователей: {total_users}")
    print(f"Всего групп: {total_groups}")
    
    if total_groups > 0:
        print("\nРаспределение по группам:")
        for group in UserGroup.objects.all():
            count = group.users.filter(is_active=True).count()
            print(f"  {group.name}: {count} пользователей")


def test_database_connectivity():
    """Тест подключения к базе данных"""
    print("=== Тестирование базы данных ===\n")
    
    try:
        # Проверяем подключение
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Подключение к базе данных: OK")
        
        # Проверяем таблицы
        tables = [
            'notifications_usergroup',
            'notifications_notificationuser', 
            'notifications_notificationmessage',
            'notifications_notificationlog'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Таблица {table}: {count} записей")
            
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")


def show_configuration_status():
    """Показать статус конфигурации"""
    print("=== Статус конфигурации ===\n")
    
    from django.conf import settings
    
    # Email настройки
    email_configured = all([
        getattr(settings, 'EMAIL_HOST_USER', ''),
        getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    ])
    print(f"Email: {'✅ Настроен' if email_configured else '❌ Не настроен'}")
    
    # SMS настройки
    sms_configured = all([
        getattr(settings, 'SMS_API_URL', ''),
        getattr(settings, 'SMS_API_KEY', '')
    ])
    print(f"SMS: {'✅ Настроен' if sms_configured else '❌ Не настроен'}")
    
    # Telegram настройки
    telegram_configured = bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))
    print(f"Telegram: {'✅ Настроен' if telegram_configured else '❌ Не настроен'}")
    
    print(f"\nДебаг режим: {'Включен' if settings.DEBUG else 'Выключен'}")
    print(f"Язык: {settings.LANGUAGE_CODE}")
    print(f"Часовой пояс: {settings.TIME_ZONE}")


if __name__ == '__main__':
    print("Система уведомлений - Тестирование\n")
    
    # Показываем меню
    print("Выберите тест:")
    print("1. Тест базы данных")
    print("2. Тест сервисов уведомлений")
    print("3. Статус конфигурации")
    print("4. Все тесты")
    print("0. Выход")
    
    try:
        choice = input("\nВведите номер (0-4): ").strip()
        
        if choice == '1':
            test_database_connectivity()
        elif choice == '2':
            test_notification_service()
        elif choice == '3':
            show_configuration_status()
        elif choice == '4':
            test_database_connectivity()
            print()
            show_configuration_status()
            print()
            test_notification_service()
        elif choice == '0':
            print("Выход...")
        else:
            print("Неверный выбор")
            
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
    except Exception as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)
