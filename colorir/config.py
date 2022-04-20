from os import path
from color_format import ColorFormat
from color import sRGB

DEFAULT_PALETTES_DIR = path.join(path.dirname(__file__), "palettes")
DEFAULT_COLOR_FORMAT = ColorFormat(sRGB)