from PIL import Image, ImageDraw
from colorir import *
import os

TRUNCATE_PALETTE = False
MAX_COLORS = 21
IMG_HEIGHT = 25

pal_pngs_dir = os.path.join(os.path.dirname(__file__), "_static/image/palettes")

pals = {name: StackPalette.load(name) for name in find_palettes(kind=StackPalette)}
pals.update({name: Palette.load(name).to_stackpalette() for name in find_palettes(kind=Palette)})
for pal_name, pal in pals.items():
    if not TRUNCATE_PALETTE:
        size = (min(len(pal), MAX_COLORS) * IMG_HEIGHT, (len(pal) // MAX_COLORS + 1) * IMG_HEIGHT)
        iterable = pal.colors
    else:
        size = (min(len(pal), MAX_COLORS + 1) * IMG_HEIGHT, IMG_HEIGHT)
        iterable = pal.colors[:MAX_COLORS]
    im = Image.new("RGBA", size=size)
    draw = ImageDraw.Draw(im)
    for i, color in enumerate(iterable):
        x = i % MAX_COLORS * IMG_HEIGHT
        y = i // MAX_COLORS * IMG_HEIGHT
        draw.rectangle((x, y, x + IMG_HEIGHT - 1, y + IMG_HEIGHT - 1),
                       fill=color,
                       width=0,
                       outline="#000000")
    if TRUNCATE_PALETTE and len(pal.colors) > MAX_COLORS:
        ellipsis_dir = os.path.join(os.path.dirname(__file__), "_static/image/ellipsis.png")
        ellipsis_png = Image.open(ellipsis_dir)
        ellipsis_png = ellipsis_png.resize((IMG_HEIGHT, IMG_HEIGHT))
        im.paste(ellipsis_png, (x + IMG_HEIGHT, 0))
    png_file = f"{pal_pngs_dir}/{pal_name}.png"
    im.save(png_file, "PNG")