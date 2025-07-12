# DumpItAll
![DumpItAll Logo](logo.png)
**🗄️ Dump It All - Автоматическое обнаружение и резервное копирование всех баз данных на VPS**

DumpItAll - это универсальная система резервного копирования, которая автоматически находит и создает дампы всех баз данных на сервере: системных, в Docker контейнерах и SQLite файлов. Поддерживает автоматическую загрузку на Google Drive и работает без ручной настройки.

## ✨ Основные возможности

- **🔍 Автоматическое обнаружение** - сканирует порты, процессы и Docker контейнеры
- **🌐 Сканирование портов** - находит БД по стандартным и нестандартным портам
- **🐳 Docker интеграция** - автоматически обнаруживает контейнеры с БД
- **📁 SQLite поиск** - рекурсивно находит SQLite файлы в системе
- **☁️ Google Drive** - автоматическая загрузка резервных копий в облако
- **⏰ Планировщик** - настраиваемые интервалы резервного копирования
- **📊 Отчетность** - детальные отчеты и статистика
- **🔧 CLI интерфейс** - гибкое управление через командную строку

## 🗄️ Поддерживаемые СУБД

| СУБД | Системные | Docker | Автообнаружение | Резервное копирование |
|------|-----------|--------|-----------------|---------------------|
| **PostgreSQL** | ✅ | ✅ | ✅ | `pg_dump` |
| **MySQL/MariaDB** | ✅ | ✅ | ✅ | `mysqldump` |
| **MongoDB** | ✅ | ✅ | ✅ | `mongodump` |
| **Redis** | ✅ | ✅ | ✅ | `BGSAVE + RDB` |
| **SQLite** | ✅ | - | ✅ | Копирование файлов |
| **Elasticsearch** | ✅ | ✅ | ✅ | REST API |
| **CouchDB** | ✅ | ✅ | ✅ | REST API |
| **Oracle** | ✅ | ✅ | ✅ | Базовое обнаружение |
| **SQL Server** | ✅ | ✅ | ✅ | Базовое обнаружение |

# 🔐 Расширенное автоматическое обнаружение учетных данных

## Обзор функциональности

DumpItAll теперь автоматически сканирует весь VPS для поиска учетных данных баз данных из различных конфигурационных файлов. Это позволяет создавать резервные копии запароленных БД без ручной настройки.

## 🔍 Что сканируется

### Директории поиска:
- `/home/*` - домашние директории пользователей
- `/var/www/*` - веб-приложения
- `/opt/*` - установленные приложения
- `/etc/*` - системные конфигурации
- `/usr/local/*` - локальные приложения
- `/srv/*` - сервисы
- `/app/*` - Docker приложения
- `/data/*` - данные приложений

### Типы файлов:
- **Env файлы**: `.env`, `.env.local`, `.env.production`, `*.env`
- **Docker**: `docker-compose.yml`, `docker-compose.yaml`
- **YAML конфиги**: `config.yml`, `database.yml`
- **PHP**: `wp-config.php`, `configuration.php`
- **Python**: `settings.py`
- **INI/CFG**: `*.ini`, `*.cfg`, `*.conf`

## 📋 Поддерживаемые паттерны

### PostgreSQL
```env
POSTGRES_PASSWORD=your_password
PGPASSWORD=your_password
DB_PASSWORD=your_password
DATABASE_PASSWORD=your_password
PG_PASSWORD=your_password
POSTGRESQL_PASSWORD=your_password

POSTGRES_USER=postgres
PGUSER=postgres
DB_USER=postgres
DATABASE_USER=postgres
```

### MySQL/MariaDB
```env
MYSQL_PASSWORD=your_password
MYSQL_ROOT_PASSWORD=your_password
MARIADB_PASSWORD=your_password
DB_PASSWORD=your_password

MYSQL_USER=root
MYSQL_ROOT_USER=root
MARIADB_USER=root
```

