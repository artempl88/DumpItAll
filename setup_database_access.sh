#!/usr/bin/env python3
"""
Скрипт автоматической настройки аутентификации для DumpItAll
Создает файлы аутентификации для различных СУБД
"""

import os
import sys
import stat
import subprocess
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AuthSetup:
    def __init__(self):
        self.home_dir = Path.home()
        self.env_file = '.env'
        self.credentials = {}
        
    def load_env_file(self):
        """Загрузка учетных данных из .env файла"""
        if not os.path.exists(self.env_file):
            logging.error(f"Файл {self.env_file} не найден")
            logging.info("Создайте файл .env с учетными данными:")
            print("""
# PostgreSQL
PGPASSWORD=your_postgres_password

# MySQL
MYSQL_ROOT_PASSWORD=your_mysql_password

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=your_mongo_password

# Redis
REDIS_PASSWORD=your_redis_password
""")
            return False
            
        logging.info(f"📄 Загрузка конфигурации из {self.env_file}")
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if value:  # Только если значение не пустое
                            os.environ[key] = value
                            self.credentials[key] = value
                            
            return True
        except Exception as e:
            logging.error(f"Ошибка чтения .env файла: {e}")
            return False
    
    def setup_postgresql_auth(self):
        """Настройка аутентификации PostgreSQL через .pgpass"""
        logging.info("🐘 Настройка PostgreSQL аутентификации...")
        
        pgpass_file = self.home_dir / '.pgpass'
        
        # Получаем учетные данные
        password = (self.credentials.get('PGPASSWORD') or 
                   self.credentials.get('POSTGRES_PASSWORD') or 
                   os.environ.get('PGPASSWORD') or 
                   os.environ.get('POSTGRES_PASSWORD'))
        
        if not password:
            logging.warning("⚠️ PostgreSQL пароль не найден в .env файле")
            return False
            
        user = (self.credentials.get('POSTGRES_USER') or 
               self.credentials.get('PGUSER') or 
               os.environ.get('POSTGRES_USER') or 
               os.environ.get('PGUSER') or 
               'postgres')
        
        # Создаем содержимое .pgpass
        pgpass_content = f"""# PostgreSQL password file
# hostname:port:database:username:password
localhost:5432:*:{user}:{password}
127.0.0.1:5432:*:{user}:{password}
*:5432:*:{user}:{password}
"""
        
        try:
            # Создаем резервную копию если файл существует
            if pgpass_file.exists():
                backup_file = pgpass_file.with_suffix('.backup')
                pgpass_file.rename(backup_file)
                logging.info(f"📋 Создана резервная копия: {backup_file}")
            
            # Записываем новый файл
            with open(pgpass_file, 'w') as f:
                f.write(pgpass_content)
            
            # Устанавливаем права доступа 600
            os.chmod(pgpass_file, stat.S_IRUSR | stat.S_IWUSR)
            
            logging.info(f"✅ Создан файл {pgpass_file} с правами 600")
            
            # Тестируем подключение
            self._test_postgresql_connection(user)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка создания .pgpass: {e}")
            return False
    
    def setup_mysql_auth(self):
        """Настройка аутентификации MySQL через .my.cnf"""
        logging.info("🐬 Настройка MySQL аутентификации...")
        
        mycnf_file = self.home_dir / '.my.cnf'
        
        # Получаем учетные данные
        password = (self.credentials.get('MYSQL_ROOT_PASSWORD') or 
                   self.credentials.get('MYSQL_PASSWORD') or 
                   os.environ.get('MYSQL_ROOT_PASSWORD') or 
                   os.environ.get('MYSQL_PASSWORD'))
        
        if not password:
            logging.warning("⚠️ MySQL пароль не найден в .env файле")
            return False
            
        user = (self.credentials.get('MYSQL_USER') or 
               self.credentials.get('MYSQL_ROOT_USER') or 
               os.environ.get('MYSQL_USER') or 
               os.environ.get('MYSQL_ROOT_USER') or 
               'root')
        
        host = (self.credentials.get('MYSQL_HOST') or 
               os.environ.get('MYSQL_HOST') or 
               'localhost')
        
        port = (self.credentials.get('MYSQL_PORT') or 
               os.environ.get('MYSQL_PORT') or 
               '3306')
        
        # Создаем содержимое .my.cnf
        mycnf_content = f"""# MySQL client configuration
[client]
user={user}
password={password}
host={host}
port={port}

[mysql]
user={user}
password={password}

[mysqldump]
user={user}
password={password}

[mysqlcheck]
user={user}
password={password}

[mysqlshow]
user={user}
password={password}
"""
        
        try:
            # Создаем резервную копию если файл существует
            if mycnf_file.exists():
                backup_file = mycnf_file.with_suffix('.backup')
                mycnf_file.rename(backup_file)
                logging.info(f"📋 Создана резервная копия: {backup_file}")
            
            # Записываем новый файл
            with open(mycnf_file, 'w') as f:
                f.write(mycnf_content)
            
            # Устанавливаем права доступа 600
            os.chmod(mycnf_file, stat.S_IRUSR | stat.S_IWUSR)
            
            logging.info(f"✅ Создан файл {mycnf_file} с правами 600")
            
            # Тестируем подключение
            self._test_mysql_connection()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка создания .my.cnf: {e}")
            return False
    
    def setup_mongodb_auth(self):
        """Настройка аутентификации MongoDB через .mongorc.js"""
        logging.info("🍃 Настройка MongoDB аутентификации...")
        
        mongorc_file = self.home_dir / '.mongorc.js'
        
        # Получаем учетные данные
        user = (self.credentials.get('MONGO_USER') or 
               self.credentials.get('MONGODB_USER') or 
               os.environ.get('MONGO_USER') or 
               os.environ.get('MONGODB_USER') or 
               'admin')
        
        password = (self.credentials.get('MONGO_PASSWORD') or 
                   self.credentials.get('MONGODB_PASSWORD') or 
                   os.environ.get('MONGO_PASSWORD') or 
                   os.environ.get('MONGODB_PASSWORD'))
        
        if not password:
            logging.warning("⚠️ MongoDB пароль не найден в .env файле")
            return False
            
        host = (self.credentials.get('MONGO_HOST') or 
               self.credentials.get('MONGODB_HOST') or 
               os.environ.get('MONGO_HOST') or 
               os.environ.get('MONGODB_HOST') or 
               'localhost')
        
        port = (self.credentials.get('MONGO_PORT') or 
               self.credentials.get('MONGODB_PORT') or 
               os.environ.get('MONGO_PORT') or 
               os.environ.get('MONGODB_PORT') or 
               '27017')
        
        # Создаем содержимое .mongorc.js
        mongorc_content = f"""// MongoDB authentication configuration
var mongoUser = '{user}';
var mongoPassword = '{password}';
var mongoHost = '{host}';
var mongoPort = {port};

function autoAuth() {{
    try {{
        db = db.getSiblingDB('admin');
        db.auth(mongoUser, mongoPassword);
        print('✅ MongoDB аутентификация успешна');
    }} catch (e) {{
        print('⚠️ MongoDB аутентификация не удалась: ' + e);
    }}
}}

// Автоматическая аутентификация при подключении
if (typeof db !== 'undefined') {{
    autoAuth();
}}
"""
        
        try:
            # Создаем резервную копию если файл существует
            if mongorc_file.exists():
                backup_file = mongorc_file.with_suffix('.backup')
                mongorc_file.rename(backup_file)
                logging.info(f"📋 Создана резервная копия: {backup_file}")
            
            # Записываем новый файл
            with open(mongorc_file, 'w') as f:
                f.write(mongorc_content)
            
            # Устанавливаем права доступа 600
            os.chmod(mongorc_file, stat.S_IRUSR | stat.S_IWUSR)
            
            logging.info(f"✅ Создан файл {mongorc_file} с правами 600")
            
            # Тестируем подключение
            self._test_mongodb_connection(user, password, host, port)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка создания .mongorc.js: {e}")
            return False
    
    def setup_redis_auth(self):
        """Настройка аутентификации Redis через .rediscli_auth"""
        logging.info("🔴 Настройка Redis аутентификации...")
        
        rediscli_file = self.home_dir / '.rediscli_auth'
        
        # Получаем учетные данные
        password = (self.credentials.get('REDIS_PASSWORD') or 
                   os.environ.get('REDIS_PASSWORD'))
        
        if not password:
            logging.warning("⚠️ Redis пароль не найден в .env файле")
            return False
        
        try:
            # Создаем резервную копию если файл существует
            if rediscli_file.exists():
                backup_file = rediscli_file.with_suffix('.backup')
                rediscli_file.rename(backup_file)
                logging.info(f"📋 Создана резервная копия: {backup_file}")
            
            # Записываем пароль в файл
            with open(rediscli_file, 'w') as f:
                f.write(password)
            
            # Устанавливаем права доступа 600
            os.chmod(rediscli_file, stat.S_IRUSR | stat.S_IWUSR)
            
            logging.info(f"✅ Создан файл {rediscli_file} с правами 600")
            
            # Настройка переменной окружения для redis-cli
            os.environ['REDISCLI_AUTH'] = password
            
            # Тестируем подключение
            self._test_redis_connection(password)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка создания .rediscli_auth: {e}")
            return False
    
    def setup_shell_aliases(self):
        """Настройка алиасов для удобного использования"""
        logging.info("🔧 Настройка shell алиасов...")
        
        bashrc_file = self.home_dir / '.bashrc'
        
        aliases = """
# DumpItAll Database Aliases
alias pgdump='pg_dump -h localhost -U postgres'
alias pglist='psql -h localhost -U postgres -l'
alias mysqllist='mysql -e "SHOW DATABASES;"'
alias mongolist='mongo --eval "db.adminCommand(\"listDatabases\").databases.forEach(function(db) { print(db.name) })" --quiet'
alias redisinfo='redis-cli INFO keyspace'

# Quick backup commands
alias backup-pg='pg_dump -h localhost -U postgres -d $1 > backup_$(date +%Y%m%d_%H%M%S).sql'
alias backup-mysql='mysqldump --single-transaction --routines --triggers $1 > backup_$(date +%Y%m%d_%H%M%S).sql'
"""
        
        try:
            # Проверяем, есть ли уже наши алиасы
            if bashrc_file.exists():
                with open(bashrc_file, 'r') as f:
                    content = f.read()
                    if 'DumpItAll Database Aliases' in content:
                        logging.info("ℹ️ Алиасы уже настроены")
                        return True
            
            # Добавляем алиасы
            with open(bashrc_file, 'a') as f:
                f.write(aliases)
            
            logging.info(f"✅ Алиасы добавлены в {bashrc_file}")
            logging.info("💡 Выполните 'source ~/.bashrc' для активации алиасов")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка настройки алиасов: {e}")
            return False
    
    def _test_postgresql_connection(self, user='postgres'):
        """Тест подключения к PostgreSQL"""
        try:
            cmd = ['psql', '-h', 'localhost', '-U', user, '-d', 'template1', '-c', '\\l', '-t']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logging.info("✅ PostgreSQL: подключение успешно (без ввода пароля)")
                return True
            else:
                logging.warning("⚠️ PostgreSQL: не удалось подключиться автоматически")
                return False
                
        except Exception as e:
            logging.error(f"❌ Ошибка тестирования PostgreSQL: {e}")
            return False
    
    def _test_mysql_connection(self):
        """Тест подключения к MySQL"""
        try:
            cmd = ['mysql', '-e', 'SELECT VERSION();']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logging.info("✅ MySQL: подключение успешно (без ввода пароля)")
                return True
            else:
                logging.warning("⚠️ MySQL: не удалось подключиться автоматически")
                return False
                
        except Exception as e:
            logging.error(f"❌ Ошибка тестирования MySQL: {e}")
            return False
    
    def _test_mongodb_connection(self, user, password, host, port):
        """Тест подключения к MongoDB"""
        try:
            cmd = ['mongo', '--host', f"{host}:{port}", '--username', user, 
                   '--password', password, '--eval', 'db.version()', '--quiet']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logging.info("✅ MongoDB: подключение успешно")
                return True
            else:
                logging.warning("⚠️ MongoDB: не удалось подключиться")
                return False
                
        except Exception as e:
            logging.error(f"❌ Ошибка тестирования MongoDB: {e}")
            return False
    
    def _test_redis_connection(self, password):
        """Тест подключения к Redis"""
        try:
            cmd = ['redis-cli', '-a', password, 'ping']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'PONG' in result.stdout:
                logging.info("✅ Redis: подключение успешно")
                return True
            else:
                logging.warning("⚠️ Redis: не удалось подключиться")
                return False
                
        except Exception as e:
            logging.error(f"❌ Ошибка тестирования Redis: {e}")
            return False
    
    def check_prerequisites(self):
        """Проверка наличия необходимых клиентов БД"""
        logging.info("🔍 Проверка установленных клиентов БД...")
        
        clients = {
            'psql': 'PostgreSQL клиент',
            'mysql': 'MySQL клиент',
            'mongo': 'MongoDB клиент',
            'redis-cli': 'Redis клиент'
        }
        
        missing = []
        for cmd, name in clients.items():
            if subprocess.run(['which', cmd], capture_output=True).returncode != 0:
                missing.append(name)
                logging.warning(f"⚠️ {name} не установлен")
            else:
                logging.info(f"✅ {name} установлен")
        
        if missing:
            logging.warning("\n⚠️ Установите недостающие клиенты:")
            logging.warning("sudo apt-get update")
            logging.warning("sudo apt-get install -y postgresql-client mysql-client mongodb-clients redis-tools")
            
        return len(missing) == 0
    
    def print_summary(self):
        """Вывод итоговой информации"""
        print("\n" + "=" * 60)
        print("📊 ИТОГИ НАСТРОЙКИ АУТЕНТИФИКАЦИИ")
        print("=" * 60)
        
        files = [
            ('~/.pgpass', 'PostgreSQL'),
            ('~/.my.cnf', 'MySQL'),
            ('~/.mongorc.js', 'MongoDB'),
            ('~/.rediscli_auth', 'Redis')
        ]
        
        for file_path, db_name in files:
            full_path = Path.home() / file_path[2:]  # Убираем ~/
            if full_path.exists():
                print(f"✅ {db_name}: {file_path}")
            else:
                print(f"❌ {db_name}: файл не создан")
        
        print("\n💡 Полезные команды:")
        print("  psql -l                    # Список БД PostgreSQL")
        print("  mysql -e 'SHOW DATABASES;' # Список БД MySQL")
        print("  mongo --eval 'db.version()' # Версия MongoDB")
        print("  redis-cli ping             # Проверка Redis")
        
        print("\n🔐 Безопасность:")
        print("  - Все файлы созданы с правами 600 (только для владельца)")
        print("  - Резервные копии сохранены с расширением .backup")
        print("  - Пароли взяты из .env файла")
        
        print("\n🚀 Теперь можно запустить резервное копирование:")
        print("  python3 backup_script.py --backup-once")
        print("=" * 60)
    
    def run(self):
        """Основной процесс настройки"""
        print("🔐 DumpItAll - Настройка автоматической аутентификации")
        print("=" * 60)
        
        # Проверка клиентов БД
        if not self.check_prerequisites():
            logging.warning("⚠️ Некоторые клиенты БД не установлены")
            response = input("\nПродолжить настройку? (y/n): ")
            if response.lower() != 'y':
                return
        
        # Загрузка конфигурации
        if not self.load_env_file():
            return
        
        # Настройка каждой СУБД
        print("\n🚀 Начинаем настройку...\n")
        
        self.setup_postgresql_auth()
        self.setup_mysql_auth()
        self.setup_mongodb_auth()
        self.setup_redis_auth()
        self.setup_shell_aliases()
        
        # Итоговая информация
        self.print_summary()

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Настройка автоматической аутентификации для DumpItAll'
    )
    parser.add_argument(
        '--config', 
        type=str, 
        default='.env',
        help='Путь к файлу конфигурации (по умолчанию: .env)'
    )
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Только тестирование подключений без создания файлов'
    )
    
    args = parser.parse_args()
    
    setup = AuthSetup()
    setup.env_file = args.config
    
    if args.test_only:
        logging.info("🧪 Режим тестирования подключений")
        setup.load_env_file()
        setup._test_postgresql_connection()
        setup._test_mysql_connection()
        # Для MongoDB и Redis нужны параметры
    else:
        setup.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Настройка прервана пользователем")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logging.error(traceback.format_exc())