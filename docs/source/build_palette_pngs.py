from PIL import Image, ImageDraw
from colorir import *
import os

MAX_COLORS = 15
IMG_HEIGHT = 25

pal_pngs_dir = os.path.join(os.path.dirname(__file__), "images/palettes")

pals = {name: StackPalette.load(name) for name in find_palettes(kind=StackPalette)}
pals.update({name: Palette.load(name).to_stackpalette() for name in find_palettes(kind=Palette)})
for pal_name, pal in pals.items():
    im = Image.new("RGBA", size=(min(len(pal), MAX_COLORS + 1) * IMG_HEIGHT, IMG_HEIGHT))
    draw = ImageDraw.Draw(im)
    for i, color in enumerate(pal.colors[:MAX_COLORS]):
        x = i * IMG_HEIGHT
        draw.rectangle((x, 0, x + IMG_HEIGHT - 1, IMG_HEIGHT - 1),
                       fill=color,
                       width=0,
                       outline="#000000")
    if len(pal.colors) > MAX_COLORS:
        ellipsis_dir = os.path.join(os.path.dirname(__file__), "images/ellipsis.png")
        ellipsis_png = Image.open(ellipsis_dir)
        ellipsis_png = ellipsis_png.resize((IMG_HEIGHT, IMG_HEIGHT))
        im.paste(ellipsis_png, (x + IMG_HEIGHT, 0))
    png_file = f"{pal_pngs_dir}/{pal_name}.png"
    im.save(png_file, "PNG")