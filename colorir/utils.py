import os
import sys
import numpy as np
from math import sqrt
from random import randint
from typing import List, Iterable, get_args

from . import config
from . import palette
from .colormath.color_conversions import convert_color
from .colormath.color_diff import *
from .colormath.color_objects import sRGBColor, LabColor
from .color_class import ColorBase, HCLab, ColorLike
from .color_format import ColorFormat
from .gradient import Grad

# Patch asscalar
np.asscalar = lambda a: a.item()

__all__ = [
    "swatch",
    "show",
    "simplified_dist",
    "color_dist",
    "random_color",
    "color_str",
    "hue_sort_key",
    "hue_sorted",
    "grayscale",
    "inverse",
    "blend"
]


def blend(color1, color2, perc=0.5, grad_class=Grad, **kwargs):
    return grad_class([color1, color2], **kwargs).perc(perc)


def grayscale(obj):
    """Returns a grayscale representation of a colorir object"""
    if isinstance(obj, list):
        return [color.grayscale() for color in obj]
    # Assume single colorlike
    elif isinstance(obj, get_args(ColorLike)):
        obj = config.DEFAULT_COLOR_FORMAT.format(obj)
    return obj.grayscale()


def inverse(obj):
    """Returns an RGB-inverted representation of a colorir object"""
    if isinstance(obj, list):
        return [~color for color in obj]
    # Assume single colorlike
    elif isinstance(obj, get_args(ColorLike)):
        obj = config.DEFAULT_COLOR_FORMAT.format(obj)
    return ~obj


def swatch(obj,
           colored_text=True,
           width=3,
           height=1,
           tabular=True,
           file=sys.stdout):
    """Swatches a colorir object in the terminal.

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
        file: If ``None`` returns the swatch as a string. Otherwise, this argument must be a file object and
            is passed to `print`.
    """
    longest_name = None
    if isinstance(obj, Grad):
        # Seven steps for each color transition = 7 * (n - 1) - (n - 2)
        obj = obj.n_colors(6 * len(obj.colors) - 5, include_ends=True)
    elif isinstance(obj, palette.Palette):
        longest_name = max([len(name) for name in obj.color_names])
    # Assume single ColorLike
    elif not isinstance(obj, (list, palette.StackPalette)):
        obj = [obj]
    # Needed to make Windows understand "\33" (https://stackoverflow.com/questions/12492810/python-
    # how-can-i-make-the-ansi-escape-codes-to-work-also-in-windows)
    os.system("")
    ret_str = ""
    for i, c_val in enumerate(obj):
        rect_str = color_str(" " * width, bg_color=c_val)
        val_str = f" {c_val}"
        if longest_name is not None:
            name = obj.color_names[i]
            spacing = tabular * " " * (longest_name - len(name))
            val_str = ' ' + name + spacing + val_str
        if colored_text:
            val_str = color_str(val_str, fg_color=c_val)
        ret_str += rect_str + val_str + '\n'
        for _ in range(height - 1):
            ret_str += rect_str + '\n'
    ret_str = ret_str.strip("\n")
    if file is None:
        return ret_str
    print(ret_str, file=file)


def show(obj,
         width=None,
         height=None,
         interactive=None,
         inline=True):
    """Shows a colorir object inlined on a Jupyter notebook or using tkinter.

    Args:
        inline: If running on a Jupyter notebook, whether to display the object inline.
            Requires Pillow to be installed.
        obj:
        width:
        height:
        interactive: Whether clicking of the screen will copy the color value
            to the clipboard and swatch the color on the terminal. Setting this
            parameter to ``False`` results is a dramatic speed-up. By default,
            is set to ``True`` for small objects (less than 100 colors) and
            ``False`` otherwise. Only has an effect if not running on a
            Jupyter notebook with `inline` == ``True``.
    """
    if inline:
        try:
            from IPython.display import display
            # For some reason this function is not in globals()... so we gotta try it
            if get_ipython().__class__.__name__ == "ZMQInteractiveShell":
                display(make_image(obj, width, height))
                return
        except (ImportError, NameError):
            pass
        show_tkinter(obj, width, height, interactive)


def show_tkinter(obj, width, height, interactive):
    import tkinter as tk
    from . import tkinter_utils as tku

    win = tk.Tk()
    win.resizable(False, False)

    max_width = win.winfo_screenwidth() * 0.8
    max_height = win.winfo_screenheight() * 0.8

    if isinstance(obj, Grad):
        if width is None:
            width = min(max_width, max(0.4 * max_width, 50 * len(obj.colors)))
        if height is None:
            height = 0.1 * max_height
        width, height = int(width), int(height)

        # Each button is two pixels wide to make the widget lighter
        colors = obj.n_colors(round(width / 2))
        color_names = None
    else:
        if isinstance(obj, palette.Palette):
            colors = obj.colors
            color_names = obj.color_names
        elif isinstance(obj, (palette.StackPalette, list)):
            colors = list(obj)
            color_names = None
        else:
            colors = [config.DEFAULT_COLOR_FORMAT.format(obj)]
            color_names = None

        if height is None:
            height = 0.1 * max_height
        if width is None:
            width = min(max_width, len(colors) * height)
        width, height = int(width), int(height)

    if interactive is None:
        interactive = True if len(colors) < 100 else False
    if interactive:
        wgt = tku.PaletteWidget(
            win,
            colors,
            color_names=color_names,
            width=width,
            height=height
        )
    else:
        wgt = tku.StaticPaletteWidget(
            win,
            colors,
            width=width,
            height=height
        )
    wgt.pack()
    win.mainloop()


