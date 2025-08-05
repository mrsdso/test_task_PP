from django.core.management.base import BaseCommand
from notifications.services import telegram_collector
import time


class Command(BaseCommand):
    help = 'Запустить сбор Telegram chat_id в режиме реального времени'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Выполнить сбор один раз и выйти',
        )

    def handle(self, *args, **options):
        if options['once']:
            self.stdout.write("Выполняется однократный сбор chat_id...")
            telegram_collector._process_updates()
            self.stdout.write(
                self.style.SUCCESS('Сбор chat_id завершен')
            )
        else:
            self.stdout.write("Запуск постоянного сбора chat_id...")
            self.stdout.write("Нажмите Ctrl+C для остановки")
            
            try:
                telegram_collector.start_collecting()
                
                while telegram_collector.running:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.stdout.write("\nОстановка сбора...")
                telegram_collector.stop_collecting()
                self.stdout.write(
                    self.style.SUCCESS('Сбор chat_id остановлен')
                )
