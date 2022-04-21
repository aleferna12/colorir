"""Configuration options.

Examples:
    Create a new color format and make it default:

    >>> from colorir import config, ColorFormat
    >>> config.DEFAULT_COLOR_FORMAT = ColorFormat(sRGB, max_rgba=1)

    Change the default locations from which palettes are loaded and to which they are saved:

    >>> config.DEFAULT_PALETTES_DIR = ".../my_project/palettes"

Attributes:
    DEFAULT_PALETTES_DIR (str): Default directory from which palettes will be loaded and to which
        they will be saved (respectively by the :meth:`Palette.load()` and :meth:`Palette.save()`
        methods).
    DEFAULT_COLOR_FORMAT (ColorFormat): Default color format used when initializing or loading
        :class:`Palette` objects.
"""
from os import path
from .color_format import ColorFormat
from .color import sRGB

DEFAULT_PALETTES_DIR = path.join(path.dirname(__file__), "palettes")
DEFAULT_COLOR_FORMAT = ColorFormat(sRGB, round_to=0)