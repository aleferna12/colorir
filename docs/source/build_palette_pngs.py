try:
    from PIL import Image, ImageDraw
except ImportError:
    raise ImportError("PIL/Pillow is required to build the palettes png files")
from colorir import Palette, find_palettes
import os
from glob import glob

MAX_COLORS = 15
IMG_HEIGHT = 25

pal_pngs_dir = os.path.join(os.path.dirname(__file__), "images/palettes")
for file in glob(pal_pngs_dir + "/*.palette"):
    os.remove(file)

pal_files = find_palettes()
for pal_name in pal_files:
    pal = Palette.load(pal_name)
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
    draw.line((0, 0, x + IMG_HEIGHT - 1, 0), fill="#000000")
    draw.line((0, 0, 0, IMG_HEIGHT - 1), fill="#000000")
    draw.line((0, IMG_HEIGHT - 1, x + IMG_HEIGHT - 1, IMG_HEIGHT - 1), fill="#000000")
    draw.line((x + IMG_HEIGHT - 1, 0, x + IMG_HEIGHT - 1, IMG_HEIGHT - 1),
              fill="#000000")
    png_file = f"{pal_pngs_dir}/{pal_name}.png"
    im.save(png_file, "PNG")