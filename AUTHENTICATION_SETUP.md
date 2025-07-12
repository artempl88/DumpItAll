# Настройка автоматической аутентификации для запароленных БД

DumpItAll поддерживает автоматическую аутентификацию для запароленных баз данных без необходимости интерактивного ввода пароля.

## 🔐 Быстрая настройка

### 1. Создайте файл с паролями

```bash
# Создайте файл .env с паролями
cp env.example .env

# Отредактируйте файл и укажите ваши пароли
nano .env
```

**Пример файла .env:**
```env
# PostgreSQL
PGPASSWORD=your_postgres_password

# MySQL
MYSQL_ROOT_PASSWORD=your_mysql_password

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=your_mongo_password

# Redis
REDIS_PASSWORD=your_redis_password
```

### 2. Запустите настройку аутентификации

```bash
# Автоматически создаст файлы аутентификации
python backup_script.py --setup-auth
```

### 3. Проверьте настройки

```bash
# Протестируйте подключения
python backup_script.py --test-connections

# Запустите резервное копирование
python backup_script.py --backup-once
```

## 📋 Что создается автоматически

### PostgreSQL - файл `.pgpass`
```
# Местоположение: ~/.pgpass
# Формат: hostname:port:database:username:password
localhost:5432:*:postgres:your_password
127.0.0.1:5432:*:postgres:your_password
*:5432:*:postgres:your_password
```

### MySQL - файл `.my.cnf`
```
# Местоположение: ~/.my.cnf
[client]
user=root
password=your_password
host=localhost
port=3306

[mysql]
user=root
password=your_password

[mysqldump]
user=root
password=your_password
```

### MongoDB - файл `.mongorc.js`
```javascript
// Местоположение: ~/.mongorc.js
var mongoUser = 'admin';
var mongoPassword = 'your_password';
var mongoHost = 'localhost';
var mongoPort = 27017;

function autoAuth() {
    try {
        db = db.getSiblingDB('admin');
        db.auth(mongoUser, mongoPassword);
        print('✅ MongoDB аутентификация успешна');
    } catch (e) {
        print('⚠️ MongoDB аутентификация не удалась: ' + e);
    }
}
```

### Redis - файл `.rediscli_auth`
```
# Местоположение: ~/.rediscli_auth
your_redis_password
```

## 🔒 Безопасность

Все файлы аутентификации автоматически получают права доступа `600` (только для владельца):

```bash
# Проверка прав доступа
ls -la ~/.pgpass ~/.my.cnf ~/.mongorc.js ~/.rediscli_auth

# Результат должен быть:
# -rw------- 1 user user ... ~/.pgpass
# -rw------- 1 user user ... ~/.my.cnf
# -rw------- 1 user user ... ~/.mongorc.js
# -rw------- 1 user user ... ~/.rediscli_auth
```

## 🚀 Использование

После настройки можно запускать резервное копирование без ввода паролей:

```bash
# Сканирование БД (включая запароленные)
python backup_script.py --scan-only

# Тестирование подключений
python backup_script.py --test-connections

# Резервное копирование
python backup_script.py --backup-once

# Демон режим
python backup_script.py --daemon
```

## 🛠️ Ручная настройка

### PostgreSQL
```bash
# Создание .pgpass файла вручную
echo "localhost:5432:*:postgres:your_password" > ~/.pgpass
chmod 600 ~/.pgpass

# Проверка
psql -h localhost -U postgres -l
```

### MySQL
```bash
# Создание .my.cnf файла вручную
cat > ~/.my.cnf << EOF
[client]
user=root
password=your_password
EOF
chmod 600 ~/.my.cnf

# Проверка
mysql -e "SHOW DATABASES;"
```

### MongoDB
```bash
# Создание .mongorc.js файла вручную
cat > ~/.mongorc.js << 'EOF'
var mongoUser = 'admin';
var mongoPassword = 'your_password';
function autoAuth() {
    try {
        db = db.getSiblingDB('admin');
        db.auth(mongoUser, mongoPassword);
        print('✅ MongoDB аутентификация успешна');
    } catch (e) {
        print('⚠️ MongoDB аутентификация не удалась: ' + e);
    }
}
EOF
chmod 600 ~/.mongorc.js

# Проверка
mongo --eval "db.version()"
```

### Redis
```bash
# Создание .rediscli_auth файла вручную
echo "your_redis_password" > ~/.rediscli_auth
chmod 600 ~/.rediscli_auth

# Проверка
redis-cli ping
```

## 🔧 Устранение проблем

### PostgreSQL не подключается
```bash
# Проверьте права доступа
ls -la ~/.pgpass

# Проверьте формат файла
cat ~/.pgpass

# Проверьте подключение
psql -h localhost -U postgres -l
```

### MySQL не подключается
```bash
# Проверьте права доступа
ls -la ~/.my.cnf

# Проверьте формат файла
cat ~/.my.cnf

# Проверьте подключение
mysql -e "SELECT VERSION();"
```

### MongoDB не подключается
```bash
# Проверьте права доступа
ls -la ~/.mongorc.js

# Проверьте подключение
mongo --eval "db.version()"
```

### Redis не подключается
```bash
# Проверьте права доступа
ls -la ~/.rediscli_auth

# Проверьте подключение
redis-cli ping
```

## 📝 Переменные окружения

Поддерживаемые переменные окружения:

| База данных | Переменные |
|-------------|------------|
| PostgreSQL  | `PGPASSWORD`, `POSTGRES_PASSWORD` |
| MySQL       | `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` |
| MongoDB     | `MONGO_USER`, `MONGO_PASSWORD` |
| Redis       | `REDIS_PASSWORD` |

## 🎯 Примеры использования

### Настройка для production сервера
```bash
# 1. Создайте .env файл
sudo tee /opt/db-backup/.env << EOF
PGPASSWORD=prod_pg_password
MYSQL_ROOT_PASSWORD=prod_mysql_password
MONGO_USER=backup_user
MONGO_PASSWORD=prod_mongo_password
REDIS_PASSWORD=prod_redis_password
EOF

# 2. Установите права доступа
sudo chmod 600 /opt/db-backup/.env

# 3. Настройте аутентификацию
sudo -u backup python backup_script.py --setup-auth --config /opt/db-backup/.env

# 4. Проверьте работу
sudo -u backup python backup_script.py --test-connections --config /opt/db-backup/.env
```

### Настройка для Docker окружения
```bash
# Создайте docker-compose.yml с паролями
cat > docker-compose.yml << EOF
version: '3.8'
services:
  backup:
    build: .
    environment:
      - PGPASSWORD=docker_pg_password
      - MYSQL_ROOT_PASSWORD=docker_mysql_password
      - MONGO_PASSWORD=docker_mongo_password
    volumes:
      - ./backups:/app/backups
    depends_on:
      - postgres
      - mysql
      - mongodb
EOF

# Запустите настройку
docker-compose run backup python backup_script.py --setup-auth
```

---

**🔐 Важно:** После настройки файлов аутентификации регулярно проверяйте их безопасность и обновляйте пароли согласно политике безопасности вашей организации. 