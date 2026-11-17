# 开发与发布指南

## 1. 环境准备

- Python 3.9+（推荐 3.11/3.12）
- Windows 打包 exe 需要 PyInstaller；Linux/macOS 可只用 CLI

```bash
git clone <your-fork-url>
cd sqlark-decryptor

python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -e ".[dev]"          # 开发/测试依赖
pip install -e ".[build]"       # 打包 exe / 生成图标时额外安装
```

## 2. 常用命令

| 命令 | 说明 |
| --- | --- |
| `pytest` | 运行全部单元测试 |
| `pytest tests/test_crypto.py -v` | 只跑加解密测试 |
| `ruff check .` | 代码风格检查（E/F/W/I） |
| `ruff check --fix .` | 自动修复可修复问题 |
| `python scripts/make_fixture.py` | 重新生成脱敏测试夹具 |
| `python scripts/make_icon.py` | 重新生成图标（需 Pillow） |
| `python scripts/check_no_secrets.py` | 提交前敏感信息自检 |
| `python scripts/check_i18n.py` | 多语言 README 一致性检查 |
| `python scripts/sync_readme_langs.py` | 重新生成 10 种 README 的语言切换栏 |
| `python -m sqlark_decrypt` | 从源码启动 GUI |
| `python -m sqlark_decrypt decrypt tests/fixtures/demo-connections.xml` | CLI 冒烟测试 |

## 3. 构建 Windows exe

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# 产物：dist\SQLarkConnectionDecryptor.exe
```

说明：

- PyInstaller 打包的是 `scripts/launcher.py`（包内 `__main__.py` 使用相对导入，不能直接作为入口）；
- `--add-data "assets;assets"` 把图标打进 exe；
- 未签名的 exe 可能被杀软误报，发布时建议同时提供「便携版 zip」与「从源码运行」两种方式；
- 若需要控制台调试版：`scripts/build_exe.ps1 -Console`。

## 4. 发布清单（Release Checklist）

0. 确认 README 徽章与克隆地址指向实际仓库（本仓库为 `muemios/sqlark-connection-decryptor`）；
1. 更新版本号：`pyproject.toml` 的 `version`、`sqlark_decrypt/gui.py` 的 `APP_VERSION`；
2. 更新 [CHANGELOG.md](../CHANGELOG.md)；
3. 运行质量门禁：

   ```bash
   pytest
   ruff check .
   python scripts/check_no_secrets.py
   ```

4. 确认没有真实连接文件、导出结果、个人路径被提交（`git status` 应为干净状态）；
5. 构建 exe 并本机验证 `decrypt` 子命令；
6. 打 tag 并推送：`git tag -a v0.1.1 -m "v0.1.1" && git push origin v0.1.1`；
7. 在 GitHub Releases 中基于 tag 创建发布，上传 `dist/*.exe` 与便携版 zip，
   并附上 SHA256 校验值；
8. 发布后确认 CI 通过、Release 附件可下载。

## 5. 版本策略

- 遵循语义化版本：`MAJOR.MINOR.PATCH`；
- SQLark 更换加密算法 → `MAJOR` 升级，并在 CHANGELOG 注明“不兼容”；
- 新增导出格式 / 新字段解析 → `MINOR`；
- 修复问题 → `PATCH`。

## 6. 持续集成

`.github/workflows/ci.yml` 在 push / PR 时执行：

- 矩阵：Ubuntu + Windows × Python 3.9 / 3.12；
- `pip install -e ".[dev]"`；
- `ruff check .`；
- `pytest`；
- `python scripts/check_no_secrets.py`（防止把真实凭据提交进仓库）；
- `python scripts/check_i18n.py`（多语言 README 语言栏完整性）。

## 7. 调试技巧

- 想查看解密后的完整 JSON：`sqlark-decrypt decrypt FILE --raw`；
- 想验证某个文件的加密结构：先用 `crypto.decrypt_outer()` 解外层，再对 `password` 调用
  `crypto.decrypt_secret()`；
- GUI 卡住时先点「停止」，后台线程会在下一个目录/文件边界结束。