### MongoDB
```env
MONGO_PASSWORD=your_password
MONGODB_PASSWORD=your_password
MONGO_INITDB_ROOT_PASSWORD=your_password

MONGO_USER=admin
MONGODB_USER=admin
MONGO_INITDB_ROOT_USERNAME=admin
```

### Redis
```env
REDIS_PASSWORD=your_password
REDIS_AUTH=your_password
CACHE_PASSWORD=your_password
```

## 🔗 Connection Strings

Поддерживается автоматический парсинг connection strings:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/database
DB_URL=mysql://root:password@localhost:3306/myapp
MONGO_URL=mongodb://admin:password@localhost:27017/app
```

## 📁 Парсинг специфичных файлов

### docker-compose.yml
```yaml
services:
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: secret_password
      POSTGRES_USER: myuser
      POSTGRES_DB: mydb
```

### wp-config.php
```php
define('DB_PASSWORD', 'wordpress_password');
define('DB_USER', 'wordpress_user');
define('DB_HOST', 'localhost');
define('DB_NAME', 'wordpress');
```

### Django settings.py
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myproject',
        'USER': 'myuser',
        'PASSWORD': 'mypassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### config.ini
```ini
[database]
host = localhost
port = 5432
user = dbuser
password = dbpassword
database = myapp
```

## 🚀 Использование

### Просмотр найденных учетных данных
```bash
# При сканировании автоматически отображаются найденные учетные данные
python3 backup_script.py --scan-only --log-level DEBUG
```

### Пример вывода
```
🔐 Этап 0: Автоматическое обнаружение учетных данных
🔍 Поиск конфигурационных файлов по всему VPS...
📄 Найдено 15 конфигурационных файлов
✅ Найдены учетные данные:
  🔑 POSTGRESQL: user: postgres, password: ********
  🔑 MYSQL: user: root, password: ********
  🔑 MONGODB: user: admin, password: ********
  🔑 REDIS: password: ********
```

## 🔒 Безопасность

### Защита паролей
- Пароли никогда не выводятся в логи в открытом виде
- Используются звездочки для маскировки паролей
- Детальная информация доступна только в режиме DEBUG

### Рекомендации
1. **Ограничьте права доступа** к конфигурационным файлам:
   ```bash
   chmod 600 .env
   chmod 600 wp-config.php
   ```

2. **Используйте отдельного пользователя** для резервного копирования:
   ```bash
   sudo useradd -r -s /bin/bash backup
   sudo -u backup python3 backup_script.py
   ```

3. **Регулярно ротируйте пароли** и обновляйте их в конфигурационных файлах

## 🛠️ Отладка

### Проверка обнаружения учетных данных
```bash
# Детальный лог процесса обнаружения
python3 backup_script.py --scan-only --log-level DEBUG 2>&1 | grep -E "(Найден|Парсинг)"
```

### Тестирование подключений
```bash
# Проверка, что найденные учетные данные работают
python3 backup_script.py --test-connections
```

### Ручная проверка файла
```bash
# Проверка, что файл читается корректно
python3 -c "
import os
with open('.env', 'r', encoding='utf-8-sig') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            print(line.strip())
"
```

## ⚡ Производительность

### Оптимизация поиска
- Поиск выполняется только при запуске сканирования
- Результаты кешируются на время выполнения
- Игнорируются бинарные файлы и большие файлы

### Ограничения
- Максимальный размер сканируемого файла: 1MB
- Максимальная глубина поиска: 3 уровня от корневой директории
- Тайм-аут на парсинг одного файла: 5 секунд

## 📝 Примеры конфигураций

### Laravel .env
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=laravel
DB_USERNAME=root
DB_PASSWORD=secret
```

### Symfony .env
```env
DATABASE_URL="postgresql://db_user:db_password@127.0.0.1:5432/db_name?serverVersion=13&charset=utf8"
```

