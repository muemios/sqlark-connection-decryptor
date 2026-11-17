# 架构设计

本文说明项目的模块划分、数据流与关键设计决策，方便不同阶段的开发者快速上手。

## 1. 总体结构

```
                 ┌────────────────────────────────────────────┐
                 │              用户交互层                      │
                 │   cli.py (scan / decrypt)   gui.py (Tkinter) │
                 └───────────────┬────────────────────────────┘
                                 │ 调用
                 ┌───────────────▼────────────────────────────┐
                 │              业务编排层                      │
                 │   scanner.py（找文件）  parser.py（解析+解密） │
                 └───────┬───────────────────────┬────────────┘
                         │                       │
        ┌────────────────▼──────┐      ┌─────────▼──────────────┐
        │  crypto.py（AES 原语） │      │ export.py（CSV/TXT/JSON）│
        └───────────────────────┘      └────────────────────────┘
                         │
                 ┌───────▼────────┐
                 │ models.py 数据模型│
                 └────────────────┘
```

依赖方向始终向下：**GUI/CLI 不直接操作字节，crypto 不感知 XML 与业务字段**。

## 2. 模块职责

| 模块 | 职责 | 不负责 |
| --- | --- | --- |
| `crypto.py` | Base64 + AES-CBC + PKCS5 的加解密；外层/内层两个入口 | XML、字段语义、错误展示 |
| `models.py` | `ConnectionRecord` 数据结构、`endpoint` / `to_row` 等派生属性 | 任何 IO |
| `parser.py` | 读取 XML、提取 `<CONNECTION>`、组合两层解密、逐条容错 | 找文件、界面 |
| `scanner.py` | 遍历目录、识别连接文件、去重、可中断 | 解密 |
| `export.py` | CSV / TXT / TSV / JSON 输出 | 界面交互 |
| `cli.py` | 子命令、参数解析、退出码 | 业务实现 |
| `gui.py` | Tkinter 界面、后台线程、消息泵 | 业务实现、加解密 |

## 3. 数据流

### 3.1 图形界面

```
点击「自动检索」
  → 后台线程 scanner.auto_detect()        # 产出文件路径列表
  → parser.parse_file()                   # 逐文件解析
      → crypto.decrypt_outer()            # 第 1 层
      → crypto.decrypt_secret()           # 第 2 层（password/ssh/ssl）
  → 消息队列回传主线程                     # Tk 只能在主线程更新 UI
  → refresh_table()                       # 填充表格
  → 用户导出 export.write_csv/txt()        # 或复制到剪贴板
```

### 3.2 命令行

```
sqlark-decrypt decrypt FILE...
  → cli._collect() → parser.parse_file()
  → 标准输出表格 / 写文件
  → 退出码：0 成功，1 无有效记录，2 部分文件失败
```

## 4. 关键设计决策

1. **分层而非平铺**：加解密、解析、检索、展示各自独立。新增一种文件格式只需要改 `parser.py`，
   新增一种导出只需要改 `export.py`。
2. **逐条容错**：单条连接解析失败只在该条 `ConnectionRecord.error` 上记录，不影响整份文件；
   单个文件失败只在 CLI 的 stderr 提示，不中断批量处理。
3. **快速文件识别**：`is_connection_xml()` 只读文件头 64 KB + 尾部 4 KB 检查
   `<CONNECTIONS>` / `</CONNECTIONS>`，避免把每个 XML 全量解析。
4. **可中断的检索**：`scanner` 接受 `threading.Event`，GUI 的「停止」按钮可以立即打断遍历。
5. **GUI 线程模型**：所有磁盘/解密操作在 `threading.Thread` 中执行，结果经 `queue.Queue`
   回到主线程（Tk 不是线程安全的）。任务执行期间禁用按钮，避免并发修改表格。
6. **延迟导入**：`cli.py` 只在执行 `gui` 子命令时才导入 tkinter，
   这样无图形环境（服务器、CI）也能使用命令行功能。
7. **测试优先覆盖纯逻辑**：crypto / parser / scanner / export / cli 都能在无显示器环境测试；
   GUI 只做薄封装，人工验收。

## 5. 错误处理策略

| 场景 | 行为 |
| --- | --- |
| 文件不是连接 XML | `NotConnectionFileError`，CLI 提示并跳过 |
| 文件不存在/无权限 | `OSError`，提示并跳过 |
| `<connectionDetail>` 解密失败 | 记录 `error`，保留明文外层字段（名称/主机等） |
| `superAttr` 解密失败 | 忽略（不影响密码） |
| `password` 无 `salt` | 视为未加密，原样返回 |
| 密码为空 | `password = None`，表格显示空白 |

## 6. 测试策略

- `tests/fixtures/demo-connections.xml`：由 `scripts/make_fixture.py` 生成的**全虚构**连接文件，
  覆盖 Oracle/MySQL/PostgreSQL 三种驱动和嵌套 SSH/SSL 字段；
- `test_crypto.py`：加解密回环、非法长度/填充、确定性；
- `test_parser.py`：字段提取、XML 转义、损坏密文容错；
- `test_scanner.py`：深度限制、跳过重目录、停止信号、去重；
- `test_export.py` / `test_cli.py`：导出格式与退出码。

## 7. 扩展点

- **新增数据库驱动**：若其连接文件结构相同则无需改动；如需解析额外字段，扩展 `parser.py` 的 `_build_record`。
- **新增导出格式**：在 `export.py` 增加 `write_xxx()`，并在 `cli.py` / `gui.py` 各加一个入口。
- **新增界面**：任何界面只要调用 `scanner` + `parser` + `export` 即可，不必重复实现解密。
