#!/usr/bin/env python
import os
import sys
import django
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_system.settings')
django.setup()

from notifications.models import NotificationUser, UserGroup

def load_users_from_json():
    """Загрузка пользователей из JSON файла"""
    try:
        with open('users_data.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        imported_count = 0
        errors = []
        
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
                
                if created:
                    print(f"Создан пользователь {user_data['id']}: {user_data['email']}")
                else:
                    print(f"Обновлен пользователь {user_data['id']}: {user_data['email']}")
                    
            except Exception as e:
                error_msg = f"Пользователь ID {user_data.get('id', '?')}: {str(e)}"
                errors.append(error_msg)
                print(f"ОШИБКА: {error_msg}")
        
        print(f"\nИтого: импортировано {imported_count} пользователей")
        if errors:
            print(f"Ошибок: {len(errors)}")
            for error in errors[:5]:  # Показываем первые 5 ошибок
                print(f"  - {error}")
        
        # Статистика по группам
        print("\nСтатистика по группам:")
        for group in UserGroup.objects.all():
            count = group.users.filter(is_active=True).count()
            print(f"  {group.name}: {count} пользователей")
                
    except Exception as e:
        print(f"Ошибка загрузки JSON файла: {e}")

if __name__ == '__main__':
    load_users_from_json()
