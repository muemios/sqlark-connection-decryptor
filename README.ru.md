# Расшифровщик подключений SQLark

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Русский** · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Инструмент разбирает файлы подключений, сохранённые **SQLark (百灵)**
(`connectionInfo.xml` / `connection-server.xml`), и восстанавливает зашифрованные в них
пароли к базам данных.

> [!WARNING]
> Инструмент предназначен **только** для восстановления учётных данных, аудита паролей и
> самопроверки безопасности на собственных или доверенных компьютерах.
> Не используйте его на чужих компьютерах и базах данных без разрешения.
> См. [SECURITY.md](SECURITY.md).

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## Возможности

- **Автопоиск** в `~/.SQLark`, `%APPDATA%\SQLark`, на рабочем столе/в документах/загрузках
  и в каталогах установки SQLark на всех дисках;
- **Ручной выбор** каталога (рекурсивный поиск) или отдельных файлов;
- **Пакетная расшифровка**: имя подключения, хост, порт, пользователь, тип СУБД и пароль;
- **GUI + CLI**: приложение на Tkinter для повседневной работы, CLI для автоматизации;
- **Экспорт** в CSV (UTF-8 BOM, совместимо с Excel), TXT и JSON;
- **Полностью офлайн**: без сети, загрузок и записи в реестр;
- **Простая сборка** автономного `.exe` для Windows одной командой.

![Скриншот интерфейса](docs/images/gui-demo.png)

> Хосты, пользователи и пароли на скриншоте — демонстрационные данные
> (диапазоны RFC 5737 для документации).

---

## Быстрый старт

### 1. Скачать exe

Скачайте `sqlark-connection-decryptor-v*-windows-x64.exe` из [Releases](../../releases) и запустите двойным
щелчком — Python не нужен. Для скриптов используйте консольную сборку
`sqlark-connection-decryptor-cli-v*-windows-x64.exe`.

Сборки CLI для Linux и macOS также доступны в Releases (`linux-x64`, `linux-arm64`, `macos-arm64`, `macos-x64`).

### 2. Запуск из исходников

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # запуск GUI
```

### 3. Использование CLI

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

Пример вывода:

```
Подключение     Хост            Порт    Пользователь  СУБД          Пароль
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Сборка Windows-exe

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# результат: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## Поддерживаемые файлы

| Файл | Описание |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | Все локальные подключения SQLark (обычный случай) |
| Любой экспортированный `connection-server.xml` | Создаётся кнопкой «Экспорт подключений» |
| `connections.xml` и аналогичные | Любой файл с корневым элементом `<CONNECTIONS>` |

Проверено на **SQLark 4.x** (драйверы Oracle / MySQL / PostgreSQL / DM). Если производитель
сменит шифрование, инструмент явно завершится ошибкой, а не вернёт неверный пароль.

---

## Как это устроено

SQLark использует **два слоя AES-128-CBC (PKCS5Padding)**:

1. **Внешний слой** — всё поле `<connectionDetail>` / `<superAttr>`
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **Внутренний слой** — `password` / `sshPassword` / `sslPassword` внутри JSON
   `Base64(AES(открытый текст, key=salt, iv=reverse(salt)))`, где `salt` — случайная
   строка из 16 символов, хранящаяся рядом с шифртекстом.

Полные заметки по реверс-инжинирингу, классы Java и оценка безопасности —
в [docs/encryption.md](docs/encryption.md) (на китайском).

---

## Структура проекта

```
sqlark-decryptor/
├── sqlark_decrypt/          # переиспользуемый пакет Python
│   ├── crypto.py            # примитивы двухслойного AES
│   ├── parser.py            # разбор XML + композиция слоёв
│   ├── scanner.py           # поиск файлов
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # подкоманды gui / scan / decrypt
│   └── gui.py               # интерфейс Tkinter
├── tests/                   # 34 модульных теста, только синтетические данные
├── scripts/                 # сборка, демо-данные, иконка, проверка секретов
├── docs/                    # шифрование, архитектура, разработка, релиз
├── .github/workflows/       # CI и автозапуск релиза по тегу
└── pyproject.toml
```

---

## Разработка

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # проверка ссылок в переведённых README
```

- Тестовые данные создаёт `scripts/make_fixture.py`; они полностью вымышлены
  (диапазоны IP для документации + демонстрационные пароли).
- Правила участия: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Конфиденциальность и безопасность данных

- Нет сетевых запросов, загрузок и изменений файлов SQLark;
- Результат может содержать **пароли продуктивных баз данных**: не коммитьте их,
  не выкладывайте в облака и не вставляйте в тикеты;
- В репозитории есть `.gitignore` для реальных файлов подключений и
  `scripts/check_no_secrets.py` (запускается и в CI).

---

## FAQ

**Автопоиск ничего не находит** → нажмите «Выбрать папку» и укажите `C:\Users\<вы>\.SQLark`.

**Столбец пароля пуст** → подключение сохранено без «запомнить пароль».

**Разбор завершается ошибкой** → возможно, SQLark сменил шифрование. Создайте issue с версией
SQLark (**никогда не прикладывайте реальный файл подключения**).

---

## Лицензия

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## Ключевые слова

Расшифровка паролей SQLark, восстановление паролей SQLark 百灵, восстановление паролей
подключений к БД, сохранённые пароли Oracle / MySQL / PostgreSQL / DM, реверс-инжиниринг
AES-128-CBC, восстановление учётных данных, аудит безопасности, инструмент Tkinter,
офлайн-аудит паролей, connectionInfo.xml, connection-server.xml.
