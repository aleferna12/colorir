import tkinter as tk
from functools import partial
from colorir import Palette, find_palettes
from colorir.utils import hue_sort_key

colors = Palette.load(palettes_dir=".")
palettes = {"all": colors}
palettes.update({
    pal_name: Palette.load(pal_name, palettes_dir=".")
    for pal_name in find_palettes(palettes_dir=".", kind=Palette)
})


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry('1280x720')
        self.resizable(False, True)

        self.pal_btns = tk.Frame(self)
        self.pal_btns.pack(side=tk.LEFT, fill=tk.Y)
        for pal_name, palette in palettes.items():
            pal_name = pal_name.capitalize().replace('_', ' ') if pal_name.islower() else pal_name
            btn = tk.Button(self.pal_btns,
                            text=pal_name,
                            command=partial(self.add_color_btns, palette.color_names))
            btn.pack(fill='x')
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox('all')
        ))
        frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=frame, anchor='nw')

        self.btn_size = 45
        # Create a button for each available color
        self.color_btns = {name: FramedButton(
            frame,
            width=self.btn_size,
            height=self.btn_size,
            bg=colors.get_color(name),  # Background of the button is its color
            bd=1,
            command=partial(self.btn_command, name)
        ) for name in colors.color_names}
        self.update()
        self.add_color_btns(colors.color_names)

    def btn_command(self, name):
        # Adds a strip of the selected color to the left of the screen
        self.pal_btns.config(bg=colors.get_color(name))
        self.clipboard_clear()
        self.clipboard_append(name)

    def add_color_btns(self, c_names):
        for btn in self.color_btns.values():
            btn.grid_forget()
        row = 0
        col = 0
        for c_name in sorted(c_names, key=lambda name: hue_sort_key(8)(colors.get_color(name))):
            self.color_btns[c_name].grid(row=row, column=col)
            if (col + 2) * self.btn_size < self.canvas.winfo_width():
                col += 1
            else:
                col = 0
                row += 1
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))


class FramedButton(tk.Frame):
    def __init__(self, parent, width, height, *args, **kwargs):
        super().__init__(parent, width=width, height=height)
        self.pack_propagate(False)
        self.button = tk.Button(self, *args, **kwargs)
        self.button.pack(fill=tk.BOTH, expand=1)


win = Window()
win.mainloop()
