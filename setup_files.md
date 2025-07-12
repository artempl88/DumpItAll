# Настройка универсального автоматического резервного копирования

## 🔍 Возможности скрипта

Скрипт **автоматически обнаруживает и создает резервные копии** всех баз данных на VPS:

### Поддерживаемые СУБД:
- **PostgreSQL** (системные и Docker)
- **MySQL/MariaDB** (системные и Docker) 
- **MongoDB** (системные и Docker)
- **Redis** (системные и Docker)
- **SQLite** (файлы по всей системе)

### Источники обнаружения:
- 🖥️ **Системные процессы** - сканирует запущенные службы СУБД
- 🐳 **Docker контейнеры** - анализирует все контейнеры с БД
- 📁 **SQLite файлы** - ищет .db, .sqlite, .sqlite3 файлы

## 1. Установка зависимостей

```bash
pip install -r requirements.txt

# Дополнительные системные пакеты
sudo apt-get update
sudo apt-get install postgresql-client mysql-client mongodb-clients redis-tools
```

## 2. Настройка прав доступа

```bash
# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перезагрузка сессии или перелогин
newgrp docker

# Проверка доступа к Docker
docker ps
```

## 3. Создание .env файла

```env
# Настройки Google Drive
DRIVE_FOLDER_ID=your_drive_folder_id

# Настройки резервного копирования  
BACKUP_DIR=./backups
```

## 4. Настройка Google Drive API

### Service Account (рекомендуется)

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект и включите Google Drive API
3. Создайте Service Account:
   - "APIs & Services" > "Credentials"
   - "Create Credentials" > "Service Account"
4. Создайте JSON ключ и сохраните как `service-account-key.json`
5. Поделитесь папкой на Drive с email Service Account

## 5. Запуск обнаружения (тест)

```bash
# Тестовый запуск для проверки обнаружения
python3 backup_script.py
```

Скрипт создаст отчет `discovery_report_YYYYMMDD_HHMMSS.json` со всеми найденными БД.

## 6. Что обнаруживает скрипт

### Системные процессы
- Сканирует `ps aux` на наличие процессов БД
- Определяет порты через анализ сетевых соединений  
- Извлекает пути к данным из командной строки процессов

### Docker контейнеры
- Анализирует все запущенные контейнеры
- Определяет тип БД по образу (postgres, mysql, mongo и т.д.)
- Извлекает учетные данные из переменных окружения
- Получает список баз данных внутри контейнеров

### SQLite файлы
- Рекурсивный поиск в системных директориях
- Проверка заголовков файлов на соответствие SQLite
- Исключение временных и системных файлов

## 7. Примеры обнаруженных конфигураций

### PostgreSQL в Docker
```json
{
  "type": "postgresql",
  "source": "docker", 
  "container_name": "postgres_db",
  "credentials": {
    "user": "postgres",
    "password": "secret",
    "database": "myapp"
  },
  "databases": ["myapp", "analytics"]
}
```

### Системный MySQL
```json
{
  "type": "mysql",
  "source": "system",
  "host": "localhost",
  "port": 3306,
  "databases": ["wordpress", "ecommerce"]
}
```

## 8. Настройка автоматического запуска

### Systemd сервис
```bash
sudo cp db-backup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable db-backup.service
sudo systemctl start db-backup.service
```

### Проверка статуса
```bash
sudo systemctl status db-backup.service
journalctl -u db-backup.service -f
```

## 9. Мониторинг и логи

```bash
# Просмотр логов
tail -f backup.log

# Проверка последнего отчета обнаружения
cat backups/discovery_report_*.json | jq .

# Проверка созданных резервных копий
ls -la backups/
```

## 10. Безопасность и настройки

### Доступ к базам данных
Скрипт пытается подключиться к БД несколькими способами:
- Без аутентификации (для локальных соединений)
- С учетными данными из Docker переменных окружения
- С стандартными учетными данными (postgres/postgres, root без пароля)

### Настройка доступа для системных БД

**PostgreSQL:**
```bash
# В pg_hba.conf добавить:
local   all   postgres   trust
host    all   postgres   127.0.0.1/32   trust
```

**MySQL:**
```bash
# Создать пользователя для резервного копирования
CREATE USER 'backup'@'localhost' IDENTIFIED BY 'password';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup'@'localhost';
```

## 11. Исключения и фильтры

### Исключаемые базы данных:
- **PostgreSQL**: template0, template1
- **MySQL**: information_schema, performance_schema, mysql, sys  
- **MongoDB**: admin, local, config

### Исключаемые SQLite файлы:
- Временные файлы (-wal, -shm)
- Системные кэши браузеров
- Файлы меньше 1KB

## 12. Устранение неполадок

### Ошибки подключения к БД
```bash
# Проверка доступности портов
netstat -tulpn | grep -E "(5432|3306|27017|6379)"

# Проверка Docker контейнеров
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
```

### Ошибки Docker API
```bash
# Проверка прав доступа
groups $USER | grep docker

# Проверка Docker daemon
sudo systemctl status docker
```

### Проблемы с Google Drive
```bash
# Проверка ключей
ls -la service-account-key.json
cat service-account-key.json | jq .client_email
```

## 13. Расширенная конфигурация

### Настройка поиска SQLite
```python
# В коде можно изменить пути поиска:
search_paths = [
    '/var/lib',
    '/opt', 
    '/home',
    '/custom/path'  # Добавить свой путь
]
```

### Настройка интервала резервного копирования
```python
# Изменить в main():
schedule.every(15).minutes.do(backup_manager.run_full_backup)  # Каждые 15 минут
schedule.every().hour.do(backup_manager.run_full_backup)       # Каждый час
schedule.every().day.at("02:00").do(backup_manager.run_full_backup)  # Ежедневно в 2:00
```

## 14. Производительность

- **Параллельное выполнение**: Каждая БД обрабатывается последовательно
- **Сжатие**: PostgreSQL использует custom формат (сжатый)
- **Очистка**: Автоматическое удаление файлов старше 7 дней
- **Ресурсы**: Мониторинг использования CPU/памяти через psutil

Скрипт создает полностью автономную систему резервного копирования всех баз данных на сервере!