### Node.js .env
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nodeuser
POSTGRES_PASSWORD=nodepass
POSTGRES_DATABASE=nodeapp
```

## 🔄 Приоритет использования учетных данных

1. **Автоматически найденные** из конфигурационных файлов
2. **Переменные окружения** текущей сессии
3. **Значения по умолчанию** (postgres/postgres, root без пароля)
4. **Попытка без пароля** (для локальных trust соединений)

## 🎯 Лучшие практики

1. **Стандартизируйте названия переменных** для лучшего обнаружения
2. **Используйте .env файлы** вместо хардкода в коде
3. **Группируйте конфигурации БД** в одном месте
4. **Документируйте** нестандартные переменные в README

Эта функциональность делает DumpItAll полностью автоматическим решением для резервного копирования всех БД на сервере!

## 🚀 Быстрый старт

### 1. Установка
```bash
git clone https://github.com/artempl88/DumpItAll.git
cd DumpItAll
pip install -r requirements.txt
```

### 2. Первое сканирование
```bash
# Обнаружение всех БД в системе
python3 backup_script.py --scan-only
```

### 3. Проверка подключений
```bash
# Тестирование доступа к найденным БД
python3 backup_script.py --test-connections
```

### 4. Настройка Google Drive
```bash
# Создание конфигурации
echo "DRIVE_FOLDER_ID=your_folder_id" > .env
echo "BACKUP_DIR=./backups" >> .env

# Размещение Service Account ключа
# Поместите service-account-key.json в директорию проекта
```

### 5. Запуск резервного копирования
```bash
# Однократное резервное копирование
python3 backup_script.py --backup-once

# Автоматический режим (каждые 30 минут)
python3 backup_script.py --daemon
```

## 📦 Установка

### Системные требования
- Python 3.7+
- Linux/macOS/Windows
- Docker (опционально)
- Клиенты БД: `postgresql-client`, `mysql-client`, `mongodb-clients`, `redis-tools`

### Автоматическая установка
```bash
curl -sSL https://raw.githubusercontent.com/artempl88/DumpItAll/main/install.sh | sudo bash
```

### Ручная установка
```bash
# 1. Клонирование репозитория
git clone https://github.com/artempl88/DumpItAll.git
cd DumpItAll

# 2. Установка Python зависимостей
pip install -r requirements.txt

# 3. Установка клиентов БД (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y postgresql-client mysql-client mongodb-clients redis-tools

# 4. Настройка Docker доступа
sudo usermod -aG docker $USER
newgrp docker

# 5. Настройка прав доступа к БД
sudo bash setup_database_access.sh
```

## ⚙️ Настройка

### Файл конфигурации `.env`
```env
# Google Drive настройки
DRIVE_FOLDER_ID=1ABC123DEF456GHI789JKL

# Директории
BACKUP_DIR=./backups

# Логирование  
LOG_LEVEL=INFO

# Пароли для доступа к базам данных
# PostgreSQL
PGPASSWORD=your_postgres_password
# или
POSTGRES_PASSWORD=your_postgres_password

# MySQL/MariaDB
MYSQL_PASSWORD=your_mysql_password
MYSQL_ROOT_PASSWORD=your_mysql_root_password

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=your_mongo_password

# Redis
REDIS_PASSWORD=your_redis_password
```

### Настройка паролей БД

DumpItAll поддерживает работу с паролями через переменные окружения:

1. **Создайте файл конфигурации**:
   ```bash
   cp env.example .env
   ```

2. **Укажите пароли в файле `.env`**:
   - **PostgreSQL**: `PGPASSWORD` или `POSTGRES_PASSWORD`
   - **MySQL/MariaDB**: `MYSQL_PASSWORD` или `MYSQL_ROOT_PASSWORD`
   - **MongoDB**: `MONGO_USER` и `MONGO_PASSWORD`
   - **Redis**: `REDIS_PASSWORD`

3. **Ограничьте права доступа**:
   ```bash
   chmod 600 .env
   ```

> **Примечание**: Если пароли не заданы, приложение попытается подключиться без аутентификации. Это может работать для локальных инсталляций БД с отключенной аутентификацией.

### Google Drive API
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект и включите Google Drive API
3. Создайте Service Account в разделе "Credentials"
4. Скачайте JSON ключ и сохраните как `service-account-key.json`
5. Поделитесь папкой на Google Drive с email Service Account
6. Скопируйте ID папки из URL и добавьте в `.env`

### Systemd сервис (Production)
```bash
# Копирование в production директорию
sudo mkdir -p /opt/db-backup
sudo cp -r . /opt/db-backup/
sudo chown -R backup:backup /opt/db-backup

