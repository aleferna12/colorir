"""Configuration options.

Examples:
    Create a new color format and make it default:

    >>> from colorir import config, ColorFormat
    >>> config.DEFAULT_COLOR_FORMAT = ColorFormat(HexRGB, uppercase=True)

    Change the default locations from which palettes are loaded and to which they are saved:

    >>> config.DEFAULT_PALETTES_DIR = ".../my_project/palettes"

Attributes:
    DEFAULT_PALETTES_DIR (str): Default directory from which palettes will be loaded and to which
        they will be saved.
    DEFAULT_COLOR_FORMAT (ColorFormat): Default color format used by different objects in this
        package.
"""
from os import path
from .color_format import ColorFormat
from .color import HexRGB

DEFAULT_PALETTES_DIR = path.join(path.dirname(path.dirname(__file__)), "palettes")
DEFAULT_COLOR_FORMAT = ColorFormat(HexRGB)