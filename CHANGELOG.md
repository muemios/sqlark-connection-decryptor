# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)，格式参考
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.1.1] - 2026-11-17

首个公开发布版本。

> 说明：`v0.1.0` 这一 tag 名称在新的 GitHub 仓库中被保留限制（历史 immutable release 记录），
> 因此首发版本号使用 `0.1.1`，功能内容与最初的 0.1.0 计划一致。

### 新增

- 解析 SQLark（百灵）连接文件 `connectionInfo.xml` / `connection-server.xml`；
- 还原双层 AES-128-CBC 加密的连接详情、密码、SSH/SSL 密码；
- 自动检索 `~/.SQLark`、`%APPDATA%\SQLark`、桌面/文档/下载及安装目录；
- Tkinter 图形界面：检索、手动选目录/文件、过滤、排序、复制、导出；
- 命令行：`gui` / `scan` / `decrypt` 三个子命令，支持 CSV / TXT / JSON 导出；
- 单元测试（34 项）与 GitHub Actions CI；
- 敏感信息自检脚本（`scripts/check_no_secrets.py`）；
- 10 种语言的 README（简中、繁中、英、日、韩、西、法、德、俄、葡）；
- 多语言一致性检查（`scripts/check_i18n.py`）与自动生成语言栏；
- 跨平台构建脚本 `scripts/build_binary.py`，产物按“版本 + 平台 + 架构”命名，
  Release 自动产出：
  - `sqlark-connection-decryptor-v<ver>-windows-x64.exe`（GUI）
  - `sqlark-connection-decryptor-cli-v<ver>-windows-x64.exe`
  - `sqlark-connection-decryptor-cli-v<ver>-linux-x64.tar.gz`
  - `sqlark-connection-decryptor-cli-v<ver>-linux-arm64.tar.gz`
  - `sqlark-connection-decryptor-cli-v<ver>-macos-arm64.tar.gz`
  - `sqlark-connection-decryptor-cli-v<ver>-macos-x64.tar.gz`
- Release 自动生成 `SHA256SUMS.txt`。

### 说明

- 仅支持 SQLark 4.x 的连接文件格式；
- GUI 仅提供 Windows 版；CLI 支持 Windows / Linux / macOS（源码亦可 `pip install` 运行）。

[0.1.1]: ../../releases/tag/v0.1.1
