# Конфигурация системы уведомлений
# Скопируйте этот файл в config.py и настройте под ваши нужды

# ==============================================
# НАСТРОЙКИ EMAIL
# ==============================================

# Базовые настройки SMTP
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Учетные данные (для Gmail используйте пароли приложений)
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ==============================================
# НАСТРОЙКИ SMS
# ==============================================

# Настройки для SMS.ru (замените на ваш SMS провайдер)
SMS_API_URL = 'https://sms.ru/sms/send'
SMS_API_KEY = 'your-sms-api-key'
SMS_SENDER = 'NotifySystem'

# Альтернативно для других провайдеров:
# Для Twilio:
# SMS_API_URL = 'https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json'
# SMS_ACCOUNT_SID = 'your-account-sid'
# SMS_AUTH_TOKEN = 'your-auth-token'
# SMS_FROM_PHONE = '+1234567890'

# ==============================================
# НАСТРОЙКИ TELEGRAM
# ==============================================

# Токен бота (получите у @BotFather)
TELEGRAM_BOT_TOKEN = 'your-bot-token'

# ==============================================
# НАСТРОЙКИ БЕЗОПАСНОСТИ
# ==============================================

# Секретный ключ Django (сгенерируйте новый для production)
SECRET_KEY = 'your-secret-key-here'

# Разрешенные хосты (для production)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com']

# Настройки HTTPS (для production)
USE_TLS = False  # Установите True для production с HTTPS
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ==============================================
# НАСТРОЙКИ БАЗЫ ДАННЫХ
# ==============================================

# По умолчанию используется SQLite
# Для production рекомендуется PostgreSQL:
# DATABASE_URL = 'postgresql://user:password@localhost:5432/notification_system'

# ==============================================
# НАСТРОЙКИ ЛОГИРОВАНИЯ
# ==============================================

# Уровень логирования
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Путь к лог файлам
LOG_DIR = 'logs'

# ==============================================
# НАСТРОЙКИ УВЕДОМЛЕНИЙ
# ==============================================

# Максимальное количество попыток отправки
MAX_RETRY_ATTEMPTS = 3

# Тайм-аут для API запросов (секунды)
API_TIMEOUT = 30

# Размер батча для массовой отправки
BATCH_SIZE = 100
