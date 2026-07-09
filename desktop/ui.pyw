import threading
import time
from tkinter import BooleanVar, Button, Checkbutton, Entry, Frame, Label, Tk, Text, END, WORD

from backend_bridge import request

SESSION = f"desktop_{int(time.time())}"


class FengqingApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("风轻思念浓")
        self.root.geometry("980x720")
        self.mode = "chat"
        self.allow_write = BooleanVar(value=False)
        self._build()
        self._status()
        self._say("风轻思念浓", "我在。现在这是原生桌面窗口，不是浏览器页。")

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        self.root.configure(bg="#f5f5f7")
        self.top = Frame(self.root, bg="#ffffff", padx=16, pady=12)
        self.top.pack(fill="x")
        Label(self.top, text="风轻思念浓", bg="#ffffff", fg="#1d1d1f", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.status = Label(self.top, text="检查中", bg="#ffffff", fg="#6e6e73", font=("Segoe UI", 10))
        self.status.pack(side="right")
        self.body = Text(self.root, wrap=WORD, bg="#f5f5f7", fg="#1d1d1f", relief="flat", padx=18, pady=16)
        self.body.pack(fill="both", expand=True)
        self._bottom()
        self._tools()

    def _bottom(self) -> None:
        self.bottom = Frame(self.root, bg="#ffffff", padx=14, pady=12)
        self.bottom.pack(fill="x")
        self.entry = Entry(self.bottom, relief="flat", font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, ipady=12)
        self.entry.bind("<Return>", lambda _event: self._submit())
        Button(self.bottom, text="发送", command=self._submit, bg="#007aff", fg="#ffffff", relief="flat").pack(side="right", padx=(10, 0), ipadx=18, ipady=9)

    def _tools(self) -> None:
        self.tools = Frame(self.root, bg="#ffffff", padx=10, pady=8)
        self.tools.pack(fill="x")
        Button(self.tools, text="对话", command=lambda: self._mode("chat"), relief="flat").pack(side="left")
        Button(self.tools, text="智能体", command=lambda: self._mode("agent"), relief="flat").pack(side="left")
        Checkbutton(self.tools, text="允许写入", variable=self.allow_write, bg="#ffffff").pack(side="left", padx=10)

    def _status(self) -> None:
        data = request("GET", "/api/v1/status") or {}
        self.status.config(text=f"{data.get('provider', 'offline')} · {data.get('model', 'unknown')}")

    def _mode(self, mode: str) -> None:
        self.mode = mode
        self._say("系统", f"已切换到{'智能体' if mode == 'agent' else '对话'}模式。")

    def _submit(self) -> None:
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, END)
            self._say("你", text)
            threading.Thread(target=self._send, args=(text,), daemon=True).start()

    def _send(self, text: str) -> None:
        data = request("POST", "/api/v1/agent", self._agent_payload(text)) if self.mode == "agent" else request("POST", "/api/v1/chat", {"session_id": SESSION, "message": text})
        reply = self._agent_text(data) if self.mode == "agent" else str((data or {}).get("reply", "连接中断。"))
        self.root.after(0, lambda: self._say("风轻思念浓", reply))

    def _agent_payload(self, text: str) -> dict[str, object]:
        return {"instruction": text, "allow_write": self.allow_write.get()}

    def _agent_text(self, data: dict[str, object] | None) -> str:
        result = (data or {}).get("result", {})
        rows = result.get("results", []) if isinstance(result, dict) else []
        first = rows[0].get("result", {}) if rows and isinstance(rows[0], dict) else {}
        return str(first.get("reply") or first or "智能体已完成任务。")

    def _say(self, who: str, text: str) -> None:
        self.body.insert(END, f"{who}\n{text}\n\n")
        self.body.see(END)
