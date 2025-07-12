#!/usr/bin/env python3
"""
DumpItAll - Универсальная система автоматического обнаружения и резервного копирования
всех баз данных на VPS (системные и в Docker контейнерах)

🗄️ Dump It All - Find It, Dump It, Save It!
"""

import os
import json
import time
import subprocess
import schedule
import psutil
import docker
import sqlite3
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import logging
import glob
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

def print_logo():
    """Отображение ASCII логотипа DumpItAll"""
    logo = """
....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
..............................................:-=**+-:..............................................
............................................=#%%%##%%%#+:...........................................
..........................................+%%%=:.....=%%%*..........................................
........................................-#%#=..........-#%#-........................................
.......................................=%%+..............+%%=.......................................
......................................+%%=................=%%+......................................
.....................................=%%=..................=%%+.....................................
....................................:%%+......:=++++=:......=%%-....................................
....................................#%*....:#%%%%%%%%%%*:....*%#....................................
...................................=%#-..-%%%%%%%%%%%%%%%%-..:#%+...................................
..................................:%%+.:#%%%%%%%%%%%%%%%%%%#:.+%%:..................................
..................................=%#-=%%%%%%%%%%%%%%%%%%%%%%=-#%+..................................
.................................:*%*-#%%%%%%%%%%%%%%%%%%%%%%#-*%*..................................
.................................:*%=+%%%%%%%%%%%%%%%%%%%%%%%%+=%#:.................................
.................................:*%+=%%%%%%%%%%%%%%%%%%%%%%%%=+%*..................................
..................................+%%=+%%%%%%%%%%%%%%%%%%%%%%+-#%=..................................
..............................:=#%%%%%=:#%%%%%%%%%%%%%%%%%%#:=%%%%%*=:..............................
.............................*%%*-:.-#%%+=%%%%%%%%%%%%%%%%==%%#-.:-*%%+.............................
...........................:#%+:......-#%%*+%%%%%%%%%%%%**%%#-......:*%#:...........................
..........................:*%*:.........-*%%%%%%%%%%%%%%%%*-.........:*%*:..........................
..........................=%%:............:+%%%%%%%%%%%%+:............:%%=..........................
.........................-%%:..-%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#:..:%%-.........................
........................:%%=...+%=................................=%+...=%%:........................
.......................:#%+....=%+................................+%=....+%#:.......................
......................:*%#:....-%*:..............................:*%-....:#%*:......................
......................=%%:.:*+=:%*:............:+**=:............:*%:=+*:.:%%=......................
.....................:%%-...:-*%%#-............#%%%%*............-#%%*-:...-%%:.....................
.....................=%*:......:%%-............#%%%%*............-%%:......:*%=.....................
.....................=%#:......*%%=............:=**=.............=%%*:.....:*%=.....................
......................*%#-....=%%%+..............................+%%%=....:#%*:.....................
.......................=%%%#-:+%%%*..............................#%%%+:-*%%%+.......................
.........................-+#%%%%%%%******************************%%%%%%%#+-.........................
.............................:-+#%%=----------------------------=%%#+-:.............................
.................................-%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#-.................................
....................................................................................................
..............######*:..................................-##-.:=-.....-###-...-%#-:%#-...............
..............#%+..=#%*:.:....:...:..::...::...:..:::...-%#-.=%*:...:*%#%*:..-%#-:%#-...............
..............#%+...:%%=+%*:.=%*.+%%##%%###%#-:%%%##%%+.-%#-+%%%#*:.-%#.*%=..-%#-:%#-...............
..............#%+...:%%=+%*:.=%*.+%+..*%*..*%=:%%-..-%%=-%#-.+%*...:%%-.-%%:.-%#-:%#-...............
..............#%+..:*%#:+%*:.=%*.+%+..*%+..*%=:%%-..-%%=-%#-.+%*...*%%%%%%%#:-%#-:%#-...............
..............#%%%%%#+:.-%%##%%*.+%+..*%+..*%=:%%%##%%+.-%#-.-#%%*=%%-...:#%+-%%*:%%#:..............
..............::::::......:-:.::.:::..:::..::::%%::--:...::....:-::::.....:::.:-:.:-:...............
..............................................:%%:..................................................
....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
....................................................................................................
"""
    print(logo)
    print("🗄️ DumpItAll - Универсальная система резервного копирования БД")
    print("🔍 Find It, Dump It, Save It!")
    print("=" * 88)

