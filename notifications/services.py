import smtplib
import json
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, List, Tuple
import asyncio
from datetime import datetime
import threading
import time


logger = logging.getLogger(__name__)


class TelegramChatIdCollector:
    """Сервис для автоматического сбора chat_id пользователей"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.running = False
        self.thread = None
        self.last_update_id = None
    
    def start_collecting(self):
        """Запустить сбор chat_id в фоновом режиме"""
        if self.running or not self.bot_token:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        logger.info("Telegram chat_id collector запущен")
    
    def stop_collecting(self):
        """Остановить сбор"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Telegram chat_id collector остановлен")
    
    def _collect_loop(self):
        """Основной цикл сбора обновлений"""
        while self.running:
            try:
                self._process_updates()
                time.sleep(5)  # Проверяем каждые 5 секунд
            except Exception as e:
                logger.error(f"Ошибка в сборе chat_id: {e}")
                time.sleep(10)  # При ошибке ждем дольше
    
    def _process_updates(self):
        """Обработать новые сообщения"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {}
            
            if self.last_update_id:
                params['offset'] = self.last_update_id + 1
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return
            
            data = response.json()
            if not data.get('ok'):
                return
            
            updates = data.get('result', [])
            
            for update in updates:
                self.last_update_id = update.get('update_id')
                self._process_single_update(update)
                
        except Exception as e:
            logger.error(f"Ошибка обработки обновлений: {e}")
    
    def _process_single_update(self, update):
        """Обработать одно обновление"""
        try:
            if 'message' not in update:
                return
            
            message = update['message']
            chat = message.get('chat', {})
            chat_id = chat.get('id')
            username = chat.get('username', '')
            
            if not chat_id:
                return
            
            # Ищем пользователя по username
            if username:
                from .models import NotificationUser
                from django.db import models
                
                users = NotificationUser.objects.filter(
                    models.Q(telegram=f"@{username}") | 
                    models.Q(telegram=username)
                )
                
                for user in users:
                    if user.telegram_chat_id != chat_id:
                        user.telegram_chat_id = chat_id
                        user.save()
                        logger.info(f"Обновлен chat_id для {user.external_id}: {chat_id}")
                        
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")


# Глобальный экземпляр коллектора
telegram_collector = TelegramChatIdCollector()


class NotificationService:
    """Базовый класс для сервисов уведомлений"""
    
    def send(self, recipient: str, message: str, subject: str = "") -> Tuple[bool, str]:
        """
        Отправить уведомление
        Returns: (success: bool, error_message: str)
        """
        raise NotImplementedError


class EmailService(NotificationService):
    """Сервис отправки email уведомлений"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        self.username = getattr(settings, 'EMAIL_HOST_USER', '')
        self.password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', self.username)
    
    def send(self, recipient: str, message: str, subject: str = "Уведомление") -> Tuple[bool, str]:
        try:
            if not self.username or not self.password:
                return False, "Email настройки не сконфигурированы"
            
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email отправлен успешно на {recipient}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Ошибка отправки email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


