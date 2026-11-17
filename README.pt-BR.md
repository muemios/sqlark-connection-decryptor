# Decifrador de conexões do SQLark

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · **Português (BR)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![CI](https://github.com/muemios/sqlark-connection-decryptor/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Ferramenta que analisa os arquivos de conexão salvos pelo **SQLark (百灵)**
(`connectionInfo.xml` / `connection-server.xml`) e recupera as senhas de banco de dados
criptografadas neles.

> [!WARNING]
> Esta ferramenta destina-se **apenas** à recuperação de credenciais, auditoria de senhas e
> autoavaliação de segurança em computadores próprios ou autorizados.
> Não a utilize em computadores ou bancos de dados de terceiros sem permissão.
> Consulte [SECURITY.md](SECURITY.md).

> [!NOTE]
> Unofficial community project — not affiliated with or endorsed by SQLark or DM.

---

## Recursos

- **Descoberta automática** em `~/.SQLark`, `%APPDATA%\SQLark`, Área de Trabalho/Documentos/Downloads
  e nas pastas de instalação do SQLark em todas as unidades;
- **Seleção manual** de uma pasta (varredura recursiva) ou de arquivos individuais;
- **Descriptografia em lote** de nome, host, porta, usuário, tipo de banco e senha;
- **GUI + CLI**: app Tkinter no dia a dia e CLI para automação;
- **Exportação** para CSV (UTF-8 BOM, compatível com Excel), TXT e JSON;
- **Totalmente offline**: sem rede, sem uploads, sem escrever no registro;
- **Empacotamento simples** em um `.exe` autônomo do Windows com um comando.

![Captura da interface](docs/images/gui-demo.png)

> Hosts, usuários e senhas na captura são dados de demonstração
> (faixas de IP RFC 5737 para documentação).

---

## Início rápido

### 1. Baixar o executável

Baixe `sqlark-connection-decryptor-v*-windows-x64.exe` em [Releases](../../releases) e clique duas vezes.
Não é necessário instalar Python. Para scripts, use a versão de console
`sqlark-connection-decryptor-cli-v*-windows-x64.exe`.

Binários CLI para Linux e macOS também estão em Releases (`linux-x64`, `linux-arm64`, `macos-arm64`, `macos-x64`).

### 2. Executar a partir do código

```bash
git clone https://github.com/muemios/sqlark-connection-decryptor.git
cd sqlark-connection-decryptor
pip install -e .
python -m sqlark_decrypt          # abre a interface
```

### 3. Usar a CLI

```bash
python -m sqlark_decrypt scan --auto
python -m sqlark_decrypt decrypt "C:\Users\me\.SQLark\connectionInfo.xml"
python -m sqlark_decrypt decrypt "*.xml" --csv result.csv --txt result.txt --json result.json
```

Exemplo de saída:

```
Conexão         Host            Porta   Usuário       BD            Senha
----------------------------------------------------------------------------
demo-oracle     192.0.2.10       1521   demo_user     ORACLE        Demo#Pass123
demo-mysql      198.51.100.24    3306   demo_reader   MYSQL         ReadOnly!2024
demo-postgres   203.0.113.5      5432   analyst       POSTGRESQL    analyst_pw
```

### 4. Compilar o exe do Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# saída: dist\sqlark-connection-decryptor-v*-windows-x64.exe
```

---

## Arquivos suportados

| Arquivo | Descrição |
| --- | --- |
| `%USERPROFILE%\.SQLark\connectionInfo.xml` | Todas as conexões locais do SQLark (mais comum) |
| Qualquer `connection-server.xml` exportado | Gerado por "Exportar conexões" |
| `connections.xml` e similares | Qualquer arquivo cujo elemento raiz seja `<CONNECTIONS>` |

Testado com **SQLark 4.x** (drivers Oracle / MySQL / PostgreSQL / DM). Se o fabricante mudar a
criptografia, a ferramenta falha explicitamente em vez de retornar uma senha errada.

---

## Como funciona

O SQLark aplica **duas camadas de AES-128-CBC (PKCS5Padding)**:

1. **Camada externa**: todo o campo `<connectionDetail>` / `<superAttr>`
   `Base64(AES(JSON, key="fudih4xp113znwp7", iv=reverse(key)))`
2. **Camada interna**: `password` / `sshPassword` / `sslPassword` dentro do JSON
   `Base64(AES(texto puro, key=salt, iv=reverse(salt)))`, em que `salt` é uma string
   aleatória de 16 caracteres armazenada junto ao texto cifrado.

As notas completas de engenharia reversa, as classes Java e a análise de segurança estão em
[docs/encryption.md](docs/encryption.md) (em chinês).

---

## Estrutura do projeto

```
sqlark-decryptor/
├── sqlark_decrypt/          # pacote Python reutilizável
│   ├── crypto.py            # primitivas AES em duas camadas
│   ├── parser.py            # análise de XML + composição das camadas
│   ├── scanner.py           # busca de arquivos
│   ├── export.py            # CSV / TXT / TSV / JSON
│   ├── cli.py               # subcomandos gui / scan / decrypt
│   └── gui.py               # interface Tkinter
├── tests/                   # 34 testes unitários, dados 100% sintéticos
├── scripts/                 # build, dados de demo, ícone, varredura de segredos
├── docs/                    # criptografia, arquitetura, desenvolvimento, release
├── .github/workflows/       # CI e release automático por tag
└── pyproject.toml
```

---

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest
ruff check .
python scripts/check_no_secrets.py
python scripts/check_i18n.py     # valida os links dos README traduzidos
```

- Os dados de teste são gerados por `scripts/make_fixture.py` e são totalmente fictícios
  (faixas de IP de documentação + senhas de demonstração).
- Regras de contribuição: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Privacidade e segurança dos dados

- Sem chamadas de rede, uploads ou alterações nos arquivos do SQLark;
- O resultado pode conter **senhas de produção**: não faça commit, não envie para nuvem nem
  cole em tickets;
- O repositório inclui um `.gitignore` para arquivos reais e `scripts/check_no_secrets.py`
  (também executado na CI).

---

## Perguntas frequentes

**A descoberta automática não encontra nada** → use "Selecionar pasta" e escolha
`C:\Users\<você>\.SQLark`.

**A coluna de senha está vazia** → a conexão foi salva sem "lembrar senha".

**A análise falha** → o SQLark pode ter mudado a criptografia. Abra uma issue com a versão do
SQLark (**nunca anexe um arquivo de conexão real**).

---

## Licença

[MIT](LICENSE) © 2026 SQLark Decryptor contributors

---

## Palavras-chave

Decifrador de senhas do SQLark, recuperação de senhas SQLark 百灵, recuperação de senhas de
conexão de banco de dados, senhas salvas do Oracle / MySQL / PostgreSQL / DM, engenharia reversa
de AES-128-CBC, recuperação de credenciais, auditoria de segurança, ferramenta Tkinter,
auditoria offline de senhas, connectionInfo.xml, connection-server.xml.
