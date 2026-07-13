from .ports import JsonMap

PYTHON_HEART_SOURCE = """from math import cos, pi, sin
from pathlib import Path
from sys import argv

from PIL import Image, ImageChops, ImageDraw, ImageFilter


def heart_points(size: int) -> list[tuple[float, float]]:
    scale, center, vertical = size / 40, size / 2, size * 0.47
    return [
        (
            center + 16 * sin(angle) ** 3 * scale,
            vertical - (13 * cos(angle) - 5 * cos(2 * angle) - 2 * cos(3 * angle) - cos(4 * angle)) * scale,
        )
        for angle in (2 * pi * index / 720 for index in range(720))
    ]


def gradient(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(image)
    for y in range(size):
        depth = y / max(size - 1, 1)
        color = (255 - int(45 * depth), 143 - int(91 * depth), 166 - int(82 * depth), 255)
        draw.line((0, y, size, y), fill=color)
    return image


def layer(mask: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", mask.size, (*color, 0))
    image.putalpha(mask)
    return image


def render_heart(output: Path, size: int = 360) -> None:
    work = size * 3
    mask = Image.new("L", (work, work), 0)
    points = heart_points(work)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    canvas = Image.new("RGBA", (work, work), (0, 0, 0, 0))
    shadow = Image.new("L", (work, work), 0)
    shadow.paste(mask.filter(ImageFilter.GaussianBlur(work // 32)), (0, work // 45))
    canvas.alpha_composite(layer(shadow.point(lambda value: value // 3), (105, 43, 72)))
    fill = gradient(work)
    fill.putalpha(mask)
    canvas.alpha_composite(fill)
    highlight = Image.new("L", (work, work), 0)
    ImageDraw.Draw(highlight).ellipse((work * 0.22, work * 0.16, work * 0.53, work * 0.47), fill=86)
    canvas.alpha_composite(layer(ImageChops.multiply(mask, highlight), (255, 255, 255)))
    outline = Image.new("RGBA", (work, work), (0, 0, 0, 0))
    ImageDraw.Draw(outline).line(points + [points[0]], fill=(143, 34, 65, 130), width=work // 150, joint="curve")
    canvas.alpha_composite(outline)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((size, size), Image.Resampling.LANCZOS).save(output)


def main() -> None:
    output = Path(argv[1])
    render_heart(output)
    print(f"image={output}")


if __name__ == "__main__":
    main()
"""


def heart_reply(execution: JsonMap) -> JsonMap:
    status = _status(execution)
    output = _output(execution)
    artifact = str(execution.get("artifact_path", "")).strip()
    artifact_note = "已生成本地 PNG，原生客户端会直接显示它。" if artifact else "图像文件没有生成，错误信息已在执行输出中保留。"
    reply = f"已使用本机 Python 在临时目录执行：{status}。{artifact_note}\n\n```python\n{PYTHON_HEART_SOURCE}```\n\n```text\n{output}\n```"
    return {"reply": reply, "mode": "executed_python_example", "writes_project": False, "execution": execution, "artifact_path": artifact, "passed": bool(execution.get("passed"))}


def _status(execution: JsonMap) -> str:
    if bool(execution.get("timed_out")):
        return "超时，进程已终止"
    if bool(execution.get("passed")):
        return "成功"
    return f"失败（退出码 {execution.get('exit_code', 'unknown')}）"


def _output(execution: JsonMap) -> str:
    stdout = str(execution.get("stdout", "")).rstrip()
    stderr = str(execution.get("stderr", "")).rstrip()
    artifact_error = str(execution.get("artifact_error", "")).rstrip()
    return stdout or stderr or artifact_error or "Python 没有返回输出。"
