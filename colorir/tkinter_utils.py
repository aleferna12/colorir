import tkinter as tk

import numpy as np

from . import config
from .utils import color_str


class StaticPaletteWidget(tk.Canvas):
    def __init__(self, master, colors, width, height):
        super().__init__(master, width=width, height=height)

        rect_w = width / len(colors)
        for i, color in enumerate(colors):
            x = i * rect_w
            color = config.DEFAULT_COLOR_FORMAT.format(color).hex()
            self.create_rectangle(
                x, 0, x + rect_w, height,
                fill=color,
                outline=color
            )


class ColorFrame(tk.Frame):
    def __init__(self, master, root, color, color_name, width, height):
        super().__init__(master, width=width, height=height)

        self.root = root
        self.color = config.DEFAULT_COLOR_FORMAT.format(color)
        self.color_name = color_name
        self.btn = tk.Button(self,
                             command=self.on_click,
                             bg=self.color.hex(),
                             activebackground=self.color.hex(),
                             bd=0,
                             highlightthickness=0)
        self.btn.pack(fill=tk.BOTH, expand=1)
        self.pack_propagate(0)

    def on_click(self):
        c_str = color_str(str(self.color), self.color)
        if self.color_name:
            c_str = self.color_name + " " + c_str
        c_str = f"{color_str('   ', bg_color=self.color)} {color_str(c_str, self.color)}"
        print(c_str)
        # Transmit clipboard command to PaletteWidget
        self.send_clipboard(str(self.color))

    def send_clipboard(self, string):
        self.root.clipboard_clear()
        self.root.clipboard_append(string)
        # Prevents from erasing clipboard after thread is closed
        self.root.update()


class PaletteWidget(tk.Frame):
    def __init__(self, master, colors, width, height, color_names=None):
        super().__init__(master, width=width, height=height)

        root = self.get_root()
        if color_names is None:
            color_names = [""] * len(colors)
        if len(colors) > width:
            indexes = np.linspace(0, len(colors) - 1, width).round().astype(int)
            colors = [colors[i] for i in indexes]

        btn_w = int(width / len(colors))
        for color, color_name in zip(colors, color_names):
            btn = ColorFrame(self, root, color, color_name, btn_w, height)
            btn.pack(side="left")

    def get_root(self):
        wgt = self
        while wgt.master is not None:
            wgt = wgt.master
        return wgt

