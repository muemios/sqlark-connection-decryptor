"""Tkinter 图形界面：检索连接文件、展示明文密码、导出结果。

界面只做“交互与展示”，所有业务逻辑都来自同包的
:mod:`scanner` / :mod:`parser` / :mod:`export` 模块，方便单独测试和替换。
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional, Sequence

from . import __version__
from .export import records_to_tsv, write_csv, write_txt
from .models import ConnectionRecord
from .parser import NotConnectionFileError, parse_file
from .scanner import auto_detect, scan_directory

APP_TITLE = "SQLark 连接批量解密工具"
APP_VERSION = __version__


def _reveal(path: Path) -> None:
    """用系统文件管理器打开路径；无图形环境时静默忽略。"""
    try:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass


def _resource_path(name: str) -> Path:
    """兼容 PyInstaller 打包（sys._MEIPASS）与源码运行。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "assets" / name


class App:
    """主窗口。"""

    COLUMNS = (
        ("seq", "#", 46, "center"),
        ("name", "连接名", 210, "w"),
        ("host", "主机", 150, "w"),
        ("port", "端口", 62, "center"),
        ("user", "用户名", 110, "w"),
        ("dbtype", "数据库", 92, "center"),
        ("password", "密码", 180, "w"),
        ("source", "来源文件", 320, "w"),
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.records: list[ConnectionRecord] = []
        self.files: list[Path] = []
        self.parse_errors: list[str] = []
        self.stop_event = threading.Event()
        self.message_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self.worker: Optional[threading.Thread] = None
        self.view_records: list[ConnectionRecord] = []
        self.sort_key: Optional[str] = None
        self.sort_desc = False
        self.show_password = tk.BooleanVar(value=True)
        self.filter_text = tk.StringVar()

        self._build_ui()
        self._pump_messages()

    # ------------------------------------------------------------------ #
    # 界面构建
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry("1180x680")
        self.root.minsize(900, 520)
        try:
            self.root.iconbitmap(default=str(_resource_path("sqlark.ico")))
        except Exception:
            pass

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24, font=("Microsoft YaHei UI", 9))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"))
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 11, "bold"))

        header = ttk.Frame(self.root, padding=(12, 10, 12, 2))
        header.pack(fill="x")
        ttk.Label(header, text="SQLark 连接批量解密", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="  自动检索 / 手动选择目录，批量还原数据库明文密码",
            foreground="#666",
        ).pack(side="left")

        toolbar = ttk.Frame(self.root, padding=(12, 6))
        toolbar.pack(fill="x")
        self.btn_auto = ttk.Button(toolbar, text="① 自动检索", width=14, command=self.scan_auto)
        self.btn_dir = ttk.Button(toolbar, text="② 选择目录", width=14, command=self.choose_directory)
        self.btn_file = ttk.Button(toolbar, text="③ 选择文件", width=14, command=self.choose_files)
        self.btn_stop = ttk.Button(toolbar, text="停止", width=8, command=self.stop_scan, state="disabled")
        for button in (self.btn_auto, self.btn_dir, self.btn_file):
            button.pack(side="left", padx=(0, 6))
        self.btn_stop.pack(side="left", padx=6)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Checkbutton(
            toolbar, text="显示密码", variable=self.show_password, command=self.refresh_table
        ).pack(side="left")
        ttk.Label(toolbar, text="过滤：").pack(side="left", padx=(16, 4))
        self.filter_text.trace_add("write", lambda *_: self.refresh_table())
        self.filter_entry = ttk.Entry(toolbar, textvariable=self.filter_text, width=22)
        self.filter_entry.pack(side="left")

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(toolbar, text="导出 CSV", width=10, command=self.export_csv).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导出 TXT", width=10, command=self.export_txt).pack(side="left", padx=2)
        ttk.Button(toolbar, text="复制全部", width=10, command=self.copy_all).pack(side="left", padx=2)
        ttk.Button(toolbar, text="清空", width=8, command=self.clear).pack(side="left", padx=2)

        table_frame = ttk.Frame(self.root, padding=(12, 4))
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(
            table_frame, columns=[c[0] for c in self.COLUMNS], show="headings", selectmode="extended"
        )
        for column, title, width, anchor in self.COLUMNS:
            self.tree.heading(column, text=title, command=lambda c=column: self.sort_by(c))
            self.tree.column(column, width=width, anchor=anchor, stretch=column in ("name", "host", "source"))
        vertical = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.tag_configure("odd", background="#f7f9fc")
        self.tree.bind("<Double-1>", lambda _event: self.copy_selected_password())
        self.tree.bind("<Button-3>", self._show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制密码", command=self.copy_selected_password)
        self.context_menu.add_command(label="复制整行", command=self.copy_selected_row)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="打开所在文件夹", command=self._open_selected_folder)
        self.context_menu.add_command(label="打开文件", command=self._open_selected_file)

        status = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        status.pack(fill="x")
        self.progress = ttk.Progressbar(status, mode="indeterminate", length=140)
        self.progress.pack(side="left", padx=(0, 8))
        self.status_text = tk.StringVar(value="就绪：点击「自动检索」查找 SQLark 连接文件（F5）")
        ttk.Label(status, textvariable=self.status_text, foreground="#333").pack(side="left")

        self.root.bind("<F5>", lambda _e: self.scan_auto())
        self.root.bind("<Control-o>", lambda _e: self.choose_directory())
        self.root.bind("<Control-O>", lambda _e: self.choose_directory())
        self.root.bind("<Control-s>", lambda _e: self.export_csv())
        self.root.bind("<Control-S>", lambda _e: self.export_csv())
        self.root.bind("<Control-f>", lambda _e: self.filter_entry.focus_set())
        self.root.bind("<Control-F>", lambda _e: self.filter_entry.focus_set())

    # ------------------------------------------------------------------ #
    # 后台任务与消息泵
    # ------------------------------------------------------------------ #
    def _post(self, kind: str, payload: object = None) -> None:
        self.message_queue.put((kind, payload))

    def _pump_messages(self) -> None:
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                if kind == "status":
                    self.status_text.set(str(payload))
                elif kind == "busy":
                    self._set_busy(bool(payload))
                elif kind == "done":
                    self._set_busy(False)
                    files, records, errors = payload  # type: ignore[misc]
                    self._apply_results(files, records, errors)
                elif kind == "error":
                    self._set_busy(False)
                    messagebox.showerror(APP_TITLE, str(payload))
        except queue.Empty:
            pass
        self.root.after(120, self._pump_messages)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for button in (self.btn_auto, self.btn_dir, self.btn_file):
            button.configure(state=state)
        self.btn_stop.configure(state="normal" if busy else "disabled")
        if busy:
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.configure(mode="determinate", value=0)

    def _run_worker(self, func: Callable[[], None]) -> None:
        """在后台线程执行 func；执行期间禁用按钮、显示进度。"""
        if self.worker is not None and self.worker.is_alive():
            return
        self.stop_event.clear()
        self._set_busy(True)
        self.worker = threading.Thread(target=func, daemon=True)
        self.worker.start()

    # ------------------------------------------------------------------ #
    # 检索动作
    # ------------------------------------------------------------------ #
    def scan_auto(self) -> None:
        def job() -> None:
            try:
                self._post("status", "正在自动检索 SQLark 相关目录…")
                files = auto_detect(
                    progress=lambda message: self._post("status", message),
                    stop_event=self.stop_event,
                )
                self._post("done", (files, self._parse(files), []))
            except Exception:
                self._post("error", traceback.format_exc())

        self._run_worker(job)

    def choose_directory(self) -> None:
        folder = filedialog.askdirectory(title="选择要检索的目录（会递归查找连接文件）")
        if not folder:
            return

        def job() -> None:
            try:
                self._post("status", f"正在检索目录：{folder}")
                files = scan_directory(
                    Path(folder),
                    progress=lambda message: self._post("status", message),
                    stop_event=self.stop_event,
                )
                self._post("done", (files, self._parse(files), []))
            except Exception:
                self._post("error", traceback.format_exc())

        self._run_worker(job)

    def choose_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="选择 SQLark 连接文件",
            filetypes=[("连接文件", "connectionInfo.xml connection-server.xml"),
                       ("XML 文件", "*.xml"), ("所有文件", "*.*")],
        )
        if not selected:
            return
        self.load_files([Path(p) for p in selected])

    def load_files(self, files: Sequence[Path]) -> None:
        """直接加载指定文件（供 --open 参数与“选择文件”使用）。"""

        def job() -> None:
            try:
                self._post("status", f"正在解密 {len(files)} 个文件…")
                records, errors = [], []
                for path in files:
                    try:
                        records.extend(parse_file(path))
                    except (NotConnectionFileError, OSError) as exc:
                        errors.append(f"{path}: {exc}")
                self._post("done", (list(files), records, errors))
            except Exception:
                self._post("error", traceback.format_exc())

        self._set_busy(True)
        self.worker = threading.Thread(target=job, daemon=True)
        self.worker.start()

    def stop_scan(self) -> None:
        self.stop_event.set()
        self.status_text.set("正在停止…")

    @staticmethod
    def _parse(files: Sequence[Path]) -> list[ConnectionRecord]:
        records: list[ConnectionRecord] = []
        for path in files:
            try:
                records.extend(parse_file(path))
            except (NotConnectionFileError, OSError):
                continue
        return records

    def _apply_results(
        self,
        files: Sequence[Path],
        records: list[ConnectionRecord],
        errors: list[str],
    ) -> None:
        self.files = list(files)
        self.records = list(records)
        self.parse_errors = list(errors)
        self.refresh_table()
        with_password = sum(1 for record in records if record.password)
        message = (
            f"完成：找到 {len(files)} 个连接文件，解析出 {len(records)} 个连接，"
            f"其中 {with_password} 个含密码"
        )
        if errors:
            message += f"；{len(errors)} 个文件解析失败"
        self.status_text.set(message)

    # ------------------------------------------------------------------ #
    # 表格
    # ------------------------------------------------------------------ #
    def _visible_records(self) -> list[ConnectionRecord]:
        keyword = self.filter_text.get().strip().lower()
        if not keyword:
            return list(self.records)
        return [
            record
            for record in self.records
            if keyword in " ".join(
                str(value) for value in (
                    record.name, record.host, record.username, record.db_type,
                    record.password, record.source,
                )
            ).lower()
        ]

    def refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        records = self._visible_records()
        sort_attr = {
            "name": "name", "host": "host", "port": "port",
            "user": "username", "dbtype": "db_type", "password": "password", "source": "source",
        }.get(self.sort_key or "")
        if sort_attr:
            records.sort(key=lambda r: str(getattr(r, sort_attr) or "").lower(), reverse=self.sort_desc)
        self.view_records = records
        for index, record in enumerate(records, 1):
            password = record.password or ""
            if password and not self.show_password.get():
                password = "*" * min(len(password), 12)
            self.tree.insert(
                "", "end", iid=str(index),
                values=(index, record.name, record.host, "" if record.port is None else record.port,
                        record.username, record.db_type, password, str(record.source)),
                tags=("odd",) if index % 2 else (),
            )

    def sort_by(self, column: str) -> None:
        if self.sort_key == column:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_key, self.sort_desc = column, False
        self.refresh_table()

    # ------------------------------------------------------------------ #
    # 复制 / 打开
    # ------------------------------------------------------------------ #
    def _selected_records(self) -> list[ConnectionRecord]:
        selected: list[ConnectionRecord] = []
        for item in self.tree.selection():
            try:
                selected.append(self.view_records[int(item) - 1])
            except (IndexError, ValueError):
                continue
        return selected

    def _copy_to_clipboard(self, text: str, message: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_text.set(message)

    def copy_selected_password(self) -> None:
        passwords = [r.password for r in self._selected_records() if r.password]
        if not passwords:
            self.status_text.set("所选连接没有可用的密码")
            return
        self._copy_to_clipboard("\n".join(passwords), f"已复制 {len(passwords)} 个密码")

    def copy_selected_row(self) -> None:
        selected = self._selected_records()
        if selected:
            self._copy_to_clipboard(records_to_tsv(selected), f"已复制 {len(selected)} 条连接信息")

    def copy_all(self) -> None:
        if self.records:
            self._copy_to_clipboard(
                records_to_tsv(self.records), f"已复制全部 {len(self.records)} 条连接信息"
            )

    def _open_selected_folder(self) -> None:
        selected = self._selected_records()
        if selected and selected[0].source.parent.is_dir():
            _reveal(selected[0].source.parent)

    def _open_selected_file(self) -> None:
        selected = self._selected_records()
        if selected and selected[0].source.is_file():
            _reveal(selected[0].source)

    def _show_context_menu(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    # ------------------------------------------------------------------ #
    # 导出 / 清空
    # ------------------------------------------------------------------ #
    def export_csv(self) -> None:
        self._export(write_csv, "CSV 文件", ".csv", "SQLark连接密码.csv")

    def export_txt(self) -> None:
        self._export(write_txt, "文本文件", ".txt", "SQLark连接密码.txt")

    def _export(self, writer: Callable[..., int], label: str, suffix: str, default_name: str) -> None:
        if not self.records:
            messagebox.showinfo(APP_TITLE, "还没有可导出的数据")
            return
        path = filedialog.asksaveasfilename(
            title=f"导出 {label}", defaultextension=suffix,
            filetypes=[(label, f"*{suffix}")], initialfile=default_name,
        )
        if not path:
            return
        count = writer(self.records, Path(path))
        self.status_text.set(f"已导出 {count} 条到 {path}")

    def clear(self) -> None:
        self.records, self.files, self.parse_errors = [], [], []
        self.refresh_table()
        self.status_text.set("已清空")


def run(initial_files: Optional[Sequence[Path]] = None, autoload: bool = False) -> None:
    """启动 GUI。

    Args:
        initial_files: 启动时直接加载的文件。
        autoload: 启动后是否立即执行自动检索。
    """
    root = tk.Tk()
    app = App(root)
    if initial_files:
        root.after(200, lambda: app.load_files(list(initial_files)))
    elif autoload:
        root.after(300, app.scan_auto)
    root.mainloop()


