#!/bin/bash

# Скрипт для автоматической настройки доступа к базам данных
# для резервного копирования

set -e

echo "🔧 Настройка доступа к базам данных для резервного копирования"

# Функция для проверки, запущен ли сервис
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✅ $service запущен"
        return 0
    else
        echo "❌ $service не запущен"
        return 1
    fi
}

# Настройка PostgreSQL
setup_postgresql() {
    echo "🐘 Настройка PostgreSQL..."
    
    if check_service postgresql; then
        # Создание пользователя для резервного копирования
        sudo -u postgres psql -c "
            DO \$\$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'backup_user') THEN
                    CREATE USER backup_user WITH PASSWORD 'backup_password';
                END IF;
            END
            \$\$;
        " 2>/dev/null || echo "⚠️ Пользователь backup_user уже существует"
        
        # Предоставление прав на все базы данных
        sudo -u postgres psql -c "
            GRANT CONNECT ON DATABASE template1 TO backup_user;
            ALTER USER backup_user CREATEDB;
        " 2>/dev/null
        
        # Настройка pg_hba.conf для локального доступа
        PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
        
        if [ -f "$PG_HBA" ]; then
            # Создание резервной копии
            sudo cp "$PG_HBA" "$PG_HBA.backup.$(date +%Y%m%d)"
            
            # Добавление правила для backup_user
            if ! sudo grep -q "backup_user" "$PG_HBA"; then
                echo "local   all   backup_user   trust" | sudo tee -a "$PG_HBA"
                echo "host    all   backup_user   127.0.0.1/32   trust" | sudo tee -a "$PG_HBA"
                sudo systemctl reload postgresql
                echo "✅ Настройки PostgreSQL обновлены"
            fi
        fi
    fi
}

# Настройка MySQL/MariaDB
setup_mysql() {
    echo "🐬 Настройка MySQL/MariaDB..."
    
    if check_service mysql || check_service mariadb; then
        # Создание пользователя для резервного копирования
        mysql -u root -e "
            CREATE USER IF NOT EXISTS 'backup_user'@'localhost' IDENTIFIED BY 'backup_password';
            GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER, SHOW DATABASES ON *.* TO 'backup_user'@'localhost';
            FLUSH PRIVILEGES;
        " 2>/dev/null && echo "✅ Пользователь MySQL backup_user создан" || echo "⚠️ Ошибка создания пользователя MySQL"
        
        # Создание файла .my.cnf для автоматической аутентификации
        cat > ~/.my.cnf << EOF
[client]
user=backup_user
password=backup_password
host=localhost

[mysqldump]
user=backup_user
password=backup_password
host=localhost
single-transaction
routines
triggers
EOF
        chmod 600 ~/.my.cnf
        echo "✅ Файл .my.cnf создан"
    fi
}

# Настройка MongoDB
setup_mongodb() {
    echo "🍃 Настройка MongoDB..."
    
    if check_service mongod; then
        # Проверка, включена ли аутентификация
        if mongo --eval "db.version()" >/dev/null 2>&1; then
            # Создание пользователя для резервного копирования
            mongo admin --eval "
                db.createUser({
                    user: 'backup_user',
                    pwd: 'backup_password',
                    roles: [
                        { role: 'backup', db: 'admin' },
                        { role: 'readAnyDatabase', db: 'admin' }
                    ]
                })
            " 2>/dev/null && echo "✅ Пользователь MongoDB backup_user создан" || echo "⚠️ Пользователь MongoDB уже существует"
        else
            echo "✅ MongoDB работает без аутентификации"
        fi
    fi
}

# Настройка Redis
setup_redis() {
    echo "🔴 Настройка Redis..."
    
    if check_service redis-server || check_service redis; then
        # Redis обычно не требует специальной настройки для резервного копирования
        echo "✅ Redis доступен для резервного копирования"
    fi
}

# Установка необходимых клиентов
install_clients() {
    echo "📦 Установка клиентов баз данных..."
    
    # Обновление списка пакетов
    sudo apt-get update -qq
    
    # PostgreSQL клиент
    if ! command -v pg_dump &> /dev/null; then
        sudo apt-get install -y postgresql-client
        echo "✅ PostgreSQL клиент установлен"
    fi
    
    # MySQL клиент
    if ! command -v mysqldump &> /dev/null; then
        sudo apt-get install -y mysql-client
        echo "✅ MySQL клиент установлен"
    fi
    
    # MongoDB клиент
    if ! command -v mongodump &> /dev/null; then
        sudo apt-get install -y mongodb-clients
        echo "✅ MongoDB клиент установлен"
    fi
    
    # Redis клиент
    if ! command -v redis-cli &> /dev/null; then
        sudo apt-get install -y redis-tools
        echo "✅ Redis клиент установлен"
    fi
}

