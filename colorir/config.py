"""Configuration options.

Examples:
    Create a new color format and make it default:

    >>> from colorir import config, ColorFormat
    >>> config.DEFAULT_COLOR_FORMAT = ColorFormat(Hex, uppercase=True)

    Change the default locations from which palettes are loaded and to which they are saved:

    >>> config.DEFAULT_PALETTES_DIR = ".../my_project/palettes"
"""
from os import path

from .color_format import ColorFormat
from .color_class import Hex

DEFAULT_PALETTES_DIR = path.join(path.dirname(__file__), "palettes")
"""Default directory from which palettes will be loaded and to which they will be saved."""

DEFAULT_COLOR_FORMAT = ColorFormat(Hex)
"""Default color format used by different objects in this package."""

REPR_STYLE = "swatch"
"""How colorir will represent objects in the terminal.

Valid values are 'swatch' - to print swatches of the objects; 'inherit' - to inherit repr 
behaviour from parent class (so tuples or strings); and 'traditional' - to represent objects with text as is common in
python.

Be aware that not all class support all styles of representation. If an object does not support a
particular style, it will fall back to its 'traditional' style.
"""