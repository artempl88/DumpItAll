# 🖥️ CLI Интерфейс универсальной системы резервного копирования

## Основные команды

### 🔍 Сканирование и обнаружение БД
```bash
# Только сканирование портов и обнаружение БД (без резервного копирования)
python3 backup_script.py --scan-only

# Сканирование с отладочными сообщениями
python3 backup_script.py --scan-only --log-level DEBUG
```

### 🔐 Настройка автоматической аутентификации
```bash
# Создание файлов аутентификации для всех БД
python3 backup_script.py --setup-auth

# Настройка с кастомным файлом конфигурации
python3 backup_script.py --setup-auth --config /path/to/custom.env
```

### 🧪 Тестирование подключений
```bash
# Проверка подключений ко всем обнаруженным БД
python3 backup_script.py --test-connections

# Тестирование с подробными логами
python3 backup_script.py --test-connections --log-level DEBUG
```

### 💾 Резервное копирование
```bash
# Однократное резервное копирование
python3 backup_script.py --backup-once

# Запуск демона с резервным копированием каждые 30 минут (по умолчанию)
python3 backup_script.py --daemon

# Демон с кастомным интервалом (каждые 15 минут)
python3 backup_script.py --daemon --interval 15

# Демон с ежечасным резервным копированием
python3 backup_script.py --daemon --interval 60
```

### ⚙️ Настройка конфигурации
```bash
# Использование кастомного файла конфигурации
python3 backup_script.py --config /path/to/custom.env --backup-once

# Запуск с разными уровнями логирования
python3 backup_script.py --scan-only --log-level WARNING
python3 backup_script.py --daemon --log-level INFO
```

## 📊 Примеры использования

### Первичная настройка и проверка
```bash
# 1. Настройка автоматической аутентификации
python3 backup_script.py --setup-auth

# 2. Сканирование системы
python3 backup_script.py --scan-only

# 3. Проверка подключений
python3 backup_script.py --test-connections

# 4. Тестовое резервное копирование
python3 backup_script.py --backup-once
```

### Полная автоматическая настройка
```bash
# Создать .env файл с паролями
cat > .env << EOF
POSTGRES_PASSWORD=mypostgrespass
MYSQL_ROOT_PASSWORD=mymysqlpass
MONGO_PASSWORD=mymongopass
REDIS_PASSWORD=myredispass
EOF

# Настроить автоматическую аутентификацию
python3 backup_script.py --setup-auth

# Запустить демон
python3 backup_script.py --daemon
```

### Отладка проблем
```bash
# Подробные логи сканирования
python3 backup_script.py --scan-only --log-level DEBUG

# Отладка подключений к БД
python3 backup_script.py --test-connections --log-level DEBUG
```

### Production запуск
```bash
# Запуск через systemd (рекомендуется)
sudo systemctl start db-backup.service

# Или прямой запуск демона
nohup python3 backup_script.py --daemon --interval 30 > /dev/null 2>&1 &
```

## 📋 Аргументы командной строки

| Аргумент | Описание | По умолчанию |
|----------|----------|--------------|
| `--scan-only` | Только сканирование БД | - |
| `--test-connections` | Тестирование подключений | - |
| `--backup-once` | Однократное резервное копирование | - |
| `--setup-auth` | Настройка файлов автоматической аутентификации | - |
| `--daemon` | Запуск демона с планировщиком | ✅ (по умолчанию) |
| `--interval N` | Интервал в минутах | 30 |
| `--config PATH` | Путь к файлу конфигурации | .env |
| `--log-level LEVEL` | Уровень логирования | INFO |

## 🔐 Автоматическая аутентификация

### Что создает команда --setup-auth:

1. **~/.pgpass** - файл паролей PostgreSQL
2. **~/.my.cnf** - конфигурация MySQL клиента
3. **~/.mongorc.js** - скрипт автоаутентификации MongoDB
4. **~/.rediscli_auth** - файл пароля Redis

### Пример использования:
```bash
# Создание всех файлов аутентификации
python3 backup_script.py --setup-auth

# После настройки можно подключаться без ввода пароля:
psql -l                    # PostgreSQL
mysql -e "SHOW DATABASES;" # MySQL
mongo --eval "db.version()" # MongoDB
redis-cli ping             # Redis
```

