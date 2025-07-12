# 🚀 DumpItAll - Быстрый старт

## От 0 до работающей системы за 5 минут

## Шаг 1: Установка (1 минута)
```bash
# Скачивание DumpItAll
curl -O https://raw.githubusercontent.com/your-username/DumpItAll/main/backup_script.py
curl -O https://raw.githubusercontent.com/your-username/DumpItAll/main/requirements.txt

# Установка зависимостей
pip3 install -r requirements.txt
```

## Шаг 2: Первое сканирование (30 секунд)
```bash
# Обнаружение всех БД в системе
python3 backup_script.py --scan-only
```

**Результат:** Увидите список всех найденных баз данных

## Шаг 3: Проверка подключений (30 секунд)
```bash
# Тестирование доступа к БД
python3 backup_script.py --test-connections
```

**Результат:** ✅/❌ статус подключения к каждой БД

## Шаг 4: Настройка Google Drive (2 минуты)
```bash
# Создание .env файла
echo "DRIVE_FOLDER_ID=your_folder_id_here" > .env
echo "BACKUP_DIR=./backups" >> .env

# Получение Service Account ключа
# 1. Перейти в Google Cloud Console
# 2. Создать Service Account
# 3. Скачать JSON ключ как service-account-key.json
```

## Шаг 5: Пробное резервное копирование (1 минута)
```bash
# Создание резервных копий всех найденных БД
python3 backup_script.py --backup-once
```

**Результат:** Резервные копии всех БД на Google Drive!

## 🎉 Готово! Запуск автоматического режима
```bash
# Автоматическое резервное копирование каждые 30 минут
python3 backup_script.py --daemon
```

---

## 🔍 Что будет обнаружено автоматически:

### Системные БД
- ✅ PostgreSQL на порту 5432
- ✅ MySQL/MariaDB на порту 3306  
- ✅ MongoDB на порту 27017
- ✅ Redis на порту 6379
- ✅ SQLite файлы по всей системе

### Docker контейнеры
- ✅ postgres, mysql, mongo, redis образы
- ✅ Автоматическое извлечение паролей из ENV
- ✅ Получение списков баз данных

### Дополнительные СУБД
- ✅ Elasticsearch (порт 9200)
- ✅ CouchDB (порт 5984)
- ✅ Oracle, SQL Server (по портам)

---

## 📊 Мониторинг результатов

```bash
# Просмотр отчета обнаружения
cat backups/discovery_report_*.json | jq .

# Логи в реальном времени
tail -f backup.log

# Статистика резервного копирования
cat backups/backup_statistics.json | jq '.[-1]'
```

---

## 🛠️ Команды для отладки

```bash
# Детальное сканирование с отладкой
python3 backup_script.py --scan-only --log-level DEBUG

# Проверка Docker доступа
docker ps && python3 backup_script.py --scan-only

# Тест конкретной БД
python3 backup_script.py --test-connections --log-level DEBUG
```

---

## ⚙️ Production настройка

### Systemd сервис
```bash
# Копирование в production директорию
sudo mkdir -p /opt/db-backup
sudo cp backup_script.py /opt/db-backup/
sudo cp .env /opt/db-backup/
sudo cp service-account-key.json /opt/db-backup/

# Установка сервиса
sudo cp db-backup.service /etc/systemd/system/
sudo systemctl enable db-backup.service
sudo systemctl start db-backup.service
```

### Проверка статуса
```bash
sudo systemctl status db-backup.service
journalctl -u db-backup.service -f
```

---

## 🔧 Частые настройки

### Изменение интервала
```bash
# Каждые 15 минут
python3 backup_script.py --daemon --interval 15

# Каждый час
python3 backup_script.py --daemon --interval 60
```

### Кастомные пути
```bash
# Свой файл конфигурации
python3 backup_script.py --config /my/custom/.env --daemon

# Другая директория бэкапов
echo "BACKUP_DIR=/mnt/backups" >> .env
```

---

## 📋 Чек-лист готовности

- [ ] Скрипт скачан и зависимости установлены
- [ ] Команда `--scan-only` показывает найденные БД  
- [ ] Команда `--test-connections` показывает ✅ для нужных БД
- [ ] Google Drive API настроен (есть service-account-key.json)
- [ ] Команда `--backup-once` создает резервные копии
- [ ] Файлы появляются на Google Drive
- [ ] Демон `--daemon` работает в фоне

**Система готова к работе! 🎊**

---

## 🆘 Быстрая помощь

### БД не обнаруживается
```bash
# Проверка открытых портов
netstat -tulpn | grep -E "(5432|3306|27017|6379)"

# Проверка процессов
ps aux | grep -E "(postgres|mysql|mongo|redis)"
```

### Ошибки подключения
```bash
# Проверка доступности порта
telnet localhost 5432

# Проверка прав доступа
sudo -u postgres psql -c "\l"
```

### Docker недоступен  
```bash
# Добавление в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

**🎯 Цель:** За 5 минут получить автоматическое резервное копирование всех БД на сервере!
