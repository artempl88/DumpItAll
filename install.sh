#!/bin/bash

# Быстрый инсталлер DumpItAll - универсальной системы резервного копирования БД
# Использование: curl -sSL https://raw.githubusercontent.com/artempl88/DumpItAll/main/install.sh | sudo bash

set -e

INSTALL_DIR="/opt/dumpitall"
SERVICE_NAME="dumpitall"
GITHUB_REPO="artempl88/DumpItAll"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
error() { echo -e "${RED}❌ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
step() { echo -e "${BLUE}🔧 $1${NC}"; }

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Скрипт должен запускаться от root или с sudo"
        exit 1
    fi
}

# Определение ОС
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        error "Не удалось определить операционную систему"
        exit 1
    fi
    
    info "Обнаружена ОС: $OS $VER"
}

# Установка MongoDB репозитория и ключей
setup_mongodb_repo() {
    step "Настройка репозитория MongoDB..."
    
    case $OS in
        *"Ubuntu"*|*"Debian"*)
            # Установка зависимостей
            apt-get install -y gnupg curl
            
            # Добавление GPG ключа MongoDB (новый способ)
            curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
                gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
            
            # Определение кодового имени релиза
            if [[ "$VER" == "22.04" ]]; then
                CODENAME="jammy"
            elif [[ "$VER" == "20.04" ]]; then
                CODENAME="focal"
            elif [[ "$VER" == "18.04" ]]; then
                CODENAME="bionic"
            else
                CODENAME="jammy"  # По умолчанию для новых версий
            fi
            
            # Добавление репозитория MongoDB
            echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] https://repo.mongodb.org/apt/ubuntu $CODENAME/mongodb-org/7.0 multiverse" | \
                tee /etc/apt/sources.list.d/mongodb-org-7.0.list
            
            # Обновление списка пакетов
            apt-get update
            ;;
        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*)
            # Для CentOS/RHEL создаем yum репозиторий
            cat > /etc/yum.repos.d/mongodb-org-7.0.repo << EOF
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
EOF
            ;;
    esac
    
    success "Репозиторий MongoDB настроен"
}

# Проверка и установка Docker
setup_docker_packages() {
    step "Проверка и установка Docker..."
    
    # Проверяем, установлен ли уже Docker
    if command -v docker &> /dev/null; then
        info "Docker уже установлен: $(docker --version)"
        return 0
    fi
    
    case $OS in
        *"Ubuntu"*|*"Debian"*)
            # Попытка установить docker.io из Ubuntu репозитория
            if apt-get install -y docker.io; then
                success "Docker установлен из Ubuntu репозитория"
            else
                warning "Не удалось установить docker.io, пытаемся установить из официального репозитория Docker"
                
                # Установка Docker из официального репозитория
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
                    gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
                    tee /etc/apt/sources.list.d/docker.list > /dev/null
                
                apt-get update
                apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                
                success "Docker установлен из официального репозитория"
            fi
            ;;
        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*)
            # Для CentOS/RHEL используем официальный репозиторий
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
    esac
    
    success "Docker настроен"
}

# Установка базовых пакетов
install_base_packages() {
    step "Установка базовых пакетов..."
    
    case $OS in
        *"Ubuntu"*|*"Debian"*)
            apt-get update -qq
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                curl \
                wget \
                git \
                postgresql-client \
                mysql-client \
                redis-tools \
                systemd \
                jq \
                gnupg \
                lsb-release
            
            # Установка Docker отдельно с обработкой конфликтов
            setup_docker_packages
            
            # Установка MongoDB клиентов из официального репозитория
            setup_mongodb_repo
            apt-get install -y \
                mongodb-mongosh \
                mongodb-database-tools
            ;;
        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*)
            yum update -y
            yum install -y \
                python3 \
                python3-pip \
                curl \
                wget \
                git \
                postgresql \
                mysql \
                redis \
                systemd \
                jq \
                yum-utils
            
            # Установка Docker отдельно
            setup_docker_packages
            
            # Установка MongoDB клиентов
            setup_mongodb_repo
            yum install -y \
                mongodb-mongosh \
                mongodb-database-tools
            ;;
        *)
            warning "Неподдерживаемая ОС, пытаемся установить с помощью пакетного менеджера по умолчанию"
            ;;
    esac
    
    success "Базовые пакеты установлены"
}