# Установка и запуск сервиса
sudo cp db-backup.service /etc/systemd/system/
sudo systemctl enable db-backup.service
sudo systemctl start db-backup.service
```

## 🖥️ Использование

### CLI команды

#### Обнаружение БД
```bash
# Сканирование всех БД
python3 backup_script.py --scan-only

# Детальное сканирование с отладкой
python3 backup_script.py --scan-only --log-level DEBUG

# Проверка подключений
python3 backup_script.py --test-connections
```

#### Резервное копирование
```bash
# Однократное резервное копирование
python3 backup_script.py --backup-once

# Демон с планировщиком (по умолчанию каждые 30 минут)
python3 backup_script.py --daemon

# Кастомный интервал (каждые 15 минут)
python3 backup_script.py --daemon --interval 15

# Ежечасное резервное копирование
python3 backup_script.py --daemon --interval 60
```

#### Конфигурация
```bash
# Кастомный файл конфигурации
python3 backup_script.py --config /path/to/custom.env --daemon

# Различные уровни логирования
python3 backup_script.py --scan-only --log-level WARNING
python3 backup_script.py --daemon --log-level DEBUG
```

### Полный список аргументов
```
--scan-only              Только сканирование БД без резервного копирования
--test-connections       Тестирование подключений к обнаруженным БД
--backup-once           Однократное резервное копирование
--daemon                Запуск демона с планировщиком (по умолчанию)
--interval N            Интервал резервного копирования в минутах (по умолчанию: 30)
--config PATH           Путь к файлу конфигурации (по умолчанию: .env)
--log-level LEVEL       Уровень логирования: DEBUG, INFO, WARNING, ERROR
```

## 📊 Отчеты и мониторинг

### Генерируемые файлы
- `discovery_report_YYYYMMDD_HHMMSS.json` - отчет обнаружения БД
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

# Статус systemd сервиса
sudo systemctl status db-backup.service
journalctl -u db-backup.service -f
```

### Пример отчета обнаружения
```json
{
  "type": "postgresql",
  "source": "network_scan",
  "host": "localhost",
  "port": 5432,
  "databases": ["myapp", "analytics", "logs"],
  "connection_tested": true,
  "auth_method": "trust"
}
```

## 🔧 Примеры использования

### Проверка новой системы
```bash
# Быстрая проверка
python3 backup_script.py --scan-only

# Детальная диагностика
python3 backup_script.py --scan-only --log-level DEBUG > scan_report.log 2>&1

# Проверка подключений
python3 backup_script.py --test-connections
```

### Настройка production среды
```bash
# 1. Обнаружение БД
python3 backup_script.py --scan-only --config /opt/db-backup/.env

# 2. Тестирование подключений
python3 backup_script.py --test-connections --config /opt/db-backup/.env

# 3. Пробное резервное копирование
python3 backup_script.py --backup-once --config /opt/db-backup/.env

# 4. Запуск production демона
systemctl start db-backup.service
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

## 🔍 Как работает обнаружение

### Этап 1: Сканирование портов
- Получение всех открытых портов через `psutil`
- Приоритетная проверка стандартных портов БД
- Определение типа БД по баннерам и откликам
- Тестирование подключений без аутентификации

### Этап 2: Анализ процессов
- Поиск процессов БД в списке запущенных процессов
- Извлечение параметров из командной строки
- Определение директорий данных и конфигураций

### Этап 3: Docker контейнеры
- Сканирование всех запущенных контейнеров
- Анализ образов Docker на наличие БД
- Извлечение переменных окружения с паролями
- Выполнение команд внутри контейнеров

### Этап 4: SQLite файлы
- Рекурсивный поиск в системных директориях
- Проверка заголовков файлов на соответствие SQLite
- Фильтрация временных и системных файлов

## 🛠️ Устранение неполадок

### БД не обнаруживается
```bash
# Проверка открытых портов
netstat -tulpn | grep -E "(5432|3306|27017|6379)"