def make_image(obj, width, height):
    from PIL import Image

    if height is None:
        height = 64
    if isinstance(obj, Grad):
        if width is None:
            width = 512
        colors = obj.n_colors(width)
    else:
        if not isinstance(obj, (palette.PaletteBase, list)):
            obj = [config.DEFAULT_COLOR_FORMAT.format(obj)]
        colors = list(obj)
        if width is None:
            width = height * len(colors)
    img = np.array([config.DEFAULT_COLOR_FORMAT.format(color)._rgba for color in colors], dtype="uint8")
    # Add height dim
    img = np.reshape(img, (1, img.shape[0], 4))
    img = img.repeat(height, axis=0).repeat(width // len(colors), axis=1)
    return Image.fromarray(img, "RGBA")


def hue_sort_key(hue_classes=None,
                 gray_thresh=12.0,
                 gray_start=True,
                 alt_lum=False,
                 invert_lum=False):
    """Returns a function that can be used as a key for python's 'sort' and 'sorted' in order to
    sort color-like objects by their hue component.

    Examples:
        >>> sorted(["0000ff", "ff0000",  "000000", "00ff00", "ffffff"], key=hue_sort_key())
        ['000000', 'ffffff', 'ff0000', '00ff00', '0000ff']

    Args:
        hue_classes: Number hue categories. Inside each hue category colors will be sorted by
            luminance rather than hue. When ``None``, colors are sorted only according to
            their hue.
        gray_thresh: Chroma threshold bellow which a color will be considered a shade of gray.
        gray_start: Whether the colors considered shades of gray will be grouped at the start or
            end of the sorted iterable.
        alt_lum: Whether to alternate luminance values with each hue class transition. Only has an
            effect if `hue_classes` > 1.
        invert_lum: By default, sorting within hue classes happen from darker to lighter colors.
            This parameter allows inverting this patern, thus starting with light colors and going
            towards darker tones. Only has an effect if `hue_classes` > 1.

    Notes:
        The refered hue and chroma components are those of :class:`~colorir.color_class.HCLab`.
    """
    color_format = config.DEFAULT_COLOR_FORMAT
    gray_hue = -1 if gray_start else hue_classes + 1

    def sort_key(color):
        interpreted = color_format.format(color)
        h, c, l = HCLab._from_rgba(interpreted._rgba, max_h=1)
        if c < gray_thresh:
            h = gray_hue
            if not gray_start and alt_lum and hue_classes % 2 == 1:
                l *= -1
        elif hue_classes is not None:
            h = int(h * hue_classes)
            if alt_lum and h % 2 == (not gray_start):
                l *= -1

        if hue_classes is None:
            return h
        if invert_lum:
            l *= -1
        return h, l

    return sort_key


def hue_sorted(colors: Iterable[ColorLike], **kwargs) -> List[ColorLike]:
    """Sort colors by their hue values. See :func:`~colorir.utils.hue_sort_key` for the arguments docs.

    Returns:
        A list of sorted colors.
    """
    key = hue_sort_key(**kwargs)
    return sorted(colors, key=key)


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


# TODO doc (mention 2000 not working properly in colormath and kwargs for delta-e funcs)
def color_dist(color1: ColorLike, color2: ColorLike, method="CIE76"):
    if method == "simplified":
        return simplified_dist(color1, color2)

    color_format = config.DEFAULT_COLOR_FORMAT
    if not isinstance(color1, ColorBase):
        color1 = color_format.format(color1)
    if not isinstance(color2, ColorBase):
        color2 = color_format.format(color2)
    color1 = sRGBColor(*color1._rgba[:3], is_upscaled=True)
    color2 = sRGBColor(*color2._rgba[:3], is_upscaled=True)
    color1 = convert_color(color1, LabColor, target_illuminant="d65")
    color2 = convert_color(color2, LabColor, target_illuminant="d65")

    if method == "CIE76":
        return delta_e_cie1976(color1, color2)
    if method == "CIE94":
        return delta_e_cie1994(color1, color2)
    if method == "CIE2000":
        return delta_e_cie2000(color1, color2)
    if method == "CMC":
        return delta_e_cmc(color1, color2)

    raise ValueError("invalid 'method' parameter")


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


# https://entropymine.com/imageworsener/srgbformula/
def _to_linear_rgb(rgba):
    """rgba must be in range 0-1"""
    srgb = np.array(rgba[:-1])
    lrgb = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return np.pad(lrgb, [(0, 1)], constant_values=rgba[-1])


def _to_srgb(rgba):
    """rgba must be in range 0-1"""
    lrgb = np.array(rgba[:-1])
    srgb = np.where(lrgb <= 0.0031308, lrgb * 12.92, 1.055 * lrgb ** (1 / 2.4) - 0.055)
    return np.pad(srgb, [(0, 1)], constant_values=rgba[-1])