class SMSService(NotificationService):
    """Сервис отправки SMS уведомлений"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'SMS_API_URL', '')
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.sender = getattr(settings, 'SMS_SENDER', 'NotifySystem')
    
    def send(self, recipient: str, message: str, subject: str = "") -> Tuple[bool, str]:
        try:
            if not self.api_url or not self.api_key:
                return False, "SMS настройки не сконфигурированы"
            
            # Пример для SMS.ru API (можно адаптировать под любой SMS сервис)
            data = {
                'api_id': self.api_key,
                'to': recipient,
                'msg': message,
                'from': self.sender,
                'json': 1
            }
            
            response = requests.post(self.api_url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'OK':
                    logger.info(f"SMS отправлен успешно на {recipient}")
                    return True, ""
                else:
                    error_msg = f"SMS API ошибка: {result.get('status_text', 'Неизвестная ошибка')}"
                    logger.error(error_msg)
                    return False, error_msg
            else:
                error_msg = f"HTTP ошибка: {response.status_code}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Ошибка отправки SMS: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


class TelegramService(NotificationService):
    """Сервис отправки Telegram уведомлений"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.bot = None
        if self.bot_token:
            try:
                self.bot = Bot(token=self.bot_token)
            except Exception as e:
                logger.error(f"Ошибка инициализации Telegram бота: {e}")
    
    def send(self, recipient: str, message: str, subject: str = "") -> Tuple[bool, str]:
        try:
            if not self.bot:
                return False, "Telegram бот не сконфигурирован"
            
            # Если передан username, ищем chat_id в базе
            if recipient.startswith('@') or not recipient.isdigit():
                from .models import NotificationUser
                from django.db import models
                
                # Ищем пользователя по telegram username
                try:
                    user = NotificationUser.objects.get(
                        models.Q(telegram=recipient) | 
                        models.Q(telegram=recipient.lstrip('@'))
                    )
                    
                    if not user.telegram_chat_id:
                        return False, f"Chat ID не найден для {recipient}. Пользователь должен написать боту."
                    
                    chat_id = user.telegram_chat_id
                    
                except NotificationUser.DoesNotExist:
                    return False, f"Пользователь {recipient} не найден в базе данных."
            else:
                # Если передан числовой chat_id
                try:
                    chat_id = int(recipient)
                except ValueError:
                    return False, f"Неверный формат chat_id: {recipient}"
            
            # Формируем полное сообщение
            full_message = f"*{subject}*\n\n{message}" if subject else message

            # Используем синхронную отправку через requests
            import requests
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': full_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                logger.info(f"Telegram сообщение отправлено успешно на chat_id: {chat_id}")
                return True, ""
            else:
                error_msg = f"Ошибка API Telegram: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg
            
        except TelegramError as e:
            error_msg = f"Telegram ошибка: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Ошибка отправки Telegram: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


class NotificationDeliveryService:
    """Главный сервис доставки уведомлений с поддержкой fallback"""
    
    def __init__(self):
        self.services = {
            'email': EmailService(),
            'sms': SMSService(),
            'telegram': TelegramService(),
        }
    
    def send_notification(self, user_data: Dict, message: str, subject: str, 
                         delivery_methods: List[str]) -> Tuple[str, str, str]:
        """
        Отправить уведомление пользователю с поддержкой fallback
        
        Args:
            user_data: Данные пользователя (email, phone, telegram)
            message: Текст сообщения
            subject: Тема сообщения
            delivery_methods: Список способов доставки ['email', 'sms', 'telegram']
        
        Returns:
            Tuple[delivery_method_used, status, error_message]
            delivery_method_used: какой способ сработал или 'none'
            status: 'success' или 'failed'
            error_message: сообщение об ошибке если есть
        """
        
        errors = []
        
        for method in delivery_methods:
            if method not in self.services:
                errors.append(f"Неизвестный способ доставки: {method}")
                continue
            
            service = self.services[method]
            
            # Определяем получателя в зависимости от способа доставки
            recipient = None
            if method == 'email':
                recipient = user_data.get('email')
            elif method == 'sms':
                recipient = user_data.get('phone')
            elif method == 'telegram':
                recipient = user_data.get('telegram')
            
            if not recipient:
                errors.append(f"Отсутствует {method} для пользователя")
                continue
            
            # Пытаемся отправить
            success, error = service.send(recipient, message, subject)
            
            if success:
                return method, 'success', ''
            else:
                errors.append(f"{method}: {error}")
        
        # Если ничего не сработало
        return 'none', 'failed', '; '.join(errors)


def load_users_from_json(file_path: str) -> List[Dict]:
    """Загрузить пользователей из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей из JSON: {e}")
        return []


def save_users_to_json(file_path: str, users: List[Dict]) -> bool:
    """Сохранить пользователей в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователей в JSON: {e}")
        return False


def create_notification_log(log_data: List[Dict], file_name: str = None) -> str:
    """
    Создать лог файл с результатами отправки уведомлений
    
    Args:
        log_data: Список словарей с данными о доставке
        file_name: Имя файла (если None, создается автоматически)
    
    Returns:
        Путь к созданному файлу
    """
    if not file_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"notification_log_{timestamp}.json"
    
    try:
        log_path = f"logs/{file_name}"
        
        # Создаем директорию если не существует
        import os
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Лог файл создан: {log_path}")
        return log_path
        
    except Exception as e:
        logger.error(f"Ошибка создания лог файла: {e}")
        return ""
