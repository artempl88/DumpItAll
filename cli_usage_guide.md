# 🖥️ CLI Интерфейс универсальной системы резервного копирования

## Основные команды

### 🔍 Сканирование и обнаружение БД
```bash
# Только сканирование портов и обнаружение БД (без резервного копирования)
python3 backup_script.py --scan-only

# Сканирование с отладочными сообщениями
python3 backup_script.py --scan-only --log-level DEBUG
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
# 1. Сканирование системы
python3 backup_script.py --scan-only

# 2. Проверка подключений
python3 backup_script.py --test-connections

# 3. Тестовое резервное копирование
python3 backup_script.py --backup-once
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
| `--daemon` | Запуск демона с планировщиком | ✅ (по умолчанию) |
| `--interval N` | Интервал в минутах | 30 |
| `--config PATH` | Путь к файлу конфигурации | .env |
| `--log-level LEVEL` | Уровень логирования | INFO |

## 🔍 Что происходит при сканировании

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
# 1. Проверка конфигурации
python3 backup_script.py --scan-only --config /opt/db-backup/.env

# 2. Тест подключений
python3 backup_script.py --test-connections --config /opt/db-backup/.env

# 3. Пробное резервное копирование
python3 backup_script.py --backup-once --config /opt/db-backup/.env

# 4. Запуск демона
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

# Немедленное резервное копирование всех БД
python3 backup_script.py --backup-once --log-level INFO

# Запуск с высокой частотой для тестирования
python3 backup_script.py --daemon --interval 5 --log-level DEBUG
```
