# 贡献指南

感谢你愿意参与改进本项目！请先阅读以下约定。

## 1. 先讨论，再动手

- 修 bug 或小改动：直接提 Pull Request 即可；
- 新功能 / 改变行为 / 兼容性调整：先开 Issue 讨论，避免白做；
- 安全问题：**不要公开提 Issue**，请按 [SECURITY.md](SECURITY.md) 私密报告。

## 2. 提交 Issue 时

- 说明 SQLark 版本、操作系统、Python 版本；
- 提供复现步骤与报错信息；
- **绝对不要上传真实的连接文件、导出的 CSV/JSON、数据库密码或内网地址**。
  如需示例，请用 `scripts/make_fixture.py` 生成脱敏文件。

## 3. Pull Request 流程

```bash
git checkout -b feat/your-feature      # 分支名：feat/ fix/ docs/ refactor/
# ... 修改代码 ...
pytest
ruff check .
python scripts/check_no_secrets.py
git commit -m "feat: 简要说明"
git push origin feat/your-feature
```

PR 描述请填写模板中的内容，确保：

- [ ] 新增/修改的行为有对应测试
- [ ] `pytest` 全部通过
- [ ] `ruff check .` 无告警
- [ ] 未提交真实凭据、个人路径、二进制产物
- [ ] 文档（README / docs / CHANGELOG）已同步更新

## 4. 代码风格

- 遵循 PEP 8，行宽 110（见 `pyproject.toml` 的 ruff 配置）；
- 所有公开函数/类写 docstring，说明参数、返回值与异常；
- 使用类型注解；`from __future__ import annotations` 保持 3.9 兼容；
- 库代码中**不要 print / 弹窗**，通过返回值、日志回调或异常表达结果；
- 加解密、解析、检索等纯逻辑必须可独立测试，不依赖 GUI。

## 5. 测试数据规则

- 只允许**虚构数据**：主机使用 RFC 5737 文档网段
  （`192.0.2.0/24`、`198.51.100.0/24`、`203.0.113.0/24`），用户名/密码使用明显示例值；
- 新增夹具请修改 `scripts/make_fixture.py` 后重新生成，不要手写二进制密文；
- `scripts/check_no_secrets.py` 与 CI 会拦截疑似真实 IP、邮箱、用户目录等。

## 6. 提交信息

使用 [Conventional Commits](https://www.conventionalcommits.org/) 前缀：

| 前缀 | 用途 |
| --- | --- |
| `feat:` | 新功能 |
| `fix:` | 修复缺陷 |
| `docs:` | 仅文档 |
| `refactor:` | 重构（不改变行为） |
| `test:` | 测试相关 |
| `chore:` | 构建/依赖/杂项 |

## 7. 翻译 README

- 支持 10 种语言，语言清单统一维护在 `scripts/readme_langs.py` 的 `LANGUAGES` 中；
- 新增语言：在该清单追加一行，新建 `README.<语言代码>.md`（可先写 `<!-- LANG-BAR -->` 占位），
  然后运行 `python scripts/sync_readme_langs.py` 自动生成语言切换栏；
- 语言栏由脚本生成，**不要手工修改**；内容翻译请保持与中文版结构一致；
- 提交前运行 `python scripts/check_i18n.py`，CI 也会执行该检查。

## 8. 行为准则

参与本项目即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
