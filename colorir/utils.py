import os
from math import sqrt
from random import randint
from typing import Union, List

from . import config
from . import palette
from .color_class import ColorBase
from .color_format import ColorLike, ColorFormat
from .gradient import Grad


def swatch(obj: Union[ColorLike, List[ColorLike], "palette.Palette", "palette.StackPalette"],
           colored_text=True,
           width=3,
           height=1,
           tabular=True):
    """Prints swatches of `obj` in the terminal with colored text.

    Each swatch consists of a rectangle of a color followed by its value (and name if known).

    Args:
        obj: What will be represented in the terminal. Is either a single color, a list of colors,
            a :class:`~colorir.palette.Palette`, a :class:`~colorir.palette.StackPalette` or a
            subclass of :class:`~colorir.gradient.Grad`.
        colored_text: Whether the text that follows the colored rectangles should also be colored.
        width: The width (in space characters) of the colored rectangles.
        height: The height (in number of lines) of the colored rectangles.
        tabular: Whether the colored rectangle, color name and color value should be printed each
            in its separate column. Only used if `obj` is a :class:`~colorir.palette.Palette`.
    """
    # Assume single ColorLike
    if isinstance(obj, (ColorBase, str, tuple)):
        obj = [obj]
    elif isinstance(obj, Grad):
        pass
    elif isinstance(obj, palette.Palette):
        longest_name = max([len(name) for name in obj.color_names])
    # Needed to make Windows understand "\33" (https://stackoverflow.com/questions/12492810/python-
    # how-can-i-make-the-ansi-escape-codes-to-work-also-in-windows)
    os.system("")
    for i, c_val in enumerate(obj):
        rect_str = color_str(" " * width, bg_color=c_val)
        val_str = f" {c_val}"
        if isinstance(obj, palette.Palette):
            name = obj.color_names[i]
            spacing = tabular * " " * (longest_name - len(name))
            val_str = ' ' + name + spacing + val_str
        if colored_text:
            val_str = color_str(val_str, fg_color=c_val)
        print(rect_str + val_str)
        for _ in range(height - 1):
            print(rect_str)


def simplified_dist(color1: ColorLike,
                    color2: ColorLike):
    """Calculates the perceived distance between two colors.

    There are many methods to approach the similarity of colors mathematically. The
    algorithm implemented in this function [#]_ tries to provide balance between efficiency and
    accuracy by using a weighted euclidian distance formula in the RGB color space.

    References:
        .. [#] Adapted from "Colour metric" by Thiadmer Riemersma. Available on
            https://www.compuphase.com/cmetric.htm.

    Args:
        color1: First color point.
        color2: Second color point.
    """
    color_format = config.DEFAULT_COLOR_FORMAT
    # We only need the '._rgba's, so no need to convert if already ColorBase
    if not isinstance(color1, ColorBase):
        color1 = color_format.format(color1)
    if not isinstance(color2, ColorBase):
        color2 = color_format.format(color2)
    rgba1, rgba2 = color1._rgba, color2._rgba
    avg_r = (rgba1[0] + rgba2[0]) / (2 * 255)
    d_r = rgba1[0] - rgba2[0]
    d_g = rgba1[1] - rgba2[1]
    d_b = rgba1[2] - rgba2[2]
    return sqrt((2 + avg_r) * d_r ** 2
                 + 4 * d_g ** 2
                 + (3 - avg_r) * d_b ** 2)


# TODO one unified function of colormath funcs and simplified
# def dist(, method="CIE94"):


# TODO
# def to_grayscale


def random_color(random_a=False,
                 color_format: ColorFormat = None):
    """Generates a new random color.

    Args:
        random_a: Whether to randomize the alpha attribute as well or just make it 1.
        color_format: Specifies the format of the output color. Defaults to
            :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.

    Examples:
        >>> random_color()  # doctest: +SKIP
        Hex('#304fcc')
    """
    if color_format is None:
        color_format = config.DEFAULT_COLOR_FORMAT
    if random_a:
        a = randint(0, 255)
    else:
        a = 255
    # randint divided by 255 has to be used to avoid floating point errors when rounding a random
    # float
    return color_format._from_rgba((randint(0, 255),
                                    randint(0, 255),
                                    randint(0, 255),
                                    a))


def color_str(string: str,
              fg_color: ColorLike = None,
              bg_color: ColorLike = None) -> str:
    """Returns an ANSI-escaped [#]_ colored representation of `string`.

    Examples:
        >>> print(color_str("It's Christmas!", "#ff0000", "#00ff00"))  # doctest: +SKIP

    Args:
        string: String that will be colored.
        fg_color: Color to be applied to the foreground of the text.
        bg_color: Color to be applied to the background of the text.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/ANSI_escape_code#Colors.
    """
    if fg_color is not None:
        rgba = config.DEFAULT_COLOR_FORMAT.format(fg_color)._rgba
        string = f"\033[38;2;{rgba[0]};{rgba[1]};{rgba[2]}m" + string + "\33[0m"
    if bg_color is not None:
        rgba = config.DEFAULT_COLOR_FORMAT.format(bg_color)._rgba
        string = f"\033[48;2;{rgba[0]};{rgba[1]};{rgba[2]}m" + string + "\33[0m"
    return string


# TODO implement in a better way
# https://entropymine.com/imageworsener/srgbformula/
def _to_linear_rgb(rgba):
    rgba = list(rgba)
    for i in range(3):
        if rgba[i] <= 255 * 0.04045:
            rgba[i] /= 12.92
        else:
            rgba[i] = 255 * pow(((rgba[i] / 255 + 0.055) / 1.055), 2.4)
    return tuple(rgba)


def _to_srgb(rgba):
    rgba = list(rgba)
    for i in range(3):
        if rgba[i] <= 255 * 0.0031308:
            rgba[i] *= 12.92
        else:
            rgba[i] = 255 * (1.055 * pow(rgba[i] / 255, 1/2.4) - 0.055)
    return tuple(rgba)