# Настройка Python окружения
setup_python_env() {
    step "Настройка Python окружения..."
    
    # Создание виртуального окружения
    python3 -m venv $INSTALL_DIR/venv
    source $INSTALL_DIR/venv/bin/activate
    
    # Обновление pip
    pip install --upgrade pip
    
    success "Python окружение настроено"
}

# Загрузка скриптов
download_scripts() {
    step "Загрузка скриптов резервного копирования..."
    
    # Создание директории
    mkdir -p $INSTALL_DIR
    cd $INSTALL_DIR
    
    # Если используется Git репозиторий
    if [ ! -z "$GITHUB_REPO" ] && [ "$GITHUB_REPO" != "your-username/DumpItAll" ]; then
        git clone https://github.com/$GITHUB_REPO.git .
        
        # Копирование файла сервиса в правильное место
        if [ -f "$INSTALL_DIR/dumpitall.service" ]; then
            cp "$INSTALL_DIR/dumpitall.service" "/etc/systemd/system/$SERVICE_NAME.service"
            success "Файл сервиса скопирован"
        else
            warning "Файл сервиса не найден в репозитории, создаем локально"
            create_service_file
        fi
    else
        # Создание файлов локально (используем встроенный код)
        create_backup_script
        create_requirements_file
        create_service_file
    fi
    
    success "Скрипты загружены"
}

# Создание основного скрипта резервного копирования
create_backup_script() {
    cat > $INSTALL_DIR/backup_script.py << 'EOF'
# Здесь будет весь код из артефакта db_backup_script
# Для краткости показываю только заголовок
#!/usr/bin/env python3
"""
Универсальный скрипт для автоматического обнаружения и резервного копирования
всех баз данных на VPS (системные и в Docker контейнерах)
"""
# ... остальной код ...
EOF
}

# Создание файла зависимостей
create_requirements_file() {
    cat > $INSTALL_DIR/requirements.txt << 'EOF'
google-api-python-client==2.108.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
schedule==1.2.0
python-dotenv==1.0.0
docker==6.1.3
psutil==5.9.5
EOF
}

# Создание systemd сервиса
create_service_file() {
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Universal Database Backup Service
After=network.target docker.service
Wants=network.target

[Service]
Type=simple
User=backup
Group=backup
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/backup_script.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF
}

# Установка Python зависимостей
install_python_deps() {
    step "Установка Python зависимостей..."
    
    source $INSTALL_DIR/venv/bin/activate
    pip install -r $INSTALL_DIR/requirements.txt
    
    success "Python зависимости установлены"
}

# Создание пользователя для резервного копирования
create_backup_user() {
    step "Создание пользователя backup..."
    
    if ! id "backup" &>/dev/null; then
        useradd -r -s /bin/bash -d $INSTALL_DIR -m backup
        usermod -aG docker backup
        success "Пользователь backup создан"
    else
        warning "Пользователь backup уже существует"
    fi
    
    # Установка владельца
    chown -R backup:backup $INSTALL_DIR
    chmod 755 $INSTALL_DIR
    chmod +x $INSTALL_DIR/backup_script.py
}

# Настройка Docker
setup_docker() {
    step "Настройка Docker..."
    
    # Проверяем что Docker установлен
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен, но требуется для работы системы"
        exit 1
    fi
    
    # Запуск и включение Docker сервиса
    systemctl enable docker
    systemctl start docker
    
    # Добавление пользователя backup в группу docker
    usermod -aG docker backup
    
    # Проверка что Docker работает
    if docker info &> /dev/null; then
        success "Docker запущен и работает"
    else
        warning "Docker установлен, но не запущен или есть проблемы с правами"
    fi
}

