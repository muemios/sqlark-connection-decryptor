# SQLark 連線解密工具

[简体中文](README.md) · **繁體中文** · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

解析 **SQLark（百靈）** 儲存的資料庫連線檔案（`connectionInfo.xml` /
`connection-server.xml`），批次還原其中加密保存的資料庫密碼。

> [!WARNING]
> 本工具僅用於**本機憑證找回、密碼稽核與安全自查**（例如忘記自己儲存的資料庫密碼、
> 換機前匯出連線）。請勿用於未經授權的他人電腦或資料庫，後果由使用者自行承擔。
> 詳見 [SECURITY.md](SECURITY.md)。

> [!NOTE]
> 本專案為非官方社群專案，與 SQLark / 達夢（DM）官方無關聯，亦未獲其背書。

---

## 功能

- **自動搜尋**：自動檢查 `~/.SQLark`、`%APPDATA%\SQLark`、桌面/文件/下載，以及各磁碟的 SQLark 安裝目錄；
- **手動指定**：可選擇目錄（遞迴掃描）或直接選擇檔案；
- **批次解密**：一次解析全部連線，還原連線名稱、主機、連接埠、使用者、資料庫類型與明文密碼；
- **圖形介面 + 命令列**：Tkinter 桌面程式適合日常使用，CLI 適合腳本化處理；
- **匯出**：CSV（Excel 開啟不亂碼）、TXT、JSON；
- **完全離線**：不連網、不上傳、不寫登錄檔，只讀取你指定的檔案；
- **易於打包**：一行命令產生免安裝的 Windows 單檔 exe。

![圖形介面截圖](docs/images/gui-demo.png)

> 截圖中的主機、使用者與密碼皆為示範資料（RFC 5737 文件專用網段）。

---

## 快速開始

### 方式一：下載 exe（一般使用者）

到 [Releases](../../releases) 下載 `sqlark-connection-decryptor-v*-windows-x64.exe`，雙擊執行即可（無需安裝 Python）。
需要命令列/腳本化呼叫時，下載 `sqlark-connection-decryptor-cli-v*-windows-x64.exe`（主控台版）。

發佈產物依平台/架構命名：
- Windows x64（圖形介面）：`sqlark-connection-decryptor-v*-windows-x64.exe`
- Windows x64（命令列）：`sqlark-connection-decryptor-cli-v*-windows-x64.exe`
- Linux x64（命令列）：`sqlark-connection-decryptor-cli-v*-linux-x64.tar.gz`
- Linux arm64（命令列）：`sqlark-connection-decryptor-cli-v*-linux-arm64.tar.gz`
- macOS（命令列）：`sqlark-connection-decryptor-cli-v*-macos-arm64.tar.gz`（Apple Silicon）、`sqlark-connection-decryptor-cli-v*-macos-x64.tar.gz`（Intel）

### 方式二：從原始碼執行

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # 啟動圖形介面
```

### 方式三：命令列

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

輸出範例：

```
連線名稱        主機            連接埠  使用者        資料庫        密碼
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 方式四：建置 Windows exe

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# 產物: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## 支援的檔案

| 檔案 | 說明 |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | SQLark 本機全部連線（最常見） |
| 任意的 `connection-server.xml` | 從介面「匯出連線」產生的檔案 |
| `connections.xml` 等 | 只要根節點是 `<CONNECTIONS>` 即可辨識 |

相容性：已在 **SQLark 4.x**（Oracle / MySQL / PostgreSQL / 達夢等驅動）驗證。
若官方更換演算法，本工具會解析失敗，而不是給出錯誤密碼。

---

## 運作原理

SQLark 對連線資訊使用**兩層 AES-128-CBC（PKCS5Padding）**：

1. **外層**：整個 `<connectionDetail>` / `<superAttr>` 欄位
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **內層**：JSON 中的 `password` / `sshPassword` / `sslPassword`
   `Base64(AES(明文, key=salt, iv=reverse(salt)))`，`salt` 為每條連線隨機產生的 16 字元字串，
   與密文一起保存在同一個 JSON 中。

完整逆向過程、Java 類別出處與安全性分析見 [docs/encryption.md](docs/encryption.md)。

---

## 專案結構

```
sqlark-decryptor/
├── sqlark_decrypt/          # 可重用的 Python 套件
│   ├── crypto.py            # 兩層 AES 原語
│   ├── parser.py            # XML 解析 + 組合兩層解密
│   ├── scanner.py           # 檔案搜尋
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # gui / scan / decrypt 子命令
│   └── gui.py               # Tkinter 圖形介面
├── tests/                   # 34 項單元測試 + 全虛構測試資料
├── scripts/                 # 建置、示範資料、圖示、敏感資訊自檢
├── docs/                    # 加密原理、架構、開發與發佈文件
├── .github/workflows/       # CI 與 tag 自動發佈
└── pyproject.toml
```

---

## 開發

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # 檢查多語言 README 連結一致性
```

- 測試資料由 `scripts/make_fixture.py` 產生，僅含虛構內容（文件專用網段 + 示範密碼）。
- 貢獻規範見 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 隱私與資料安全

- 程式不連網、不上傳、不修改 SQLark 檔案；
- 解密結果可能包含**生產環境資料庫密碼**：請勿提交到 Git、上傳雲端或貼到工單；
- 儲存庫已設定 `.gitignore` 忽略真實連線檔案，並提供 `scripts/check_no_secrets.py` 與 CI 檢查。

---

## 常見問題

**自動搜尋找不到？** 點「選擇目錄」，選擇 `C:\Users\<你>\.SQLark` 或匯出檔案所在資料夾。

**密碼欄位是空的？** 該連線儲存時未勾選「記住密碼」，檔案中沒有密文。

**解析失敗？** SQLark 可能更換了演算法。請開 Issue 並附上 SQLark 版本（**不要附真實連線檔案**）。

---

## 授權

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## 關鍵字

SQLark 密碼解密、SQLark 百靈 密碼找回、資料庫連線密碼還原、Oracle / MySQL / PostgreSQL / 達夢
儲存密碼、AES-128-CBC 逆向、憑證恢復、安全自查、Tkinter 桌面工具、離線密碼稽核、
connectionInfo.xml 解密、connection-server.xml 解密。
