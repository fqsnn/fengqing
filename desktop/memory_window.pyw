from collections.abc import Callable
from tkinter import Button, Frame, Label, Listbox, Misc, Toplevel, messagebox, simpledialog

from sky_theme import BLUE, CARD, INK, MUTED, SKY

RequestFn = Callable[[str, str, dict[str, object] | None], dict[str, object] | None]


class MemoryWindow:
    def __init__(self, parent: Misc, request: RequestFn) -> None:
        self.request = request
        self.items: list[dict[str, object]] = []
        self.window = Toplevel(parent)
        self.window.title("私人记忆")
        self.window.geometry("760x500")
        self._build()
        self._load()

    def _build(self) -> None:
        self.window.configure(bg=SKY)
        Label(self.window, text="私人记忆", bg=SKY, fg=INK, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        Label(self.window, text="只保存在本机，可查看、修正和删除", bg=SKY, fg=MUTED).pack(anchor="w", padx=18)
        self.listbox = Listbox(self.window, bg=CARD, fg=INK, relief="flat", font=("Segoe UI", 10), activestyle="none")
        self.listbox.pack(fill="both", expand=True, padx=18, pady=14)
        tools = Frame(self.window, bg=SKY)
        tools.pack(fill="x", padx=18, pady=(0, 16))
        for text, command in (("新增", self._add), ("修改", self._edit), ("删除", self._delete), ("刷新", self._load)):
            Button(tools, text=text, command=command, bg=BLUE if text == "新增" else CARD, fg="#ffffff" if text == "新增" else INK, relief="flat").pack(side="left", padx=(0, 8), ipadx=12, ipady=5)

    def _load(self) -> None:
        data = self.request("GET", "/api/v1/memories", None) or {}
        raw = data.get("items", [])
        self.items = [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
        self.listbox.delete(0, "end")
        for item in self.items:
            self.listbox.insert("end", f"{item.get('text')}  [{item.get('source')}]  {item.get('id')}")

    def _selected(self) -> dict[str, object] | None:
        selection = self.listbox.curselection()
        if selection:
            return self.items[int(selection[0])]
        messagebox.showinfo("私人记忆", "请先选择一条记忆。", parent=self.window)
        return None

    def _add(self) -> None:
        text = simpledialog.askstring("新增记忆", "写下要记住的内容", parent=self.window)
        if text and text.strip():
            self.request("POST", "/api/v1/memories", {"text": text.strip()})
            self._load()

    def _edit(self) -> None:
        item = self._selected()
        if not item:
            return
        text = simpledialog.askstring("修改记忆", "修正这条内容", initialvalue=str(item.get("text", "")), parent=self.window)
        if text and text.strip():
            self.request("PATCH", f"/api/v1/memories/{item.get('id')}", {"text": text.strip()})
            self._load()

    def _delete(self) -> None:
        item = self._selected()
        if not item or not messagebox.askyesno("删除记忆", "确定删除选中的私人记忆？", parent=self.window):
            return
        self.request("DELETE", f"/api/v1/memories/{item.get('id')}", None)
        self._load()
