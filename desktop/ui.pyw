import threading
import time
import re
from pathlib import Path
from tkinter import BooleanVar, Button, Checkbutton, Entry, Frame, Label, PhotoImage, TclError, Tk, Text, END, WORD

from backend_bridge import request
from memory_window import MemoryWindow
from sky_theme import BLUE, CARD, INK, MUTED, SKY, SkyHeader

SESSION = f"desktop_{int(time.time())}"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "backend" / "runtime_artifacts"
TASK_LABELS = {"planned": "已计划", "running": "运行中", "verified": "已验证", "completed": "已完成", "needs_attention": "待处理", "failed": "失败"}


class FengqingApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("风轻思念浓")
        self._fit_window()
        self.mode = "chat"
        self.allow_write = BooleanVar(value=False)
        self.artifacts: list[PhotoImage] = []
        self._build()
        self._status()
        self._say("风轻思念浓", "我在。对话里需要检查、测试或推进项目时，我会受控调用自己的智能体。")

    def _fit_window(self) -> None:
        self.root.geometry("900x620+40+40")
        self.root.minsize(720, 520)
        self.root.state("zoomed")

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        self.root.configure(bg=SKY)
        SkyHeader(self.root).pack(fill="x")
        self.status = Label(self.root, text="检查中", bg=SKY, fg=MUTED, font=("Segoe UI", 10))
        self.status.pack(anchor="e", padx=18, pady=(0, 4))
        self._bottom()
        self._tools()
        self.body = Text(self.root, wrap=WORD, bg=CARD, fg=INK, relief="flat", padx=22, pady=18)
        self.body.pack(fill="both", expand=True)
        self.body.tag_configure("who", foreground=BLUE, spacing1=10, font=("Segoe UI", 10, "bold"))
        self.body.tag_configure("line", foreground=INK, spacing3=12, font=("Segoe UI", 11))

    def _bottom(self) -> None:
        self.bottom = Frame(self.root, bg=SKY, padx=16, pady=12)
        self.bottom.pack(side="bottom", fill="x")
        self.entry = Entry(self.bottom, relief="flat", bg=CARD, fg=INK, font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, ipady=12)
        self.entry.bind("<Return>", lambda _event: self._submit())
        Button(self.bottom, text="发送", command=self._submit, bg=BLUE, fg="#ffffff", relief="flat").pack(side="right", padx=(10, 0), ipadx=18, ipady=9)

    def _tools(self) -> None:
        self.tools = Frame(self.root, bg=SKY, padx=12, pady=8)
        self.tools.pack(side="bottom", fill="x")
        Button(self.tools, text="状态", command=self._show_runtime, bg=CARD, fg=INK, relief="flat").pack(side="left")
        Button(self.tools, text="对话", command=lambda: self._mode("chat"), bg=CARD, fg=INK, relief="flat").pack(side="left")
        Button(self.tools, text="智能体", command=lambda: self._mode("agent"), bg=CARD, fg=INK, relief="flat").pack(side="left", padx=8)
        Button(self.tools, text="进度", command=self._show_progress, bg=CARD, fg=INK, relief="flat").pack(side="left", padx=4)
        Button(self.tools, text="记忆", command=lambda: MemoryWindow(self.root, request), bg=CARD, fg=INK, relief="flat").pack(side="left", padx=4)
        Button(self.tools, text="任务", command=self._show_tasks, bg=CARD, fg=INK, relief="flat").pack(side="left", padx=4)
        Button(self.tools, text="历史", command=self._show_history, bg=CARD, fg=INK, relief="flat").pack(side="left", padx=4)
        Checkbutton(self.tools, text="允许写入", variable=self.allow_write, bg=SKY, fg=MUTED).pack(side="left", padx=4)

    def _status(self) -> None:
        data = request("GET", "/api/v1/status") or {}
        model = f"{data.get('provider', 'offline')} / {data.get('model', 'unknown')}"
        self.status.config(text=f"{model} | {_runtime_label(data)} | {data.get('progress_stage', '未读取进度')}")

    def _show_runtime(self) -> None:
        data = request("GET", "/api/v1/status") or {}
        runtime = data.get("model_runtime", {})
        runtime = runtime if isinstance(runtime, dict) else {}
        lines = [
            f"提供方：{data.get('provider', 'unknown')}",
            f"配置模型：{data.get('model', 'unknown')}",
            f"当前状态：{_runtime_label(data)}",
            f"说明：{runtime.get('detail', '没有返回诊断说明。')}",
        ]
        models = runtime.get("available_models", [])
        if isinstance(models, list):
            lines.append(f"本机已下载：{', '.join(str(item) for item in models) or '无'}")
        self._say("运行状态", "\n".join(lines))

    def _show_progress(self) -> None:
        data = request("GET", "/api/v1/progress") or {}
        self._say("进度", self._progress_text(data))

    def _show_history(self) -> None:
        data = request("GET", "/api/v1/history?limit=12") or {}
        items = data.get("items", []) if isinstance(data.get("items"), list) else []
        text = "\n".join(self._history_line(item) for item in items if isinstance(item, dict))
        self._say("历史", text or "还没有智能体执行或记忆变更记录。")

    def _show_tasks(self) -> None:
        data = request("GET", "/api/v1/tasks?limit=8") or {}
        items = data.get("items", []) if isinstance(data.get("items"), list) else []
        text = "\n".join(self._task_line(item) for item in items if isinstance(item, dict))
        self._say("任务", text or "还没有可追溯的智能体任务。")

    def _task_line(self, task: dict[str, object]) -> str:
        task_id = str(task.get("id", ""))[:8]
        status = TASK_LABELS.get(str(task.get("status", "unknown")), "未知")
        instruction = str(task.get("instruction", ""))[:72]
        return f"{task_id}  {status}：{instruction}"

    def _history_line(self, item: dict[str, object]) -> str:
        labels = {"agent_run": "智能体", "task_state": "任务状态", "memory_added": "新增记忆", "memory_updated": "修改记忆", "memory_deleted": "删除记忆"}
        data = item.get("data", {}) if isinstance(item.get("data"), dict) else {}
        detail = data.get("instruction") or _memory_detail(data)
        return f"{item.get('time', '')}  {labels.get(str(item.get('kind')), str(item.get('kind')))}：{detail}"

    def _progress_text(self, data: dict[str, object]) -> str:
        rows = [str(data.get("reply", "暂无进度"))]
        for item in data.get("milestones", []) if isinstance(data.get("milestones"), list) else []:
            if isinstance(item, dict):
                rows.append(f"- {item.get('name')}: {item.get('proof')}")
        return "\n".join(rows)

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
        payload = self._agent_payload(text) if self.mode == "agent" else self._chat_payload(text)
        data = request("POST", "/api/v1/agent" if self.mode == "agent" else "/api/v1/chat", payload)
        reply = self._agent_text(data) if self.mode == "agent" else str((data or {}).get("reply", "连接中断。"))
        artifact = _agent_artifact(data) if self.mode == "agent" else _reply_artifact(reply)
        self.root.after(0, lambda: self._say("风轻思念浓", reply, artifact))

    def _agent_payload(self, text: str) -> dict[str, object]:
        return {"instruction": text, "allow_write": self.allow_write.get()}

    def _chat_payload(self, text: str) -> dict[str, object]:
        return {"session_id": SESSION, "message": text, "allow_agent_write": self.allow_write.get()}

    def _agent_text(self, data: dict[str, object] | None) -> str:
        result = (data or {}).get("result", {})
        if isinstance(result, dict) and isinstance(result.get("visible_progress"), dict):
            return self._format_visible_agent(result)
        rows = result.get("results", []) if isinstance(result, dict) else []
        first = rows[0].get("result", {}) if rows and isinstance(rows[0], dict) else {}
        return self._format_agent_result(first if isinstance(first, dict) else {})

    def _format_visible_agent(self, result: dict[str, object]) -> str:
        code = _code_example_reply(result)
        if code:
            return code
        visible = result["visible_progress"]
        lines = [str(visible.get("summary", "")), f"下一步：{visible.get('next', '')}"]
        resource = visible.get("resource_balance", {})
        if isinstance(resource, dict):
            reasons = resource.get("reasons", [])
            reason_text = "；".join(str(item) for item in reasons) if isinstance(reasons, list) else ""
            lines.append(f"资源均衡：{resource.get('mode', 'unknown')} {reason_text}".rstrip())
        for item in visible.get("steps", []) if isinstance(visible.get("steps"), list) else []:
            if isinstance(item, dict):
                lines.append(f"- {item.get('action')} / {item.get('status')}: {item.get('evidence')}")
        return "\n".join(lines)

    def _format_agent_result(self, result: dict[str, object]) -> str:
        lines = [str(result.get("reply") or result or "智能体已完成任务。")]
        if isinstance(result.get("game_project"), dict):
            lines.append(f"雨城映射：{result['game_project'].get('reply')}")
        if isinstance(result.get("first_sprint"), dict):
            lines.append(f"第一步：{result['first_sprint'].get('name')}")
        return "\n".join(lines)

    def _say(self, who: str, text: str, artifact: str = "") -> None:
        self.body.insert(END, f"{who}\n", "who")
        self._insert_artifact(artifact)
        self.body.insert(END, f"{text}\n\n", "line")
        self.body.see(END)

    def _insert_artifact(self, value: str) -> None:
        path = Path(value)
        if path.suffix.lower() != ".png" or not path.is_file() or not _is_runtime_artifact(path):
            return
        try:
            image = PhotoImage(file=str(path))
        except TclError:
            return
        self.artifacts.append(image)
        self.body.image_create(END, image=image, padx=12, pady=8)
        self.body.insert(END, "\n", "line")