# Проверка процессов БД
ps aux | grep -E "(postgres|mysql|mongo|redis)"

# Проверка Docker контейнеров
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
```

### Ошибки подключения
```bash
# Проверка доступности портов
telnet localhost 5432

# Проверка аутентификации PostgreSQL
sudo -u postgres psql -c "\l"

# Проверка MySQL
mysql -u root -e "SHOW DATABASES;"
```

### Docker недоступен
```bash
# Проверка статуса Docker
sudo systemctl status docker

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка доступа
docker ps
```

### Google Drive API
```bash
# Проверка ключей
ls -la service-account-key.json
cat service-account-key.json | jq .client_email

# Проверка прав доступа к папке
# Убедитесь, что папка поделена с email Service Account
```

### Systemd сервис
```bash
# Проверка статуса
sudo systemctl status db-backup.service

# Просмотр логов
journalctl -u db-backup.service -f

# Перезапуск сервиса
sudo systemctl restart db-backup.service
```

## 📁 Структура проекта

```
DumpItAll/
├── backup_script.py              # Основной скрипт
├── requirements.txt               # Python зависимости
├── .env.example                  # Пример конфигурации
├── service-account-key.json      # Google Drive ключи (не в git)
├── db-backup.service             # Systemd сервис
├── setup_database_access.sh      # Скрипт настройки БД
├── install.sh                    # Автоматический инсталлер
├── backups/                      # Директория резервных копий
│   ├── discovery_report_*.json   # Отчеты обнаружения
│   └── backup_statistics.json    # Статистика
└── README.md                     # Документация
```

## 🔐 Безопасность

### Рекомендации
- Ограничьте права доступа к файлам конфигурации: `chmod 600 .env service-account-key.json`
- Используйте отдельного пользователя `backup` для резервного копирования
- Регулярно ротируйте пароли и ключи Service Account
- Мониторьте логи на предмет подозрительной активности

### Права доступа к БД
```bash
# PostgreSQL - создание пользователя только для чтения
sudo -u postgres psql -c "
CREATE USER backup_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE template1 TO backup_user;
"

# MySQL - ограниченные права
mysql -u root -e "
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, LOCK TABLES, SHOW VIEW ON *.* TO 'backup_user'@'localhost';
"
```

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! 

### Как внести вклад
1. Форкните репозиторий
2. Создайте ветку для новой функции: `git checkout -b feature/amazing-feature`
3. Внесите изменения и добавьте тесты
4. Зафиксируйте изменения: `git commit -m 'Add amazing feature'`
5. Отправьте в ветку: `git push origin feature/amazing-feature`
6. Создайте Pull Request

### Области для улучшений
- Поддержка новых СУБД
- Улучшение алгоритмов обнаружения
- Дополнительные методы аутентификации
- Интеграция с другими облачными сервисами
- Web интерфейс для управления

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## 🙏 Благодарности

- [psutil](https://github.com/giampaolo/psutil) - системная информация
- [docker-py](https://github.com/docker/docker-py) - Docker API
- [google-api-python-client](https://github.com/googleapis/google-api-python-client) - Google Drive API
- [schedule](https://github.com/dbader/schedule) - планировщик задач

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/artempl88/DumpItAll/issues)
- **Discussions**: [GitHub Discussions](https://github.com/artempl88/DumpItAll/discussions)
- **Email**: notpunksdev@gmail.com

---

**⭐ Если DumpItAll оказался полезным, поставьте звездочку на GitHub!**
