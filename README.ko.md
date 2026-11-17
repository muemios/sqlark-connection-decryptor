# SQLark 연결 파일 복호화 도구

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [日本語](README.ja.md) · **한국어** · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Português (BR)](README.pt-BR.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

**SQLark(百灵)** 이 저장한 데이터베이스 연결 파일(`connectionInfo.xml` /
`connection-server.xml`)을 파싱하여 암호화되어 저장된 연결 비밀번호를 일괄 복원합니다.

> [!WARNING]
> 이 도구는 **본인이 소유하거나 관리 권한이 있는 컴퓨터에서의 자격 증명 복구, 비밀번호 감사,
> 보안 자가 점검** 용도로만 사용해야 합니다. 다른 사람의 컴퓨터나 데이터베이스에 무단으로
> 사용하는 것은 금지됩니다. 자세한 내용은 [SECURITY.md](SECURITY.md)를 참고하세요.

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## 기능

- **자동 검색**: `~/.SQLark`, `%APPDATA%\SQLark`, 바탕화면/문서/다운로드, 각 드라이브의 SQLark 설치 폴더를 자동 탐색;
- **수동 선택**: 폴더(재귀 검색) 또는 파일을 직접 선택;
- **일괄 복호화**: 연결 이름, 호스트, 포트, 사용자, DB 종류, 평문 비밀번호를 한 번에 표시;
- **GUI + CLI**: 일상 사용은 Tkinter GUI, 자동화는 CLI;
- **내보내기**: CSV(Excel에서 깨지지 않는 UTF-8 BOM), TXT, JSON;
- **완전 오프라인**: 네트워크 통신·업로드·레지스트리 쓰기 없음. 지정한 파일만 읽음;
- **간편 패키징**: 명령 하나로 설치가 필요 없는 Windows 단일 exe 생성.

![GUI 스크린샷](docs/images/gui-demo.png)

> 스크린샷의 호스트·사용자·비밀번호는 모두 데모 데이터입니다(RFC 5737 문서용 네트워크).

---

## 빠른 시작

### 1. exe 다운로드

[Releases](../../releases)에서 `sqlark-connection-decryptor-v*-windows-x64.exe`를 받아 더블 클릭하면 됩니다
(Python 설치 불필요). 스크립트 용도로는 콘솔 버전 `sqlark-connection-decryptor-cli-v*-windows-x64.exe`를 사용하세요.

Linux / macOS용 CLI 바이너리도 Releases에서 제공합니다(`linux-x64` / `linux-arm64` / `macos-arm64` / `macos-x64`).

### 2. 소스에서 실행

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # GUI 실행
```

### 3. CLI 사용

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

출력 예시:

```
연결 이름        호스트          포트    사용자        DB            비밀번호
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Windows exe 빌드

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# 산출물: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## 지원 파일

| 파일 | 설명 |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | SQLark 로컬 전체 연결(가장 일반적) |
| 내보낸 `connection-server.xml` | UI의 "연결 내보내기"로 생성 |
| `connections.xml` 등 | 루트 요소가 `<CONNECTIONS>`이면 인식 |

**SQLark 4.x**(Oracle / MySQL / PostgreSQL / DM 등)에서 검증했습니다.
벤더가 암호화 방식을 변경하면 잘못된 비밀번호를 반환하지 않고 파싱 오류가 발생합니다.

---

## 동작 원리

SQLark는 연결 정보를 **2중 AES-128-CBC(PKCS5Padding)** 로 암호화합니다.

1. **외부 계층**: `<connectionDetail>` / `<superAttr>` 필드 전체
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **내부 계층**: JSON 내부의 `password` / `sshPassword` / `sslPassword`
   `Base64(AES(평문, key=salt, iv=reverse(salt)))`. `salt`는 연결마다 생성되는
   16자리 랜덤 문자열로, 암호문과 같은 JSON에 저장됩니다.

자세한 리버스 엔지니어링 과정, Java 클래스 출처, 보안 평가는
[docs/encryption.md](docs/encryption.md)(중국어)를 참고하세요.

---

## 프로젝트 구조

```
sqlark-decryptor/
├── sqlark_decrypt/          # 재사용 가능한 Python 패키지
│   ├── crypto.py            # 2중 AES 프리미티브
│   ├── parser.py            # XML 파싱 + 두 계층 복호화
│   ├── scanner.py           # 파일 탐색
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # gui / scan / decrypt 서브커맨드
│   └── gui.py               # Tkinter GUI
├── tests/                   # 34개 단위 테스트(전부 가상 데이터)
├── scripts/                 # 빌드·데모 데이터·아이콘·민감정보 점검
├── docs/                    # 암호화 원리·아키텍처·개발·배포 문서
├── .github/workflows/       # CI 및 tag 기반 릴리스
└── pyproject.toml
```

---

## 개발

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # 다국어 README 링크 일관성 검사
```

- 테스트 데이터는 `scripts/make_fixture.py`가 생성하며 모두 가상의 내용입니다
  (문서용 IP 대역 + 데모 비밀번호).
- 기여 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

---

## 개인정보 및 데이터 보호

- 네트워크 통신, 업로드, SQLark 파일 수정을 하지 않습니다;
- 복호화 결과에는 **운영 데이터베이스 비밀번호**가 포함될 수 있습니다.
  Git 커밋, 클라우드 업로드, 티켓 붙여넣기를 피하세요;
- 저장소에는 실제 연결 파일을 무시하는 `.gitignore`와
  `scripts/check_no_secrets.py`(CI에서도 실행)가 포함되어 있습니다.

---

## FAQ

**자동 검색에서 찾지 못함** → "폴더 선택"으로 `C:\Users\<사용자>\.SQLark`를 지정하세요.

**비밀번호가 비어 있음** → 연결 저장 시 "비밀번호 기억"이 꺼져 있어 암호문이 없습니다.

**파싱 실패** → SQLark가 암호화 방식을 변경했을 수 있습니다. SQLark 버전과 함께 Issue를
등록해 주세요(**실제 연결 파일은 첨부하지 마세요**).

---

## 라이선스

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## 키워드

SQLark 비밀번호 복호화, SQLark 百灵 비밀번호 복구, 데이터베이스 연결 비밀번호 복구,
Oracle / MySQL / PostgreSQL / DM 저장 비밀번호, AES-128-CBC 리버스 엔지니어링,
자격 증명 복구, 보안 자가 점검, Tkinter 데스크톱 도구, 오프라인 비밀번호 감사,
connectionInfo.xml 복호화, connection-server.xml 복호화.