def _memory_detail(data: dict[str, object]) -> str:
    item = data.get("memory") or data.get("after") or data.get("before") or {}
    return str(item.get("text", "")) if isinstance(item, dict) else ""


def _code_example_reply(result: dict[str, object]) -> str:
    rows = result.get("results", [])
    first = rows[0].get("result", {}) if rows and isinstance(rows[0], dict) else {}
    reply = first.get("reply") if isinstance(first, dict) else None
    return reply if isinstance(reply, str) and first.get("mode") in {"code_example", "executed_python_example"} else ""


def _agent_artifact(data: dict[str, object] | None) -> str:
    result = (data or {}).get("result", {})
    rows = result.get("results", []) if isinstance(result, dict) else []
    first = rows[0].get("result", {}) if rows and isinstance(rows[0], dict) else {}
    execution = first.get("execution", {}) if isinstance(first, dict) else {}
    path = execution.get("artifact_path", "") if isinstance(execution, dict) else ""
    return path if isinstance(path, str) else ""


def _reply_artifact(reply: str) -> str:
    match = re.search(r"^image=(.+\.png)$", reply, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _is_runtime_artifact(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(ARTIFACT_DIR.resolve())
    except OSError:
        return False


def _runtime_label(data: dict[str, object]) -> str:
    runtime = data.get("model_runtime", {})
    state = str(runtime.get("state", "unknown")) if isinstance(runtime, dict) else "unknown"
    labels = {
        "ready": "模型就绪",
        "model_missing": "模型未下载",
        "unreachable": "Ollama 未连接",
        "service_error": "Ollama 服务错误",
        "invalid_response": "模型响应异常",
        "configured_remote": "远程模型待验证",
        "diagnostic_failed": "模型诊断失败",
    }
    return labels.get(state, "模型状态未知")
