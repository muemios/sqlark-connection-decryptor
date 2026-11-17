# Pull Request

## 变更类型

- [ ] feat：新功能
- [ ] fix：修复缺陷
- [ ] refactor：重构（不改变行为）
- [ ] docs：仅文档
- [ ] test：测试相关
- [ ] chore：构建 / 依赖 / 杂项

## 变更说明

<!-- 这个 PR 做了什么？为什么需要？ -->

## 关联 Issue

Closes #

## 检查清单

- [ ] 新增/修改的行为有对应测试
- [ ] `pytest` 全部通过
- [ ] `ruff check .` 无告警
- [ ] `python scripts/check_no_secrets.py` 通过
- [ ] `python scripts/check_i18n.py` 通过（改动 README 时）
- [ ] 未提交真实连接文件、导出的密码、个人路径或二进制产物
- [ ] 文档（README / docs / CHANGELOG）已同步更新
- [ ] 测试数据全部为虚构数据（RFC 5737 文档网段 + 演示密码）