# Настройка баз данных
setup_databases() {
    step "Настройка доступа к базам данных..."
    
    # PostgreSQL
    if systemctl is-active --quiet postgresql; then
        sudo -u postgres psql -c "
            DO \$\$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'backup_user') THEN
                    CREATE USER backup_user WITH PASSWORD 'backup_password_$(openssl rand -hex 8)';
                END IF;
            END
            \$\$;
            GRANT CONNECT ON DATABASE template1 TO backup_user;
            ALTER USER backup_user CREATEDB;
        " 2>/dev/null || warning "Не удалось настроить PostgreSQL"
    fi
    
    # MySQL
    if systemctl is-active --quiet mysql || systemctl is-active --quiet mariadb; then
        MYSQL_BACKUP_PASS=$(openssl rand -hex 12)
        mysql -u root -e "
            CREATE USER IF NOT EXISTS 'backup_user'@'localhost' IDENTIFIED BY '$MYSQL_BACKUP_PASS';
            GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER, SHOW DATABASES ON *.* TO 'backup_user'@'localhost';
            FLUSH PRIVILEGES;
        " 2>/dev/null || warning "Не удалось настроить MySQL"
    fi
    
    success "Базы данных настроены"
}

# Создание конфигурационного файла
create_config() {
    step "Создание конфигурационного файла..."
    
    cat > $INSTALL_DIR/.env << EOF
# Настройки Google Drive
DRIVE_FOLDER_ID=

# Настройки резервного копирования
BACKUP_DIR=$INSTALL_DIR/backups

# Логирование
LOG_LEVEL=INFO
EOF
    
    # Создание директории для резервных копий
    mkdir -p $INSTALL_DIR/backups
    
    chown backup:backup $INSTALL_DIR/.env
    chmod 600 $INSTALL_DIR/.env
    
    success "Конфигурация создана"
}

# Установка и запуск сервиса
setup_service() {
    step "Настройка systemd сервиса..."
    
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    success "Сервис настроен"
}

# Тестирование установки
test_installation() {
    step "Тестирование установки..."
    
    # Проверка Python скрипта
    if su backup -c "cd $INSTALL_DIR && $INSTALL_DIR/venv/bin/python -c 'import backup_script'"; then
        success "Python скрипт загружается корректно"
    else
        error "Ошибка загрузки Python скрипта"
    fi
    
    # Проверка Docker доступа
    if su backup -c "docker ps" &>/dev/null; then
        success "Docker доступен пользователю backup"
    else
        warning "Docker недоступен (требуется перезагрузка для применения групп)"
    fi
    
    # Проверка сервиса
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        success "Сервис включен в автозагрузку"
    else
        error "Сервис не включен в автозагрузку"
    fi
}

# Вывод инструкций по завершению
show_completion_instructions() {
    echo ""
    echo "🎉 Установка завершена!"
    echo ""
    info "📋 Следующие шаги для завершения настройки:"
    echo ""
    echo "1. Настройте Google Drive API:"
    echo "   - Создайте Service Account в Google Cloud Console"
    echo "   - Скачайте JSON ключ и сохраните как: $INSTALL_DIR/service-account-key.json"
    echo "   - Выполните: chown backup:backup $INSTALL_DIR/service-account-key.json"
    echo ""
    echo "2. Настройте Google Drive папку:"
    echo "   - Создайте папку на Google Drive"
    echo "   - Скопируйте ID папки из URL"
    echo "   - Добавьте в $INSTALL_DIR/.env: DRIVE_FOLDER_ID=your_folder_id"
    echo ""
    echo "3. Запустите сервис:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "4. Проверьте статус:"
    echo "   sudo systemctl status $SERVICE_NAME"
    echo "   tail -f $INSTALL_DIR/backup.log"
    echo ""
    echo "5. Просмотрите обнаруженные БД:"
    echo "   cat $INSTALL_DIR/backups/discovery_report_*.json | jq ."
    echo ""
    warning "Перезагрузите систему или выполните 'newgrp docker' для применения групп Docker"
}

# Главная функция установки
main() {
    echo "🚀 Универсальный инсталлер системы резервного копирования БД"
    echo "================================================================"
    
    check_root
    detect_os
    install_base_packages
    download_scripts
    setup_python_env
    install_python_deps
    create_backup_user
    setup_docker
    setup_databases
    create_config
    setup_service
    test_installation
    show_completion_instructions
    
    echo ""
    success "Установка успешно завершена! 🎊"
}

# Обработка ошибок
trap 'error "Произошла ошибка в строке $LINENO. Код выхода: $?"' ERR

# Запуск установки
main "$@"