class UniversalBackup:
    def __init__(self):
        # Настройки Google Drive
        self.CREDENTIALS_FILE = 'service-account-key.json'
        self.DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID', None)
        
        # Папка для резервных копий
        self.BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')
        os.makedirs(self.BACKUP_DIR, exist_ok=True)
        
        # Инициализация сервисов
        self.drive_service = self._init_drive_service()
        self.docker_client = self._init_docker_client()
        
        # Обнаруженные базы данных
        self.discovered_databases = []
        
        # Конфигурация для разных СУБД
        self.db_configs = {
            'postgresql': {
                'default_ports': [5432],
                'process_names': ['postgres', 'postgresql'],
                'backup_cmd': 'pg_dump',
                'docker_images': ['postgres', 'postgis/postgis', 'timescale/timescaledb']
            },
            'mysql': {
                'default_ports': [3306],
                'process_names': ['mysqld', 'mysql'],
                'backup_cmd': 'mysqldump',
                'docker_images': ['mysql', 'mariadb', 'percona']
            },
            'mongodb': {
                'default_ports': [27017],
                'process_names': ['mongod'],
                'backup_cmd': 'mongodump',
                'docker_images': ['mongo', 'mongodb/mongodb-community-server']
            },
            'redis': {
                'default_ports': [6379],
                'process_names': ['redis-server'],
                'backup_cmd': 'redis-cli',
                'docker_images': ['redis', 'bitnami/redis']
            },
            'sqlite': {
                'default_ports': [],
                'process_names': [],
                'backup_cmd': 'sqlite3',
                'docker_images': []
            }
        }

    def _init_drive_service(self):
        """Инициализация сервиса Google Drive"""
        try:
            if os.path.exists(self.CREDENTIALS_FILE):
                credentials = Credentials.from_service_account_file(
                    self.CREDENTIALS_FILE,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                return build('drive', 'v3', credentials=credentials)
            else:
                logging.warning(f"Файл {self.CREDENTIALS_FILE} не найден")
                return None
        except Exception as e:
            logging.error(f"Ошибка инициализации Google Drive API: {e}")
            return None

    def _init_docker_client(self):
        """Инициализация Docker клиента"""
        try:
            return docker.from_env()
        except Exception as e:
            logging.warning(f"Docker недоступен: {e}")
            return None

    def discover_system_databases(self):
        """Обнаружение системных баз данных"""
        logging.info("Сканирование системных процессов...")
        
        system_dbs = []
        
        # Сканирование запущенных процессов
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'].lower()
                
                for db_type, config in self.db_configs.items():
                    if any(name in proc_name for name in config['process_names']):
                        db_info = self._analyze_system_process(proc, db_type, config)
                        if db_info:
                            system_dbs.append(db_info)
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Поиск SQLite файлов
        sqlite_dbs = self._find_sqlite_databases()
        system_dbs.extend(sqlite_dbs)
        
        logging.info(f"Найдено {len(system_dbs)} системных баз данных")
        return system_dbs

    def _analyze_system_process(self, proc, db_type, config):
        """Анализ системного процесса СУБД"""
        try:
            connections = proc.connections() if hasattr(proc, 'connections') else []
            cmdline = proc.cmdline()
            
            # Определение порта
            port = None
            for conn in connections:
                if conn.status == 'LISTEN' and conn.laddr.port in config['default_ports']:
                    port = conn.laddr.port
                    break
            
            if not port:
                port = config['default_ports'][0] if config['default_ports'] else None
            
            # Определение конфигурационных файлов и данных
            data_dir = self._extract_data_directory(cmdline, db_type)
            
            return {
                'type': db_type,
                'source': 'system',
                'host': 'localhost',
                'port': port,
                'pid': proc.pid,
                'data_dir': data_dir,
                'cmdline': ' '.join(cmdline) if cmdline else '',
                'databases': self._get_database_list(db_type, 'localhost', port)
            }
            
        except Exception as e:
            logging.error(f"Ошибка анализа процесса {proc.pid}: {e}")
            return None

    def _extract_data_directory(self, cmdline, db_type):
        """Извлечение директории данных из командной строки"""
        if not cmdline:
            return None
            
        cmdline_str = ' '.join(cmdline)
        
        patterns = {
            'postgresql': ['-D', '--data-directory'],
            'mysql': ['--datadir'],
            'mongodb': ['--dbpath']
        }
        
        if db_type in patterns:
            for pattern in patterns[db_type]:
                if pattern in cmdline_str:
                    parts = cmdline_str.split()
                    try:
                        idx = parts.index(pattern)
                        if idx + 1 < len(parts):
                            return parts[idx + 1]
                    except ValueError:
                        continue
        
        return None

    def discover_docker_databases(self):
        """Обнаружение баз данных в Docker контейнерах"""
        if not self.docker_client:
            return []
            
        logging.info("Сканирование Docker контейнеров...")
        docker_dbs = []
        
        try:
            containers = self.docker_client.containers.list()
            
            for container in containers:
                db_info = self._analyze_docker_container(container)
                if db_info:
                    docker_dbs.extend(db_info)
                    
        except Exception as e:
            logging.error(f"Ошибка сканирования Docker: {e}")
        
        logging.info(f"Найдено {len(docker_dbs)} баз данных в Docker")
        return docker_dbs

    def _analyze_docker_container(self, container):
        """Анализ Docker контейнера"""
        try:
            image_name = container.image.tags[0] if container.image.tags else ''
            container_info = []
            
            for db_type, config in self.db_configs.items():
                if any(img in image_name.lower() for img in config['docker_images']):
                    
                    # Получение портов
                    ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                    exposed_ports = []
                    
                    for port_info in ports.values():
                        if port_info:
                            for binding in port_info:
                                if binding.get('HostPort'):
                                    exposed_ports.append(int(binding['HostPort']))
                    
                    # Получение переменных окружения
                    env_vars = {}
                    for env in container.attrs.get('Config', {}).get('Env', []):
                        if '=' in env:
                            key, value = env.split('=', 1)
                            env_vars[key] = value
                    
                    # Определение учетных данных
                    credentials = self._extract_docker_credentials(env_vars, db_type)
                    
                    # Получение списка баз данных
                    databases = self._get_docker_database_list(container, db_type, credentials)
                    
                    container_info.append({
                        'type': db_type,
                        'source': 'docker',
                        'container_id': container.id,
                        'container_name': container.name,
                        'image': image_name,
                        'host': 'localhost',
                        'ports': exposed_ports,
                        'credentials': credentials,
                        'databases': databases,
                        'volumes': self._get_container_volumes(container)
                    })
            
            return container_info
            
        except Exception as e:
            logging.error(f"Ошибка анализа контейнера {container.name}: {e}")
            return []

    def _extract_docker_credentials(self, env_vars, db_type):
        """Извлечение учетных данных из переменных окружения"""
        credentials = {}
        
        env_mappings = {
            'postgresql': {
                'user': ['POSTGRES_USER', 'POSTGRESQL_USER'],
                'password': ['POSTGRES_PASSWORD', 'POSTGRESQL_PASSWORD'],
                'database': ['POSTGRES_DB', 'POSTGRESQL_DATABASE']
            },
            'mysql': {
                'user': ['MYSQL_USER', 'MARIADB_USER'],
                'password': ['MYSQL_PASSWORD', 'MARIADB_PASSWORD', 'MYSQL_ROOT_PASSWORD'],
                'database': ['MYSQL_DATABASE', 'MARIADB_DATABASE']
            },
            'mongodb': {
                'user': ['MONGO_INITDB_ROOT_USERNAME'],
                'password': ['MONGO_INITDB_ROOT_PASSWORD'],
                'database': ['MONGO_INITDB_DATABASE']
            }
        }
        
        if db_type in env_mappings:
            mapping = env_mappings[db_type]
            for cred_type, env_keys in mapping.items():
                for env_key in env_keys:
                    if env_key in env_vars:
                        credentials[cred_type] = env_vars[env_key]
                        break
        
        return credentials

    def _get_container_volumes(self, container):
        """Получение информации о томах контейнера"""
        volumes = []
        mounts = container.attrs.get('Mounts', [])
        
        for mount in mounts:
            volumes.append({
                'source': mount.get('Source'),
                'destination': mount.get('Destination'),
                'type': mount.get('Type')
            })
        
        return volumes

    def _find_sqlite_databases(self):
        """Поиск SQLite файлов в системе"""
        sqlite_dbs = []
        search_paths = [
            '/var/lib',
            '/opt',
            '/home',
            '/usr/local',
            '/tmp'
        ]
        
        sqlite_extensions = ['*.db', '*.sqlite', '*.sqlite3']
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                for ext in sqlite_extensions:
                    try:
                        files = glob.glob(os.path.join(search_path, '**', ext), recursive=True)
                        for file_path in files:
                            if self._is_sqlite_database(file_path):
                                sqlite_dbs.append({
                                    'type': 'sqlite',
                                    'source': 'system',
                                    'file_path': file_path,
                                    'size': os.path.getsize(file_path),
                                    'databases': [os.path.basename(file_path)]
                                })
                    except (PermissionError, OSError):
                        continue
        
        return sqlite_dbs

    def _is_sqlite_database(self, file_path):
        """Проверка, является ли файл базой данных SQLite"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
                return header.startswith(b'SQLite format 3\x00')
        except:
            return False

    def _get_database_list(self, db_type, host, port):
        """Получение списка баз данных для системных СУБД"""
        databases = []
        
        try:
            if db_type == 'postgresql':
                cmd = ['psql', '-h', host, '-p', str(port), '-U', 'postgres', '-l', '-t']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '|' in line:
                            db_name = line.split('|')[0].strip()
                            if db_name and db_name not in ['template0', 'template1']:
                                databases.append(db_name)
            
            elif db_type == 'mysql':
                cmd = ['mysql', '-h', host, '-P', str(port), '-e', 'SHOW DATABASES;']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        db_name = line.strip()
                        if db_name and db_name not in ['Database', 'information_schema', 'performance_schema', 'mysql', 'sys']:
                            databases.append(db_name)
            
            elif db_type == 'mongodb':
                cmd = ['mongo', '--host', f"{host}:{port}", '--eval', 'db.adminCommand("listDatabases").databases.forEach(function(db) { print(db.name) })']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        db_name = line.strip()
                        if db_name and db_name not in ['admin', 'local', 'config']:
                            databases.append(db_name)
                            
        except Exception as e:
            logging.warning(f"Не удалось получить список БД для {db_type}: {e}")
        
        return databases

    def _get_docker_database_list(self, container, db_type, credentials):
        """Получение списка баз данных в Docker контейнере"""
        databases = []
        
        try:
            if db_type == 'postgresql':
                cmd = ['psql', '-U', credentials.get('user', 'postgres'), '-l', '-t']
            elif db_type == 'mysql':
                cmd = ['mysql', '-u', credentials.get('user', 'root'), '-e', 'SHOW DATABASES;']
            elif db_type == 'mongodb':
                cmd = ['mongo', '--eval', 'db.adminCommand("listDatabases").databases.forEach(function(db) { print(db.name) })']
            else:
                return []
            
            if credentials.get('password'):
                if db_type == 'postgresql':
                    env = {'PGPASSWORD': credentials['password']}
                elif db_type == 'mysql':
                    cmd.extend(['-p' + credentials['password']])
                    env = {}
                else:
                    env = {}
            else:
                env = {}
            
            result = container.exec_run(cmd, environment=env)
            if result.exit_code == 0:
                output = result.output.decode('utf-8')
                
                if db_type == 'postgresql':
                    for line in output.split('\n'):
                        if '|' in line:
                            db_name = line.split('|')[0].strip()
                            if db_name and db_name not in ['template0', 'template1']:
                                databases.append(db_name)
                
                elif db_type == 'mysql':
                    for line in output.split('\n'):
                        db_name = line.strip()
                        if db_name and db_name not in ['Database', 'information_schema', 'performance_schema', 'mysql', 'sys']:
                            databases.append(db_name)
                
                elif db_type == 'mongodb':
                    for line in output.split('\n'):
                        db_name = line.strip()
                        if db_name and db_name not in ['admin', 'local', 'config']:
                            databases.append(db_name)
                            
        except Exception as e:
            logging.warning(f"Не удалось получить список БД в контейнере {container.name}: {e}")
        
        return databases

    def scan_network_ports(self):
        """Сканирование сетевых портов для обнаружения СУБД"""
        logging.info("Сканирование сетевых портов...")
        
        port_databases = []
        
        # Получение всех открытых портов
        open_ports = self._get_open_ports()
        
        # Стандартные порты СУБД для приоритетного сканирования
        priority_ports = {
            5432: 'postgresql',
            3306: 'mysql',
            27017: 'mongodb', 
            6379: 'redis',
            1521: 'oracle',
            1433: 'mssql',
            50000: 'db2',
            8086: 'influxdb',
            9200: 'elasticsearch',
            5984: 'couchdb'
        }
        
        # Сначала проверяем стандартные порты БД
        for port, expected_type in priority_ports.items():
            if port in open_ports:
                db_info = self._probe_database_port('localhost', port, expected_type)
                if db_info:
                    port_databases.append(db_info)
                    logging.info(f"Обнаружена {expected_type} на порту {port}")
        
        # Затем проверяем все остальные открытые порты
        for port in open_ports:
            if port not in priority_ports:
                # Пытаемся определить тип БД по баннеру/отклику
                db_info = self._probe_unknown_port('localhost', port)
                if db_info:
                    port_databases.append(db_info)
                    logging.info(f"Обнаружена БД {db_info['type']} на порту {port}")
        
        logging.info(f"Обнаружено {len(port_databases)} БД через сканирование портов")
        return port_databases

    def _get_open_ports(self):
        """Получение списка всех открытых портов"""
        open_ports = set()
        
        try:
            # Используем psutil для получения сетевых соединений
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.status == 'LISTEN' and conn.laddr:
                    port = conn.laddr.port
                    # Исключаем системные порты < 1024 (кроме известных БД)
                    if port >= 1024 or port in [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]:
                        continue
                    if port in [5432, 3306, 27017, 6379, 1521, 1433, 50000, 8086, 9200, 5984]:
                        open_ports.add(port)
                    elif port >= 1024:
                        open_ports.add(port)
            
            # Дополнительно сканируем стандартные порты БД, даже если psutil их не видит
            standard_db_ports = [5432, 3306, 27017, 6379, 1521, 1433, 50000, 8086, 9200, 5984]
            for port in standard_db_ports:
                if self._is_port_open('localhost', port):
                    open_ports.add(port)
                    
        except Exception as e:
            logging.error(f"Ошибка получения открытых портов: {e}")
        
        return open_ports

    def _is_port_open(self, host, port):
        """Проверка, открыт ли порт"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                return result == 0
        except:
            return False

    def _probe_database_port(self, host, port, expected_type):
        """Проверка конкретного порта на наличие ожидаемой СУБД"""
        try:
            if expected_type == 'postgresql':
                return self._probe_postgresql(host, port)
            elif expected_type == 'mysql':
                return self._probe_mysql(host, port)
            elif expected_type == 'mongodb':
                return self._probe_mongodb(host, port)
            elif expected_type == 'redis':
                return self._probe_redis(host, port)
            elif expected_type == 'oracle':
                return self._probe_oracle(host, port)
            elif expected_type == 'mssql':
                return self._probe_mssql(host, port)
            else:
                return None
        except Exception as e:
            logging.debug(f"Ошибка проверки {expected_type} на {host}:{port}: {e}")
            return None

    def _probe_unknown_port(self, host, port):
        """Определение типа БД на неизвестном порту"""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((host, port))
                
                # Отправляем пустой запрос и анализируем ответ
                try:
                    sock.send(b'\n')
                    response = sock.recv(1024)
                    
                    response_str = response.decode('utf-8', errors='ignore').lower()
                    
                    # Анализ баннеров/откликов
                    if 'postgresql' in response_str or 'postgres' in response_str:
                        return self._probe_postgresql(host, port)
                    elif 'mysql' in response_str or 'mariadb' in response_str:
                        return self._probe_mysql(host, port)
                    elif 'mongodb' in response_str or 'mongo' in response_str:
                        return self._probe_mongodb(host, port)
                    elif '+pong' in response_str or 'redis' in response_str:
                        return self._probe_redis(host, port)
                    elif 'elasticsearch' in response_str:
                        return self._probe_elasticsearch(host, port)
                    elif 'couchdb' in response_str:
                        return self._probe_couchdb(host, port)
                        
                except:
                    pass
                    
        except Exception as e:
            logging.debug(f"Не удалось определить тип БД на {host}:{port}: {e}")
        
        return None

    def _probe_postgresql(self, host, port):
        """Проверка PostgreSQL"""
        try:
            # Пытаемся подключиться к PostgreSQL
            import subprocess
            
            # Проверяем подключение без пароля
            cmd = ['psql', '-h', host, '-p', str(port), '-U', 'postgres', '-d', 'template1', '-c', '\\l', '-t']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                                  env={**os.environ, 'PGPASSWORD': ''})
            
            databases = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '|' in line:
                        db_name = line.split('|')[0].strip()
                        if db_name and db_name not in ['template0', 'template1']:
                            databases.append(db_name)
            
            return {
                'type': 'postgresql',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': databases,
                'connection_tested': result.returncode == 0,
                'auth_method': 'trust' if result.returncode == 0 else 'required'
            }
            
        except Exception as e:
            logging.debug(f"Ошибка проверки PostgreSQL {host}:{port}: {e}")
            # Возвращаем базовую информацию даже если не удалось получить список БД
            return {
                'type': 'postgresql',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': [],
                'connection_tested': False,
                'auth_method': 'unknown'
            }

    def _probe_mysql(self, host, port):
        """Проверка MySQL/MariaDB"""
        try:
            import subprocess
            
            # Пытаемся подключиться к MySQL
            cmd = ['mysql', '-h', host, '-P', str(port), '-u', 'root', '-e', 'SHOW DATABASES;']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            databases = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    db_name = line.strip()
                    if db_name and db_name not in ['Database', 'information_schema', 'performance_schema', 'mysql', 'sys']:
                        databases.append(db_name)
            
            return {
                'type': 'mysql',
                'source': 'network_scan', 
                'host': host,
                'port': port,
                'databases': databases,
                'connection_tested': result.returncode == 0,
                'auth_method': 'no_password' if result.returncode == 0 else 'required'
            }
            
        except Exception as e:
            logging.debug(f"Ошибка проверки MySQL {host}:{port}: {e}")
            return {
                'type': 'mysql',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': [],
                'connection_tested': False,
                'auth_method': 'unknown'
            }

    def _probe_mongodb(self, host, port):
        """Проверка MongoDB"""
        try:
            import subprocess
            
            # Пытаемся подключиться к MongoDB
            cmd = ['mongo', '--host', f"{host}:{port}", '--eval', 
                   'db.adminCommand("listDatabases").databases.forEach(function(db) { print(db.name) })', 
                   '--quiet']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            databases = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    db_name = line.strip()
                    if db_name and db_name not in ['admin', 'local', 'config']:
                        databases.append(db_name)
            
            return {
                'type': 'mongodb',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': databases,
                'connection_tested': result.returncode == 0,
                'auth_method': 'no_auth' if result.returncode == 0 else 'required'
            }
            
        except Exception as e:
            logging.debug(f"Ошибка проверки MongoDB {host}:{port}: {e}")
            return {
                'type': 'mongodb',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': [],
                'connection_tested': False,
                'auth_method': 'unknown'
            }

    def _probe_redis(self, host, port):
        """Проверка Redis"""
        try:
            import subprocess
            
            # Пытаемся подключиться к Redis
            cmd = ['redis-cli', '-h', host, '-p', str(port), 'ping']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'PONG' in result.stdout:
                # Получаем информацию о Redis
                info_cmd = ['redis-cli', '-h', host, '-p', str(port), 'info', 'keyspace']
                info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=5)
                
                databases = []
                if info_result.returncode == 0:
                    for line in info_result.stdout.split('\n'):
                        if line.startswith('db'):
                            db_num = line.split(':')[0]
                            databases.append(db_num)
                
                if not databases:
                    databases = ['db0']  # По умолчанию Redis использует db0
                
                return {
                    'type': 'redis',
                    'source': 'network_scan',
                    'host': host,
                    'port': port,
                    'databases': databases,
                    'connection_tested': True,
                    'auth_method': 'no_auth'
                }
            
        except Exception as e:
            logging.debug(f"Ошибка проверки Redis {host}:{port}: {e}")
        
        return None

    def _probe_elasticsearch(self, host, port):
        """Проверка Elasticsearch"""
        try:
            import requests
            
            # Проверяем Elasticsearch API
            response = requests.get(f'http://{host}:{port}/', timeout=5)
            if response.status_code == 200 and 'elasticsearch' in response.text.lower():
                
                # Получаем список индексов
                indices_response = requests.get(f'http://{host}:{port}/_cat/indices?format=json', timeout=5)
                databases = []
                if indices_response.status_code == 200:
                    indices = indices_response.json()
                    databases = [idx['index'] for idx in indices if not idx['index'].startswith('.')]
                
                return {
                    'type': 'elasticsearch',
                    'source': 'network_scan',
                    'host': host,
                    'port': port,
                    'databases': databases,
                    'connection_tested': True,
                    'auth_method': 'no_auth'
                }
                
        except Exception as e:
            logging.debug(f"Ошибка проверки Elasticsearch {host}:{port}: {e}")
        
        return None

    def _probe_couchdb(self, host, port):
        """Проверка CouchDB"""
        try:
            import requests
            
            # Проверяем CouchDB API
            response = requests.get(f'http://{host}:{port}/', timeout=5)
            if response.status_code == 200 and 'couchdb' in response.text.lower():
                
                # Получаем список баз данных
                dbs_response = requests.get(f'http://{host}:{port}/_all_dbs', timeout=5)
                databases = []
                if dbs_response.status_code == 200:
                    databases = [db for db in dbs_response.json() if not db.startswith('_')]
                
                return {
                    'type': 'couchdb',
                    'source': 'network_scan',
                    'host': host,
                    'port': port,
                    'databases': databases,
                    'connection_tested': True,
                    'auth_method': 'no_auth'
                }
                
        except Exception as e:
            logging.debug(f"Ошибка проверки CouchDB {host}:{port}: {e}")
        
        return None

    def _probe_oracle(self, host, port):
        """Проверка Oracle Database"""
        try:
            # Oracle требует специальный клиент, возвращаем базовую информацию
            return {
                'type': 'oracle',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': [],
                'connection_tested': False,
                'auth_method': 'unknown',
                'note': 'Oracle detected by port, manual configuration required'
            }
        except Exception as e:
            logging.debug(f"Ошибка проверки Oracle {host}:{port}: {e}")
        
        return None

    def _probe_mssql(self, host, port):
        """Проверка Microsoft SQL Server"""
        try:
            # SQL Server требует специальный клиент, возвращаем базовую информацию
            return {
                'type': 'mssql',
                'source': 'network_scan',
                'host': host,
                'port': port,
                'databases': [],
                'connection_tested': False,
                'auth_method': 'unknown',
                'note': 'SQL Server detected by port, manual configuration required'
            }
        except Exception as e:
            logging.debug(f"Ошибка проверки SQL Server {host}:{port}: {e}")
        
        return None

    def discover_all_databases(self):
        """Обнаружение всех баз данных"""
        logging.info("=" * 60)
        logging.info("Начало полного обнаружения баз данных")
        logging.info("=" * 60)
        
        self.discovered_databases = []
        
        # 1. Сканирование сетевых портов (приоритет)
        logging.info("🔍 Этап 1: Сканирование сетевых портов")
        port_dbs = self.scan_network_ports()
        self.discovered_databases.extend(port_dbs)
        
        # 2. Системные процессы БД
        logging.info("🖥️ Этап 2: Анализ системных процессов")
        system_dbs = self.discover_system_databases()
        self.discovered_databases.extend(system_dbs)
        
        # 3. Docker контейнеры
        logging.info("🐳 Этап 3: Сканирование Docker контейнеров")
        docker_dbs = self.discover_docker_databases()
        self.discovered_databases.extend(docker_dbs)
        
        # 4. Удаление дубликатов
        self._remove_duplicate_databases()
        
        logging.info("=" * 60)
        logging.info(f"Обнаружение завершено: {len(self.discovered_databases)} уникальных БД")
        logging.info("=" * 60)
        
        # Сохранение подробного отчета
        self._save_discovery_report()
        self._print_discovery_summary()
        
        return self.discovered_databases

    def _remove_duplicate_databases(self):
        """Удаление дубликатов БД"""
        unique_dbs = []
        seen = set()
        
        for db in self.discovered_databases:
            # Создаем ключ для идентификации уникальной БД
            key = f"{db['type']}:{db.get('host', 'localhost')}:{db.get('port', 'unknown')}"
            
            if key not in seen:
                seen.add(key)
                unique_dbs.append(db)
            else:
                # Объединяем информацию из разных источников
                existing_db = next(d for d in unique_dbs if 
                                 f"{d['type']}:{d.get('host', 'localhost')}:{d.get('port', 'unknown')}" == key)
                
                # Объединяем списки баз данных
                existing_databases = set(existing_db.get('databases', []))
                new_databases = set(db.get('databases', []))
                existing_db['databases'] = list(existing_databases.union(new_databases))
                
                # Обновляем источники
                sources = existing_db.get('sources', [existing_db.get('source', 'unknown')])
                if db.get('source') not in sources:
                    sources.append(db.get('source'))
                existing_db['sources'] = sources
        
        self.discovered_databases = unique_dbs
        logging.info(f"После удаления дубликатов: {len(unique_dbs)} уникальных БД")

    def _print_discovery_summary(self):
        """Вывод краткого отчета об обнаружении"""
        logging.info("\n📊 КРАТКИЙ ОТЧЕТ ОБ ОБНАРУЖЕНИИ:")
        
        by_type = {}
        by_source = {}
        total_databases = 0
        
        for db in self.discovered_databases:
            db_type = db['type']
            sources = db.get('sources', [db.get('source', 'unknown')])
            databases_count = len(db.get('databases', []))
            
            by_type[db_type] = by_type.get(db_type, 0) + 1
            total_databases += databases_count
            
            for source in sources:
                by_source[source] = by_source.get(source, 0) + 1
        
        logging.info(f"📈 Всего СУБД: {len(self.discovered_databases)}")
        logging.info(f"📊 Всего баз данных: {total_databases}")
        
        logging.info("\n🔧 По типам СУБД:")
        for db_type, count in sorted(by_type.items()):
            logging.info(f"  {db_type}: {count}")
        
        logging.info("\n🔍 По источникам обнаружения:")
        for source, count in sorted(by_source.items()):
            logging.info(f"  {source}: {count}")
        
        logging.info("\n💾 Подробный отчет сохранен в discovery_report_*.json")

    def _save_discovery_report(self):
        """Сохранение отчета об обнаруженных БД"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.BACKUP_DIR, f'discovery_report_{timestamp}.json')
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.discovered_databases, f, indent=2, ensure_ascii=False, default=str)
            logging.info(f"Отчет об обнаружении сохранен: {report_file}")
        except Exception as e:
            logging.error(f"Ошибка сохранения отчета: {e}")

    def backup_database(self, db_info):
        """Создание резервной копии отдельной БД"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if db_info['source'] == 'system':
            return self._backup_system_database(db_info, timestamp)
        elif db_info['source'] == 'docker':
            return self._backup_docker_database(db_info, timestamp)
        
        return None

    def backup_database(self, db_info):
        """Создание резервной копии отдельной БД"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if db_info['source'] == 'system' or db_info['source'] == 'network_scan':
            return self._backup_system_database(db_info, timestamp)
        elif db_info['source'] == 'docker':
            return self._backup_docker_database(db_info, timestamp)
        
        return None

    def _backup_system_database(self, db_info, timestamp):
        """Резервное копирование системной БД"""
        backups = []
        
        # Если нет баз данных для резервного копирования, пропускаем
        if not db_info.get('databases'):
            logging.warning(f"Нет баз данных для резервного копирования в {db_info['type']} на {db_info.get('host', 'localhost')}:{db_info.get('port', 'unknown')}")
            return backups
        
        for database in db_info.get('databases', []):
            try:
                if db_info['type'] == 'postgresql':
                    backup_file = f"pg_{db_info.get('host', 'localhost')}_{db_info.get('port', 5432)}_{database}_{timestamp}.sql"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                    
                    cmd = [
                        'pg_dump',
                        '-h', db_info.get('host', 'localhost'),
                        '-p', str(db_info.get('port', 5432)),
                        '-U', 'postgres',
                        '--format=custom',
                        '--no-password',
                        '--file', backup_path,
                        database
                    ]
                    
                    env = os.environ.copy()
                    # Пытаемся без пароля, потом с пустым паролем
                    env['PGPASSWORD'] = ''
                    
                elif db_info['type'] == 'mysql':
                    backup_file = f"mysql_{db_info.get('host', 'localhost')}_{db_info.get('port', 3306)}_{database}_{timestamp}.sql"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                    
                    cmd = [
                        'mysqldump',
                        '-h', db_info.get('host', 'localhost'),
                        '-P', str(db_info.get('port', 3306)),
                        '-u', 'root',
                        '--single-transaction',
                        '--routines',
                        '--triggers',
                        database
                    ]
                    
                    env = os.environ.copy()
                    
                    with open(backup_path, 'w') as f:
                        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
                        
                elif db_info['type'] == 'mongodb':
                    backup_dir = f"mongo_{db_info.get('host', 'localhost')}_{db_info.get('port', 27017)}_{database}_{timestamp}"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_dir)
                    os.makedirs(backup_path, exist_ok=True)
                    
                    cmd = [
                        'mongodump',
                        '--host', f"{db_info.get('host', 'localhost')}:{db_info.get('port', 27017)}",
                        '--db', database,
                        '--out', backup_path
                    ]
                    
                    env = os.environ.copy()
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                    
                elif db_info['type'] == 'redis':
                    backup_file = f"redis_{db_info.get('host', 'localhost')}_{db_info.get('port', 6379)}_{database}_{timestamp}.rdb"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                    
                    # Для Redis используем BGSAVE и копируем RDB файл
                    cmd = [
                        'redis-cli',
                        '-h', db_info.get('host', 'localhost'),
                        '-p', str(db_info.get('port', 6379)),
                        'BGSAVE'
                    ]
                    
                    env = os.environ.copy()
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                    
                    if result.returncode == 0:
                        # Ждем завершения BGSAVE
                        import time
                        time.sleep(5)
                        
                        # Копируем RDB файл
                        try:
                            # Пытаемся найти RDB файл Redis
                            rdb_locations = [
                                '/var/lib/redis/dump.rdb',
                                '/var/redis/dump.rdb', 
                                '/usr/local/var/db/redis/dump.rdb',
                                '/data/dump.rdb'
                            ]
                            
                            for rdb_path in rdb_locations:
                                if os.path.exists(rdb_path):
                                    import shutil
                                    shutil.copy2(rdb_path, backup_path)
                                    break
                        except Exception as e:
                            logging.error(f"Ошибка копирования RDB файла: {e}")
                            continue
                
                elif db_info['type'] == 'sqlite':
                    backup_file = f"sqlite_{os.path.basename(db_info['file_path'])}_{timestamp}.db"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                    
                    # Простое копирование файла SQLite
                    import shutil
                    shutil.copy2(db_info['file_path'], backup_path)
                    backups.append(backup_path)
                    continue
                
                elif db_info['type'] == 'elasticsearch':
                    # Elasticsearch snapshot через API
                    backup_file = f"elasticsearch_{db_info.get('host', 'localhost')}_{db_info.get('port', 9200)}_{database}_{timestamp}.json"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                    
                    try:
                        import requests
                        # Экспорт индекса
                        url = f"http://{db_info.get('host', 'localhost')}:{db_info.get('port', 9200)}/{database}/_search"
                        params = {'size': 10000, 'scroll': '1m'}
                        response = requests.get(url, params=params, timeout=30)
                        
                        if response.status_code == 200:
                            with open(backup_path, 'w') as f:
                                json.dump(response.json(), f, indent=2)
                            backups.append(backup_path)
                            logging.info(f"Создана резервная копия Elasticsearch: {backup_path}")
                        continue
                    except Exception as e:
                        logging.error(f"Ошибка резервного копирования Elasticsearch {database}: {e}")
                        continue
                
                elif db_info['type'] == 'couchdb':
                    # CouchDB replication/export
                    backup_file = f"couchdb_{db_info.get('host', 'localhost')}_{db_info.get('port', 5984)}_{database}_{timestamp}.json"
                    backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                    
                    try:
                        import requests
                        # Экспорт базы данных
                        url = f"http://{db_info.get('host', 'localhost')}:{db_info.get('port', 5984)}/{database}/_all_docs"
                        params = {'include_docs': True}
                        response = requests.get(url, params=params, timeout=30)
                        
                        if response.status_code == 200:
                            with open(backup_path, 'w') as f:
                                json.dump(response.json(), f, indent=2)
                            backups.append(backup_path)
                            logging.info(f"Создана резервная копия CouchDB: {backup_path}")
                        continue
                    except Exception as e:
                        logging.error(f"Ошибка резервного копирования CouchDB {database}: {e}")
                        continue
                
                else:
                    logging.warning(f"Резервное копирование {db_info['type']} не поддерживается")
                    continue
                
                # Выполнение команды для PostgreSQL, MySQL, MongoDB, Redis
                if db_info['type'] in ['postgresql', 'mongodb', 'redis'] and db_info['type'] != 'mysql':
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    logging.info(f"Создана резервная копия: {backup_path}")
                    backups.append(backup_path)
                else:
                    logging.error(f"Ошибка создания резервной копии {database}: {result.stderr}")
                    
            except Exception as e:
                logging.error(f"Ошибка резервного копирования {database}: {e}")
        
        return backups

    def _backup_docker_database(self, db_info, timestamp):
        """Резервное копирование БД в Docker"""
        backups = []
        
        try:
            container = self.docker_client.containers.get(db_info['container_id'])
            credentials = db_info.get('credentials', {})
            
            for database in db_info.get('databases', []):
                try:
                    if db_info['type'] == 'postgresql':
                        backup_file = f"docker_pg_{db_info['container_name']}_{database}_{timestamp}.sql"
                        backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                        
                        cmd = [
                            'pg_dump',
                            '-U', credentials.get('user', 'postgres'),
                            '--format=custom',
                            database
                        ]
                        
                        env = {}
                        if credentials.get('password'):
                            env['PGPASSWORD'] = credentials['password']
                        
                    elif db_info['type'] == 'mysql':
                        backup_file = f"docker_mysql_{db_info['container_name']}_{database}_{timestamp}.sql"
                        backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                        
                        cmd = [
                            'mysqldump',
                            '-u', credentials.get('user', 'root'),
                            '--single-transaction',
                            '--routines',
                            '--triggers',
                            database
                        ]
                        
                        env = {}
                        if credentials.get('password'):
                            cmd.append(f"-p{credentials['password']}")
                    
                    elif db_info['type'] == 'mongodb':
                        backup_file = f"docker_mongo_{db_info['container_name']}_{database}_{timestamp}.archive"
                        backup_path = os.path.join(self.BACKUP_DIR, backup_file)
                        
                        cmd = [
                            'mongodump',
                            '--db', database,
                            '--archive'
                        ]
                        env = {}
                    
                    # Выполнение команды в контейнере
                    result = container.exec_run(cmd, environment=env)
                    
                    if result.exit_code == 0:
                        # Сохранение результата в файл
                        with open(backup_path, 'wb') as f:
                            f.write(result.output)
                        
                        logging.info(f"Создана резервная копия Docker: {backup_path}")
                        backups.append(backup_path)
                    else:
                        logging.error(f"Ошибка создания резервной копии Docker {database}: {result.output.decode()}")
                        
                except Exception as e:
                    logging.error(f"Ошибка резервного копирования Docker {database}: {e}")
                    
        except Exception as e:
            logging.error(f"Ошибка работы с контейнером {db_info['container_name']}: {e}")
        
        return backups

    def upload_to_drive(self, file_path):
        """Загрузка файла на Google Drive"""
        if not self.drive_service:
            logging.warning("Google Drive API недоступен")
            return False
        
        try:
            filename = os.path.basename(file_path)
            
            file_metadata = {
                'name': filename,
                'parents': [self.DRIVE_FOLDER_ID] if self.DRIVE_FOLDER_ID else []
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logging.info(f"Файл {filename} загружен на Google Drive. ID: {file.get('id')}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка загрузки на Google Drive: {e}")
            return False

    def cleanup_old_backups(self, keep_days=7):
        """Очистка старых резервных копий"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (keep_days * 24 * 60 * 60)
            
            for filename in os.listdir(self.BACKUP_DIR):
                file_path = os.path.join(self.BACKUP_DIR, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getctime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        logging.info(f"Удален старый файл: {filename}")
                        
        except Exception as e:
            logging.error(f"Ошибка очистки старых файлов: {e}")

    def run_full_backup(self):
        """Выполнение полного резервного копирования"""
        logging.info("=" * 80)
        logging.info("🚀 ЗАПУСК ПОЛНОГО РЕЗЕРВНОГО КОПИРОВАНИЯ")
        logging.info("=" * 80)
        
        start_time = datetime.now()
        
        # Этап 1: Обнаружение всех БД
        databases = self.discover_all_databases()
        
        if not databases:
            logging.warning("❌ Базы данных не обнаружены")
            return
        
        logging.info(f"\n💾 Начинаем резервное копирование {len(databases)} обнаруженных СУБД...")
        
        total_backups = 0
        successful_backups = 0
        successful_uploads = 0
        failed_backups = []
        
        # Этап 2: Создание резервных копий для каждой БД
        for i, db_info in enumerate(databases, 1):
            db_name = f"{db_info['type']} ({db_info.get('host', 'localhost')}:{db_info.get('port', 'unknown')})"
            logging.info(f"\n📦 [{i}/{len(databases)}] Резервное копирование: {db_name}")
            
            # Проверяем, есть ли базы данных для резервного копирования
            db_count = len(db_info.get('databases', []))
            if db_count == 0:
                logging.warning(f"⚠️ Нет баз данных для резервного копирования в {db_name}")
                continue
            
            logging.info(f"🗄️ Баз данных для резервного копирования: {db_count}")
            for db_name_item in db_info.get('databases', []):
                logging.info(f"   - {db_name_item}")
            
            try:
                backup_files = self.backup_database(db_info)
                
                if backup_files:
                    total_backups += len(backup_files)
                    successful_backups += len(backup_files)
                    
                    logging.info(f"✅ Создано {len(backup_files)} резервных копий")
                    
                    # Загрузка на Google Drive
                    if self.drive_service:
                        for backup_file in backup_files:
                            try:
                                if self.upload_to_drive(backup_file):
                                    successful_uploads += 1
                                    logging.info(f"☁️ Загружено на Google Drive: {os.path.basename(backup_file)}")
                                    
                                    # Удаление локального файла после успешной загрузки
                                    try:
                                        if os.path.isfile(backup_file):
                                            os.remove(backup_file)
                                        elif os.path.isdir(backup_file):
                                            import shutil
                                            shutil.rmtree(backup_file)
                                        logging.debug(f"🗑️ Локальный файл удален: {backup_file}")
                                    except Exception as e:
                                        logging.error(f"Ошибка удаления локального файла: {e}")
                                else:
                                    logging.error(f"❌ Ошибка загрузки на Google Drive: {os.path.basename(backup_file)}")
                            except Exception as e:
                                logging.error(f"❌ Ошибка обработки файла {backup_file}: {e}")
                    else:
                        logging.warning("⚠️ Google Drive API недоступен, файлы сохранены локально")
                else:
                    logging.error(f"❌ Не удалось создать резервные копии для {db_name}")
                    failed_backups.append(db_name)
                    
            except Exception as e:
                logging.error(f"❌ Критическая ошибка при резервном копировании {db_name}: {e}")
                failed_backups.append(db_name)
        
        # Этап 3: Очистка старых файлов
        logging.info("\n🧹 Очистка старых резервных копий...")
        self.cleanup_old_backups()
        
        # Этап 4: Итоговая статистика
        end_time = datetime.now()
        duration = end_time - start_time
        
        logging.info("=" * 80)
        logging.info("📊 ИТОГОВАЯ СТАТИСТИКА РЕЗЕРВНОГО КОПИРОВАНИЯ")
        logging.info("=" * 80)
        logging.info(f"⏱️ Время выполнения: {duration}")
        logging.info(f"🔍 СУБД обнаружено: {len(databases)}")
        logging.info(f"💾 Резервных копий создано: {successful_backups}/{total_backups}")
        logging.info(f"☁️ Файлов загружено на Drive: {successful_uploads}")
        
        if failed_backups:
            logging.warning(f"❌ Ошибки резервного копирования ({len(failed_backups)}):")
            for failed in failed_backups:
                logging.warning(f"   - {failed}")
        else:
            logging.info("✅ Все резервные копии созданы успешно!")
        
        # Сохранение статистики
        self._save_backup_statistics({
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'databases_discovered': len(databases),
            'backups_created': successful_backups,
            'backups_uploaded': successful_uploads,
            'failed_backups': failed_backups,
            'success_rate': (successful_backups / total_backups * 100) if total_backups > 0 else 0
        })
        
        logging.info("=" * 80)

    def _save_backup_statistics(self, stats):
        """Сохранение статистики резервного копирования"""
        try:
            stats_file = os.path.join(self.BACKUP_DIR, 'backup_statistics.json')
            
            # Загружаем существующую статистику
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    all_stats = json.load(f)
            else:
                all_stats = []
            
            # Добавляем новую статистику
            all_stats.append(stats)
            
            # Сохраняем только последние 100 записей
            all_stats = all_stats[-100:]
            
            # Записываем обратно
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_stats, f, indent=2, ensure_ascii=False)
                
            logging.debug(f"Статистика сохранена в {stats_file}")
            
        except Exception as e:
            logging.error(f"Ошибка сохранения статистики: {e}")

    def generate_discovery_report(self):
        """Генерация детального отчета об обнаружении БД"""
        if not self.discovered_databases:
            logging.info("Сначала выполните обнаружение баз данных")
            return
        
        logging.info("\n" + "=" * 80)
        logging.info("📋 ДЕТАЛЬНЫЙ ОТЧЕТ ОБ ОБНАРУЖЕНИИ БД")
        logging.info("=" * 80)
        
        for i, db in enumerate(self.discovered_databases, 1):
            logging.info(f"\n🔹 [{i}] {db['type'].upper()}")
            logging.info(f"   📍 Расположение: {db.get('host', 'localhost')}:{db.get('port', 'N/A')}")
            logging.info(f"   🔍 Источник обнаружения: {', '.join(db.get('sources', [db.get('source', 'unknown')]))}")
            
            if db.get('connection_tested'):
                status = "✅ Подключение успешно" 
            elif db.get('connection_tested') is False:
                status = "❌ Ошибка подключения"
            else:
                status = "❓ Подключение не тестировалось"
            logging.info(f"   🔗 {status}")
            
            if db.get('auth_method'):
                logging.info(f"   🔐 Аутентификация: {db['auth_method']}")
            
            databases = db.get('databases', [])
            if databases:
                logging.info(f"   💾 Баз данных ({len(databases)}):")
                for db_name in databases:
                    logging.info(f"      - {db_name}")
            else:
                logging.info(f"   💾 Баз данных: не обнаружено")
            
            if db.get('note'):
                logging.info(f"   📝 Примечание: {db['note']}")
            
            # Дополнительная информация для Docker
            if db.get('source') == 'docker':
                logging.info(f"   🐳 Контейнер: {db.get('container_name', 'N/A')}")
                logging.info(f"   📦 Образ: {db.get('image', 'N/A')}")
            
            # Дополнительная информация для SQLite
            if db.get('type') == 'sqlite':
                file_path = db.get('file_path', 'N/A')
                file_size = db.get('size', 0)
                logging.info(f"   📁 Файл: {file_path}")
                logging.info(f"   📏 Размер: {file_size / 1024 / 1024:.2f} MB")
        
        logging.info("=" * 80)

    def test_database_connections(self):
        """Тестирование подключений ко всем обнаруженным БД"""
        if not self.discovered_databases:
            logging.info("Сначала выполните обнаружение баз данных")
            return
        
        logging.info("\n🧪 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЙ К БД")
        logging.info("=" * 50)
        
        success_count = 0
        total_count = len(self.discovered_databases)
        
        for db in self.discovered_databases:
            db_name = f"{db['type']} ({db.get('host', 'localhost')}:{db.get('port', 'N/A')})"
            
            try:
                if db['type'] == 'postgresql':
                    success = self._test_postgresql_connection(db)
                elif db['type'] == 'mysql':
                    success = self._test_mysql_connection(db)
                elif db['type'] == 'mongodb':
                    success = self._test_mongodb_connection(db)
                elif db['type'] == 'redis':
                    success = self._test_redis_connection(db)
                elif db['type'] == 'sqlite':
                    success = os.path.exists(db.get('file_path', ''))
                else:
                    success = False
                    
                if success:
                    logging.info(f"✅ {db_name}")
                    success_count += 1
                else:
                    logging.error(f"❌ {db_name}")
                    
            except Exception as e:
                logging.error(f"❌ {db_name}: {e}")
        
        logging.info("=" * 50)
        logging.info(f"📊 Результат: {success_count}/{total_count} успешных подключений")

    def _test_postgresql_connection(self, db):
        """Тест подключения к PostgreSQL"""
        try:
            cmd = ['psql', '-h', db.get('host', 'localhost'), '-p', str(db.get('port', 5432)),
                   '-U', 'postgres', '-d', 'template1', '-c', 'SELECT version();']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5,
                                  env={**os.environ, 'PGPASSWORD': ''})
            return result.returncode == 0
        except:
            return False

    def _test_mysql_connection(self, db):
        """Тест подключения к MySQL"""
        try:
            cmd = ['mysql', '-h', db.get('host', 'localhost'), '-P', str(db.get('port', 3306)),
                   '-u', 'root', '-e', 'SELECT VERSION();']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _test_mongodb_connection(self, db):
        """Тест подключения к MongoDB"""
        try:
            cmd = ['mongo', '--host', f"{db.get('host', 'localhost')}:{db.get('port', 27017)}",
                   '--eval', 'db.version()', '--quiet']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _test_redis_connection(self, db):
        """Тест подключения к Redis"""
        try:
            cmd = ['redis-cli', '-h', db.get('host', 'localhost'), '-p', str(db.get('port', 6379)), 'ping']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and 'PONG' in result.stdout
        except:
            return False

