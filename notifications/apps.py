from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    
    def ready(self):
        """Запускается при готовности приложения"""
        # Запускаем сбор chat_id только если это основной процесс Django
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            from .services import telegram_collector
            telegram_collector.start_collecting()
