# SQLark-Verbindungsentschlüssler

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · **Deutsch** · [Русский](README.ru.md) · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Ein Werkzeug, das von **SQLark (百灵)** gespeicherte Verbindungsdateien
(`connectionInfo.xml` / `connection-server.xml`) ausliest und die darin verschlüsselten
Datenbankpasswörter wiederherstellt.

> [!WARNING]
> Dieses Werkzeug ist **ausschließlich** für die Wiederherstellung von Zugangsdaten, Passwort-
> Audits und Sicherheitsselbstprüfungen auf eigenen oder autorisierten Rechnern gedacht.
> Die Nutzung auf fremden Rechnern oder Datenbanken ist untersagt.
> Siehe [SECURITY.md](SECURITY.md).

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## Funktionen

- **Automatische Suche** in `~/.SQLark`, `%APPDATA%\SQLark`, Desktop/Dokumente/Downloads und den
  SQLark-Installationsordnern aller Laufwerke;
- **Manuelle Auswahl** eines Ordners (rekursive Suche) oder einzelner Dateien;
- **Stapelentschlüsselung** von Name, Host, Port, Benutzer, Datenbanktyp und Passwort;
- **GUI + CLI**: Tkinter-Anwendung für den Alltag, CLI für Skripte;
- **Export** nach CSV (UTF-8-BOM, Excel-freundlich), TXT und JSON;
- **Vollständig offline**: keine Netzwerkzugriffe, keine Uploads, keine Registry-Schreibzugriffe;
- **Einfaches Packen** in eine eigenständige Windows-`.exe` mit einem Befehl.

![GUI-Screenshot](docs/images/gui-demo.png)

> Hosts, Benutzer und Passwörter im Screenshot sind Demodaten
> (RFC-5737-Dokumentationsnetze).

---

## Schnellstart

### 1. Executable herunterladen

`sqlark-connection-decryptor-v*-windows-x64.exe` aus [Releases](../../releases) herunterladen und doppelklicken.
Python ist nicht erforderlich. Für Skripte gibt es die Konsolenversion
`sqlark-connection-decryptor-cli-v*-windows-x64.exe`.

CLI-Binaries für Linux und macOS gibt es ebenfalls in den Releases (`linux-x64`, `linux-arm64`, `macos-arm64`, `macos-x64`).

### 2. Aus dem Quellcode starten

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # startet die GUI
```

### 3. CLI verwenden

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

Beispielausgabe:

```
Verbindung      Host            Port    Benutzer      DB            Passwort
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Windows-EXE bauen

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# Ausgabe: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## Unterstützte Dateien

| Datei | Beschreibung |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | Alle lokalen Verbindungen von SQLark (üblich) |
| Exportierte `connection-server.xml` | Über „Verbindungen exportieren“ erzeugt |
| `connections.xml` und ähnliche | Jede Datei mit `<CONNECTIONS>` als Wurzelelement |

Getestet mit **SQLark 4.x** (Oracle / MySQL / PostgreSQL / DM). Ändert der Hersteller die
Verschlüsselung, schlägt das Werkzeug explizit fehl, statt ein falsches Passwort zu liefern.

---

## Funktionsweise

SQLark verwendet **zwei AES-128-CBC-Schichten (PKCS5Padding)**:

1. **Äußere Schicht**: das gesamte Feld `<connectionDetail>` / `<superAttr>`
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **Innere Schicht**: `password` / `sshPassword` / `sslPassword` im JSON
   `Base64(AES(Klartext, key=salt, iv=reverse(salt)))`, wobei `salt` eine zufällige
   16-Zeichen-Zeichenkette ist, die neben dem Geheimtext gespeichert wird.

Vollständige Reverse-Engineering-Notizen, Java-Klassen und Sicherheitsbewertung:
[docs/encryption.md](docs/encryption.md) (chinesisch).

---

## Projektstruktur

```
sqlark-decryptor/
├── sqlark_decrypt/          # wiederverwendbares Python-Paket
│   ├── crypto.py            # zweischichtige AES-Primitive
│   ├── parser.py            # XML-Parsing + Schichtkomposition
│   ├── scanner.py           # Dateisuche
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # Unterbefehle gui / scan / decrypt
│   └── gui.py               # Tkinter-GUI
├── tests/                   # 34 Unit-Tests, rein synthetische Daten
├── scripts/                 # Build, Demodaten, Icon, Secret-Scan
├── docs/                    # Verschlüsselung, Architektur, Entwicklung, Release
├── .github/workflows/       # CI und automatischer Release per Tag
└── pyproject.toml
```

---

## Entwicklung

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # prüft die Links aller übersetzten READMEs
```

- Testdaten erzeugt `scripts/make_fixture.py`; sie sind vollständig fiktiv
  (Dokumentations-IP-Bereiche + Demo-Passwörter).
- Beitragsregeln: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Datenschutz und Datensicherheit

- Keine Netzwerkzugriffe, keine Uploads, keine Änderungen an SQLark-Dateien;
- Ergebnisse können **Produktionsdatenbank-Passwörter** enthalten: nicht committen,
  nicht in Clouds hochladen, nicht in Tickets einfügen;
- Das Repository enthält eine `.gitignore` für echte Verbindungsdateien und
  `scripts/check_no_secrets.py` (läuft auch in der CI).

---

## FAQ

**Die automatische Suche findet nichts** → „Ordner auswählen“ und
`C:\Users\<Benutzer>\.SQLark` wählen.

**Passwortspalte ist leer** → Die Verbindung wurde ohne „Passwort merken“ gespeichert.

**Parsing schlägt fehl** → SQLark hat möglicherweise die Verschlüsselung geändert. Bitte ein
Issue mit der SQLark-Version öffnen (**niemals echte Verbindungsdateien anhängen**).

---

## Lizenz

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## Schlüsselwörter

SQLark-Passwortentschlüsselung, SQLark 百灵 Passwortwiederherstellung, Wiederherstellung von
Datenbank-Verbindungspasswörtern, gespeicherte Passwörter Oracle / MySQL / PostgreSQL / DM,
AES-128-CBC Reverse Engineering, Wiederherstellung von Zugangsdaten, Sicherheitsaudit,
Tkinter-Werkzeug, Offline-Passwortaudit, connectionInfo.xml, connection-server.xml.