## 🔍 Что происходит при сканировании

### Этап 0: Автоматическое обнаружение учетных данных 🔐
- Поиск всех .env файлов на VPS
- Парсинг docker-compose.yml файлов
- Извлечение паролей из конфигураций приложений
- Анализ wp-config.php, settings.py и других конфигов

### Этап 1: Сканирование портов 🌐
- Проверка всех открытых портов
- Приоритетная проверка стандартных портов БД (5432, 3306, 27017, 6379...)
- Определение типа БД по баннерам и откликам

### Этап 2: Анализ процессов 🖥️
- Поиск процессов БД через `psutil`
- Извлечение параметров из командной строки
- Определение директорий данных

### Этап 3: Docker контейнеры 🐳
- Сканирование всех запущенных контейнеров
- Анализ образов Docker на наличие БД
- Извлечение переменных окружения

### Этап 4: SQLite файлы 📁
- Рекурсивный поиск в системных директориях
- Проверка заголовков файлов
- Определение размеров и доступности

## 📈 Отчеты и логи

### Файлы отчетов
- `discovery_report_YYYYMMDD_HHMMSS.json` - детальный отчет обнаружения
- `backup_statistics.json` - статистика резервного копирования
- `backup.log` - основной лог файл

### Просмотр отчетов
```bash
# Последний отчет обнаружения
cat backups/discovery_report_*.json | tail -n 1 | jq .

# Статистика резервного копирования
cat backups/backup_statistics.json | jq '.[-1]'

# Мониторинг логов в реальном времени
tail -f backup.log
```

## 🚨 Типичные сценарии использования

### Проверка новой системы
```bash
# Быстрая проверка что обнаруживается
python3 backup_script.py --scan-only --log-level INFO

# Детальная диагностика
python3 backup_script.py --scan-only --log-level DEBUG > scan_report.log 2>&1
```

### Настройка production среды
```bash
# 1. Создание конфигурации
cp env.example /opt/db-backup/.env
# Отредактировать файл и добавить пароли

# 2. Настройка аутентификации
python3 backup_script.py --setup-auth --config /opt/db-backup/.env

# 3. Проверка конфигурации
python3 backup_script.py --scan-only --config /opt/db-backup/.env

# 4. Тест подключений
python3 backup_script.py --test-connections --config /opt/db-backup/.env

# 5. Пробное резервное копирование
python3 backup_script.py --backup-once --config /opt/db-backup/.env

# 6. Запуск демона
python3 backup_script.py --daemon --config /opt/db-backup/.env
```

### Отладка проблем
```bash
# Проблемы с подключением к БД
python3 backup_script.py --test-connections --log-level DEBUG

# Проблемы с Docker
docker ps && python3 backup_script.py --scan-only --log-level DEBUG

# Проблемы с Google Drive
python3 backup_script.py --backup-once --log-level DEBUG
```

## ⚡ Быстрые команды

```bash
# Полная диагностика системы
python3 backup_script.py --scan-only && python3 backup_script.py --test-connections

# Быстрая настройка и запуск
python3 backup_script.py --setup-auth && python3 backup_script.py --backup-once

# Немедленное резервное копирование всех БД
python3 backup_script.py --backup-once --log-level INFO

# Запуск с высокой частотой для тестирования
python3 backup_script.py --daemon --interval 5 --log-level DEBUG
```

## 🔐 Советы по безопасности

1. **Ограничьте права доступа к .env файлу**:
   ```bash
   chmod 600 .env
   ```

2. **Используйте отдельного пользователя для резервного копирования**:
   ```bash
   sudo useradd -r -s /bin/bash backup
   sudo chown -R backup:backup /opt/db-backup
   sudo -u backup python3 backup_script.py --daemon
   ```

3. **Регулярно проверяйте права доступа к файлам аутентификации**:
   ```bash
   ls -la ~/.pgpass ~/.my.cnf ~/.mongorc.js ~/.rediscli_auth
   ```

4. **Ротируйте пароли и обновляйте конфигурацию**:
   ```bash
   # Обновить .env файл с новыми паролями
   vim .env
   
   # Пересоздать файлы аутентификации
   python3 backup_script.py --setup-auth
   ```