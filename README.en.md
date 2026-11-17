# SQLark Connection Decryptor

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · **English** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

A small tool that parses database connection files saved by **SQLark** (百灵,
`connectionInfo.xml` / `connection-server.xml`) and restores the passwords
stored in them. SQLark encrypts connection details with a **two-layer
AES-128-CBC** scheme: a fixed global key for the outer field, plus a
per-connection random `salt` for the password itself.

> [!WARNING]
> This tool is intended **only** for local credential recovery, password audits and
> security self-assessment on machines you own or are authorized to administer.
> Do not use it against other people's computers or databases.
> See [SECURITY.md](SECURITY.md).

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## Features

- **Auto-discovery** of connection files in `~/.SQLark`, `%APPDATA%\SQLark`,
  Desktop/Documents/Downloads and SQLark installation folders on every drive;
- **Manual selection** of a directory (recursively scanned) or individual files;
- **Batch decryption** of connection name, host, port, username, database type and password;
- **GUI + CLI**: Tkinter desktop app for everyday use, CLI for scripting and CI;
- **Export** to CSV (Excel-friendly UTF-8 BOM), TXT and JSON;
- **Fully offline**: no network calls, no uploads, no registry writes;
- **Packaged easily** into a standalone Windows `.exe` with one command.

![GUI screenshot](docs/images/gui-demo.png)

> All hosts, users and passwords in the screenshot are demo data
> (RFC 5737 documentation networks).

---

## Quick start

### 1. Download the executable

Grab `sqlark-connection-decryptor-v*-windows-x64.exe` from [Releases](../../releases) and double-click it.
No Python installation required. For scripting, download the console build
`sqlark-connection-decryptor-cli-v*-windows-x64.exe` instead.

Artifacts are named by platform and architecture:
- Windows x64 (GUI): `sqlark-connection-decryptor-v*-windows-x64.exe`
- Windows x64 (CLI): `sqlark-connection-decryptor-cli-v*-windows-x64.exe`
- Linux x64 (CLI): `sqlark-connection-decryptor-cli-v*-linux-x64.tar.gz`
- Linux arm64 (CLI): `sqlark-connection-decryptor-cli-v*-linux-arm64.tar.gz`
- macOS (CLI): `sqlark-connection-decryptor-cli-v*-macos-arm64.tar.gz` (Apple Silicon), `sqlark-connection-decryptor-cli-v*-macos-x64.tar.gz` (Intel)

### 2. Run from source

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # launches the GUI
```

### 3. Use the CLI

```bash
# auto-discover and print every connection
python -m sqlark_decrypt scan --auto

# decrypt one file
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"

# batch decrypt + export
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

Example output:

```
Connection      Host             Port   User          DB            Password
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Build a Windows executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# output: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## Supported files

| File | Description |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | All connections stored by SQLark on this machine |
| Any exported `connection-server.xml` | One or more connections exported from the UI |
| `connections.xml` and similar | Any file whose root element is `<CONNECTIONS>` |

Tested with **SQLark 4.x** (Oracle / MySQL / PostgreSQL / DM drivers). If the vendor
changes the cipher, the parser fails loudly instead of returning a wrong password.

---

## How it works

SQLark applies **two layers of AES-128-CBC (PKCS5)**:

1. **Outer layer** — the whole `<connectionDetail>` / `<superAttr>` field:
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **Inner layer** — `password` / `sshPassword` / `sslPassword` inside that JSON:
   `Base64(AES(plaintext, key=salt, iv=reverse(salt)))`, where `salt` is a random
   16-character string stored next to the ciphertext.

Full reverse-engineering notes, the Java class references and a security assessment
are in [docs/encryption.md](docs/encryption.md) (Chinese).

---

## Project layout

```
sqlark-decryptor/
├── sqlark_decrypt/          # reusable Python package
│   ├── crypto.py            # two-layer AES primitives (no business logic)
│   ├── models.py            # ConnectionRecord data model
│   ├── parser.py            # XML parsing + composition of both layers
│   ├── scanner.py           # auto-discovery / recursive directory scan
│   ├── export.py            # CSV / TXT / TSV / JSON writers
│   ├── cli.py               # gui / scan / decrypt subcommands
│   ├── gui.py               # Tkinter GUI
│   └── __main__.py          # python -m sqlark_decrypt entry point
├── tests/                   # pytest suite with fully synthetic fixtures
├── scripts/                 # build, fixture/icon generators, secret scan
├── docs/                    # encryption, architecture, development, publishing
├── assets/                  # icon
├── .github/workflows/       # CI + tagged release build
└── pyproject.toml
```

See [docs/architecture.md](docs/architecture.md) for module responsibilities and data flow.

---

## Development

```bash
pip install -e ".[dev]"

pytest                               # run the test suite
ruff check .                         # lint
python scripts/check_no_secrets.py   # pre-commit secret scan
python scripts/check_i18n.py         # verify translated README links
```

- Test fixtures are generated by `scripts/make_fixture.py` and contain only synthetic
  data (documentation IP ranges + demo passwords).
- Contribution rules: [CONTRIBUTING.md](CONTRIBUTING.md).
- Release checklist: [docs/development.md](docs/development.md).

---

## Privacy & data safety

- The tool never connects to the network, never uploads anything and never modifies
  SQLark files.
- Decrypted output can contain **production database passwords**: do not commit exported
  CSV/JSON, upload it to cloud drives or paste it into tickets.
- The repository ships a `.gitignore` for real connection files plus
  `scripts/check_no_secrets.py` (and CI) to prevent accidental leaks.

---

## FAQ

**Nothing found by auto-discovery?**
Pick "Select directory" and choose `C:\Users\<you>\.SQLark` or the folder with exported files.

**Password column is empty?**
The connection was saved without "remember password", so no ciphertext exists.

**Parsing fails?**
SQLark may have changed the cipher in a new version. Open an issue with the SQLark version
(**never attach a real connection file**).

**Antivirus flags the exe?**
Unsigned PyInstaller binaries are often flagged heuristically. Build from source or add an
exclusion.

---

## License

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## Keywords

SQLark password decryptor, SQLark 百灵 password recovery, database connection password
recovery, Oracle / MySQL / PostgreSQL / DM saved password, AES-128-CBC reverse engineering,
credential recovery, security self-assessment, Tkinter desktop tool, offline password audit.
