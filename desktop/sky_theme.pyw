from tkinter import Canvas, Misc

SKY = "#dff4ff"
SKY_DEEP = "#a8d9ff"
CLOUD = "#ffffff"
SUN = "#ffd77a"
CARD = "#fafdff"
INK = "#1d2b36"
MUTED = "#5f7480"
BLUE = "#1683e2"


class SkyHeader(Canvas):
    def __init__(self, master: Misc) -> None:
        super().__init__(master, height=128, bd=0, highlightthickness=0)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _event: object | None = None) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 1)
        self._bands(width)
        self._sun(width - 86, 34)
        self._cloud(width * 0.20, 58, 1.08)
        self._cloud(width * 0.78, 78, 0.88)
        self._breeze(width)
        self._butterfly(width * 0.58, 74, 0.9)
        self._butterfly(width * 0.68, 44, 0.72)
        self.create_text(28, 42, text="风轻思念浓", anchor="w", fill=INK, font=("Segoe UI", 21, "bold"))
        self.create_text(30, 76, text="fqsnn · morning sky", anchor="w", fill=MUTED, font=("Segoe UI", 10))

    def _bands(self, width: int) -> None:
        steps = 16
        for index in range(steps):
            color = self._blend(index / (steps - 1))
            self.create_rectangle(0, index * 8, width, (index + 1) * 8, fill=color, outline=color)

    def _blend(self, ratio: float) -> str:
        start = (223, 244, 255)
        end = (168, 217, 255)
        rgb = [round(start[i] + (end[i] - start[i]) * ratio) for i in range(3)]
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _cloud(self, x: float, y: float, scale: float) -> None:
        parts = [(-48, 4, 70, 32), (-20, -20, 46, 42), (24, -10, 86, 38), (64, 0, 120, 30)]
        for x1, y1, x2, y2 in parts:
            self.create_oval(x + x1 * scale, y + y1 * scale, x + x2 * scale, y + y2 * scale, fill=CLOUD, outline=CLOUD)

    def _sun(self, x: float, y: float) -> None:
        self.create_oval(x - 24, y - 24, x + 24, y + 24, fill=SUN, outline=SUN)
        self.create_oval(x - 42, y - 42, x + 42, y + 42, outline="#ffe9a9", width=2)

    def _breeze(self, width: int) -> None:
        lines = [(width * 0.46, 32, 82), (width * 0.52, 48, 112), (width * 0.40, 92, 96)]
        for x, y, span in lines:
            self.create_line(x, y, x + span, y - 4, fill="#d6f1ff", width=2, smooth=True)

    def _butterfly(self, x: float, y: float, scale: float) -> None:
        wing = "#fff6cf"
        self.create_oval(x - 14 * scale, y - 9 * scale, x, y + 7 * scale, fill=wing, outline=wing)
        self.create_oval(x, y - 9 * scale, x + 14 * scale, y + 7 * scale, fill=wing, outline=wing)
        self.create_line(x, y - 8 * scale, x, y + 9 * scale, fill="#c99948", width=1)