def main():
    """Основная функция"""
    import argparse
    
    # Отображение логотипа при запуске
    print_logo()
    
    parser = argparse.ArgumentParser(description='DumpItAll - Универсальная система резервного копирования БД')
    parser.add_argument('--scan-only', action='store_true', 
                       help='Только сканирование и обнаружение БД без резервного копирования')
    parser.add_argument('--test-connections', action='store_true',
                       help='Тестирование подключений к обнаруженным БД')
    parser.add_argument('--backup-once', action='store_true',
                       help='Однократное резервное копирование без планировщика')
    parser.add_argument('--daemon', action='store_true',
                       help='Запуск в режиме демона с планировщиком')
    parser.add_argument('--interval', type=int, default=30,
                       help='Интервал резервного копирования в минутах (по умолчанию: 30)')
    parser.add_argument('--config', type=str, default='.env',
                       help='Путь к файлу конфигурации (по умолчанию: .env)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Уровень логирования')
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Загрузка конфигурации
    if os.path.exists(args.config):
        from dotenv import load_dotenv
        load_dotenv(args.config)
    
    backup_manager = UniversalBackup()
    
    if args.scan_only:
        # Только сканирование
        logging.info("🔍 Режим: только сканирование БД")
        backup_manager.discover_all_databases()
        backup_manager.generate_discovery_report()
        
    elif args.test_connections:
        # Тестирование подключений
        logging.info("🧪 Режим: тестирование подключений")
        backup_manager.discover_all_databases()
        backup_manager.test_database_connections()
        
    elif args.backup_once:
        # Однократное резервное копирование
        logging.info("💾 Режим: однократное резервное копирование")
        backup_manager.run_full_backup()
        
    else:
        # Режим демона с планировщиком (по умолчанию)
        logging.info("🤖 Режим: демон с автоматическим резервным копированием")
        
        # Планирование выполнения
        schedule.every(args.interval).minutes.do(backup_manager.run_full_backup)
        
        logging.info(f"🗄️ DumpItAll служба запущена")
        logging.info(f"Резервное копирование каждые {args.interval} минут")
        
        # Выполнение первого обнаружения и бэкапа
        backup_manager.run_full_backup()
        
        # Основной цикл
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Проверка каждую минуту
        except KeyboardInterrupt:
            logging.info("Демон остановлен пользователем")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Служба остановлена пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        import traceback
        logging.error(traceback.format_exc())
