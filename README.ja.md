# SQLark 接続ファイル復号ツール

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · **日本語** · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

**SQLark（百霊）** が保存したデータベース接続ファイル（`connectionInfo.xml` /
`connection-server.xml`）を解析し、暗号化された接続パスワードをまとめて復元するツールです。

> [!WARNING]
> 本ツールは**自分が所有・管理する端末での認証情報の復元、パスワード監査、セキュリティ自己診断**
> のみを目的としています。他者の端末やデータベースへの無断使用は禁止です。
> 詳細は [SECURITY.md](SECURITY.md) を参照してください。

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## 機能

- **自動検索**：`~/.SQLark`、`%APPDATA%\SQLark`、デスクトップ/ドキュメント/ダウンロード、
  各ドライブの SQLark インストール先を自動で探索；
- **手動指定**：フォルダ（再帰検索）またはファイルを直接選択；
- **一括復号**：接続名・ホスト・ポート・ユーザー・DB 種別・平文パスワードをまとめて表示；
- **GUI + CLI**：日常利用は Tkinter のデスクトップアプリ、自動化は CLI；
- **エクスポート**：CSV（Excel で文字化けしない UTF-8 BOM）、TXT、JSON；
- **完全オフライン**：通信・アップロード・レジストリ書き込みなし。指定したファイルのみ読み込み；
- **簡単パッケージング**：コマンド 1 つで Windows 用の単体 exe を作成。

![GUI スクリーンショット](docs/images/gui-demo.png)

> スクリーンショットのホスト・ユーザー・パスワードはすべてデモ用データです（RFC 5737 の文書用ネットワーク）。

---

## クイックスタート

### 1. exe をダウンロード

[Releases](../../releases) から `sqlark-connection-decryptor-v*-windows-x64.exe` を取得してダブルクリックするだけです
（Python のインストール不要）。スクリプト用途には `sqlark-connection-decryptor-cli-v*-windows-x64.exe`（コンソール版）も用意しています。

Linux / macOS 用の CLI バイナリも Releases で配布しています（`linux-x64` / `linux-arm64` / `macos-arm64` / `macos-x64`）。

### 2. ソースから実行

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # GUI を起動
```

### 3. CLI で実行

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

出力例：

```
接続名          ホスト          ポート  ユーザー      DB            パスワード
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Windows exe をビルド

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# 出力: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## 対応ファイル

| ファイル | 説明 |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | この端末の全接続（最も一般的） |
| エクスポートした `connection-server.xml` | UI の「接続のエクスポート」で生成 |
| `connections.xml` など | ルート要素が `<CONNECTIONS>` であれば認識 |

**SQLark 4.x**（Oracle / MySQL / PostgreSQL / DM など）で動作確認済み。
ベンダーが暗号方式を変更した場合、本ツールは誤ったパスワードを返さず解析エラーになります。

---

## 仕組み

SQLark は接続情報を**2 層の AES-128-CBC（PKCS5Padding）**で暗号化しています。

1. **外側**：`<connectionDetail>` / `<superAttr>` フィールド全体
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **内側**：JSON 内の `password` / `sshPassword` / `sslPassword`
   `Base64(AES(平文, key=salt, iv=reverse(salt)))`。`salt` は接続ごとに生成される
   16 文字のランダム文字列で、暗号文と同じ JSON に保存されます。

詳細なリバースエンジニアリング手順・Java クラス名・安全性評価は
[docs/encryption.md](docs/encryption.md)（中国語）にあります。

---

## プロジェクト構成

```
sqlark-decryptor/
├── sqlark_decrypt/          # 再利用可能な Python パッケージ
│   ├── crypto.py            # 2 層 AES のプリミティブ
│   ├── parser.py            # XML 解析 + 2 層復号の組み合わせ
│   ├── scanner.py           # ファイル探索
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # gui / scan / decrypt サブコマンド
│   └── gui.py               # Tkinter GUI
├── tests/                   # 34 件のユニットテスト（合成データのみ）
├── scripts/                 # ビルド・デモデータ・アイコン・機密情報チェック
├── docs/                    # 暗号仕様・アーキテクチャ・開発・公開手順
├── .github/workflows/       # CI とタグ連動リリース
└── pyproject.toml
```

---

## 開発

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # 多言語 README のリンク整合性チェック
```

- テスト用データは `scripts/make_fixture.py` が生成し、すべて架空の内容です
  （文書用 IP 範囲 + デモパスワード）。
- コントリビューション規約は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

---

## プライバシーとデータ保護

- ネットワーク通信・アップロード・SQLark ファイルの変更は一切行いません；
- 復号結果には**本番データベースのパスワード**が含まれる場合があります。
  Git へのコミット、クラウドへのアップロード、チケットへの貼り付けは避けてください；
- リポジトリは実データを無視する `.gitignore` と、`scripts/check_no_secrets.py`
  （CI でも実行）を備えています。

---

## FAQ

**自動検索で見つからない** → 「フォルダを選択」で `C:\Users\<ユーザー>\.SQLark` を指定してください。

**パスワード欄が空** → 接続保存時に「パスワードを記憶する」が無効だったため、暗号文がありません。

**解析に失敗する** → SQLark が暗号方式を変更した可能性があります。SQLark のバージョンを添えて
Issue を作成してください（**実際の接続ファイルは添付しないでください**）。

---

## ライセンス

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## キーワード

SQLark パスワード復号、SQLark 百霊 パスワード復元、データベース接続パスワード復元、
Oracle / MySQL / PostgreSQL / DM 保存パスワード、AES-128-CBC リバースエンジニアリング、
認証情報復元、セキュリティ自己診断、Tkinter デスクトップツール、オフラインパスワード監査、
connectionInfo.xml 復号、connection-server.xml 復号。
