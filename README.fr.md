# Déchiffreur de connexions SQLark

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · **Français** · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Outil qui analyse les fichiers de connexion enregistrés par **SQLark (百灵)**
(`connectionInfo.xml` / `connection-server.xml`) et restaure les mots de passe de bases de
données qui y sont chiffrés.

> [!WARNING]
> Cet outil est destiné **uniquement** à la récupération d'identifiants, aux audits de mots de
> passe et à l'auto-évaluation de sécurité sur des machines dont vous êtes propriétaire ou
> administrateur autorisé. Ne l'utilisez pas sur les ordinateurs ou bases de données de tiers.
> Voir [SECURITY.md](SECURITY.md).

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## Fonctionnalités

- **Découverte automatique** dans `~/.SQLark`, `%APPDATA%\SQLark`, Bureau/Documents/Téléchargements
  et les dossiers d'installation de SQLark sur chaque disque ;
- **Sélection manuelle** d'un dossier (analyse récursive) ou de fichiers ;
- **Déchiffrement par lot** du nom, de l'hôte, du port, de l'utilisateur, du type de SGBD et du mot de passe ;
- **GUI + CLI** : application Tkinter au quotidien, CLI pour l'automatisation ;
- **Export** en CSV (UTF-8 BOM, compatible Excel), TXT et JSON ;
- **Entièrement hors ligne** : aucun appel réseau, aucun envoi, aucune écriture dans le registre ;
- **Empaquetage simple** en un `.exe` Windows autonome avec une seule commande.

![Capture d'écran de l'interface](docs/images/gui-demo.png)

> Les hôtes, utilisateurs et mots de passe de la capture sont des données de démonstration
> (plages d'adresses RFC 5737 réservées à la documentation).

---

## Démarrage rapide

### 1. Télécharger l'exécutable

Récupérez `sqlark-connection-decryptor-v*-windows-x64.exe` dans [Releases](../../releases) et double-cliquez.
Aucune installation de Python n'est nécessaire. Pour les scripts, utilisez la version console
`sqlark-connection-decryptor-cli-v*-windows-x64.exe`.

Les binaires CLI pour Linux et macOS sont aussi disponibles dans Releases (`linux-x64`, `linux-arm64`, `macos-arm64`, `macos-x64`).

### 2. Depuis les sources

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # lance l'interface graphique
```

### 3. Utiliser la CLI

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

Exemple de sortie :

```
Connexion       Hôte            Port    Utilisateur   SGBD          Mot de passe
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Compiler l'exe Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# sortie : dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## Fichiers pris en charge

| Fichier | Description |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | Toutes les connexions locales de SQLark (le plus courant) |
| Tout `connection-server.xml` exporté | Généré par « Exporter les connexions » |
| `connections.xml` et similaires | Tout fichier dont la racine est `<CONNECTIONS>` |

Testé avec **SQLark 4.x** (pilotes Oracle / MySQL / PostgreSQL / DM). Si l'éditeur change le
chiffrement, l'outil échoue explicitement au lieu de renvoyer un mot de passe erroné.

---

## Fonctionnement

SQLark applique **deux couches d'AES-128-CBC (PKCS5Padding)** :

1. **Couche externe** : tout le champ `<connectionDetail>` / `<superAttr>`
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **Couche interne** : `password` / `sshPassword` / `sslPassword` dans le JSON
   `Base64(AES(texte clair, key=salt, iv=reverse(salt)))`, où `salt` est une chaîne aléatoire
   de 16 caractères stockée à côté du chiffré.

Les notes complètes de rétro-ingénierie, les classes Java d'origine et l'analyse de sécurité
sont dans [docs/encryption.md](docs/encryption.md) (en chinois).

---

## Structure du projet

```
sqlark-decryptor/
├── sqlark_decrypt/          # paquet Python réutilisable
│   ├── crypto.py            # primitives AES à deux couches
│   ├── parser.py            # analyse XML + composition des couches
│   ├── scanner.py           # recherche de fichiers
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # sous-commandes gui / scan / decrypt
│   └── gui.py               # interface Tkinter
├── tests/                   # 34 tests unitaires, données 100 % synthétiques
├── scripts/                 # build, données de démo, icône, scan de secrets
├── docs/                    # chiffrement, architecture, développement, publication
├── .github/workflows/       # CI et release automatique sur tag
└── pyproject.toml
```

---

## Développement

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # vérifie la cohérence des liens des README traduits
```

- Les données de test sont générées par `scripts/make_fixture.py` et sont entièrement fictives
  (plages IP de documentation + mots de passe de démonstration).
- Règles de contribution : [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Confidentialité et sécurité des données

- Aucun appel réseau, aucun envoi, aucune modification des fichiers SQLark ;
- Le résultat peut contenir des **mots de passe de production** : ne les commitez pas, ne les
  déposez pas sur un cloud et ne les collez pas dans un ticket ;
- Le dépôt fournit un `.gitignore` pour les fichiers réels et
  `scripts/check_no_secrets.py` (exécuté aussi en CI).

---

## FAQ

**La découverte automatique ne trouve rien** → utilisez « Sélectionner un dossier » et choisissez
`C:\Users\<vous>\.SQLark`.

**La colonne mot de passe est vide** → la connexion a été enregistrée sans « mémoriser le mot de passe ».

**L'analyse échoue** → SQLark a peut-être changé le chiffrement. Ouvrez une issue avec la version
de SQLark (**ne joignez jamais un fichier de connexion réel**).

---

## Licence

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## Mots-clés

Déchiffrement de mots de passe SQLark, récupération de mots de passe SQLark 百灵, récupération de
mots de passe de connexion, mots de passe enregistrés Oracle / MySQL / PostgreSQL / DM,
rétro-ingénierie AES-128-CBC, récupération d'identifiants, audit de sécurité, outil Tkinter,
audit hors ligne, connectionInfo.xml, connection-server.xml.