# Настройка Docker доступа
setup_docker() {
    echo "🐳 Настройка Docker доступа..."
    
    if command -v docker &> /dev/null; then
        # Добавление пользователя в группу docker
        sudo usermod -aG docker $USER
        echo "✅ Пользователь добавлен в группу docker"
        echo "⚠️ Требуется перезагрузка сессии: newgrp docker"
    else
        echo "❌ Docker не установлен"
    fi
}

# Создание пользователя для резервного копирования
create_backup_user() {
    echo "👤 Создание пользователя для резервного копирования..."
    
    if ! id "backup" &>/dev/null; then
        sudo useradd -r -s /bin/bash -d /opt/db-backup -m backup
        sudo usermod -aG docker backup
        echo "✅ Пользователь backup создан"
    else
        echo "⚠️ Пользователь backup уже существует"
    fi
}

# Создание директории для резервных копий
create_backup_directory() {
    echo "📁 Создание директории для резервных копий..."
    
    sudo mkdir -p /opt/db-backup/backups
    sudo chown -R backup:backup /opt/db-backup
    sudo chmod 755 /opt/db-backup
    echo "✅ Директория /opt/db-backup создана"
}

# Создание файла окружения
create_env_file() {
    echo "⚙️ Создание файла окружения..."
    
    cat > /tmp/db-backup.env << EOF
# Настройки Google Drive
DRIVE_FOLDER_ID=your_drive_folder_id_here

# Настройки резервного копирования
BACKUP_DIR=/opt/db-backup/backups

# Настройки аутентификации (если нужно)
# DB_USER=backup_user
# DB_PASSWORD=backup_password
EOF

    sudo mv /tmp/db-backup.env /opt/db-backup/.env
    sudo chown backup:backup /opt/db-backup/.env
    sudo chmod 600 /opt/db-backup/.env
    echo "✅ Файл .env создан в /opt/db-backup/"
}

# Тестирование подключений
test_connections() {
    echo "🧪 Тестирование подключений к базам данных..."
    
    # PostgreSQL
    if command -v psql &> /dev/null; then
        if psql -h localhost -U backup_user -d template1 -c "\l" &>/dev/null; then
            echo "✅ PostgreSQL: подключение успешно"
        else
            echo "❌ PostgreSQL: ошибка подключения"
        fi
    fi
    
    # MySQL
    if command -v mysql &> /dev/null; then
        if mysql -u backup_user -e "SHOW DATABASES;" &>/dev/null; then
            echo "✅ MySQL: подключение успешно"
        else
            echo "❌ MySQL: ошибка подключения"
        fi
    fi
    
    # MongoDB
    if command -v mongo &> /dev/null; then
        if mongo --eval "db.version()" &>/dev/null; then
            echo "✅ MongoDB: подключение успешно"
        else
            echo "❌ MongoDB: ошибка подключения"
        fi
    fi
    
    # Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &>/dev/null; then
            echo "✅ Redis: подключение успешно"
        else
            echo "❌ Redis: ошибка подключения"
        fi
    fi
    
    # Docker
    if command -v docker &> /dev/null; then
        if docker ps &>/dev/null; then
            echo "✅ Docker: доступ успешно"
        else
            echo "❌ Docker: нет доступа (требуется newgrp docker)"
        fi
    fi
}

# Главная функция
main() {
    echo "🚀 Начало настройки системы резервного копирования..."
    
    # Проверка прав root
    if [[ $EUID -ne 0 ]]; then
        echo "❌ Скрипт должен запускаться от root или с sudo"
        exit 1
    fi
    
    install_clients
    setup_postgresql
    setup_mysql
    setup_mongodb
    setup_redis
    setup_docker
    create_backup_user
    create_backup_directory
    create_env_file
    
    echo ""
    echo "🎉 Настройка завершена!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Настройте Google Drive API и сохраните service-account-key.json в /opt/db-backup/"
    echo "2. Отредактируйте /opt/db-backup/.env и укажите DRIVE_FOLDER_ID"
    echo "3. Скопируйте скрипт backup_script.py в /opt/db-backup/"
    echo "4. Установите systemd сервис"
    echo "5. Перезагрузите сессию: newgrp docker"
    echo ""
    
    test_connections
}

# Запуск
main "$@"
