from .ports import JsonMap

PYTHON_HEART_SOURCE = """def heart() -> None:
    rows = (
        "         ****       ****",
        "        *******   *******",
        "       ********* *********",
        "      *********************",
        "     ***********************",
        "    *************************",
        "   ***************************",
        "  *****************************",
        " *******************************",
        "*********************************",
        " *******************************",
        "  *****************************",
        "   ***************************",
        "    *************************",
        "     ***********************",
        "      *********************",
        "       *******************",
        "        *****************",
        "         ***************",
        "          *************",
        "           ***********",
        "            *********",
        "             *******",
        "              *****",
        "               ***",
        "                *",
    )
    for row in rows:
        print(row.rstrip())


heart()
"""


def heart_reply(execution: JsonMap) -> JsonMap:
    status = _status(execution)
    output = _output(execution)
    reply = f"```python\n{PYTHON_HEART_SOURCE}```\n\n已使用本机 Python 在临时目录执行：{status}。\n```text\n{output}\n```"
    return {"reply": reply, "mode": "executed_python_example", "writes_project": False, "execution": execution, "passed": bool(execution.get("passed"))}


def _status(execution: JsonMap) -> str:
    if bool(execution.get("timed_out")):
        return "超时，进程已终止"
    if bool(execution.get("passed")):
        return "成功"
    return f"失败（退出码 {execution.get('exit_code', 'unknown')}）"


def _output(execution: JsonMap) -> str:
    stdout = str(execution.get("stdout", "")).rstrip()
    stderr = str(execution.get("stderr", "")).rstrip()
    return stdout or stderr or "Python 没有返回输出。"
