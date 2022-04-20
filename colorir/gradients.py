"""Classes to create gradients between colors.

For now only the RGB linear gradient is available.
"""
from typing import Iterable
from math import pow
import config
from color import ColorBase


class RGBLinearGrad:
    """Poly-linear interpolation gradient using the `RGB color space`_.

    Although `RGB color space`_ is used for interpolation, any :mod:`color classes <color>`
    can be used as inputs.

    Args:
        colors: List of colors that compose the gradient.
        color_format: Color format of the
        use_linear_RGB: Whether to use `linear RGB`_ rather than sRGB to create the gradient.

    .. _linear RGB: https://aykevl.nl/2019/12/colors
    """

    def __init__(self, colors: Iterable[ColorBase], color_format=None, use_linear_RGB=False):
        self.colors = list(colors)
        if color_format is None:
            if self.colors and isinstance(self.colors[0], ColorBase):
                color_format = self.colors[0].get_format()
            else:
                color_format = config.DEFAULT_COLOR_FORMAT
        self.color_format = color_format
        self.use_linear_RGB = use_linear_RGB

    def perc(self, p: float) -> ColorBase:
        """Returns the color placed in a given percentage of the gradient.

        Args:
            p: Percentage of the gradient expressed in a range of 0-1 from which a color will be
                drawn.

        Examples:
            >>> cdict = ColorDict()
            >>> grad = RGBLinearGrad([cdict.red, cdict.blue])
            >>> grad.perc(0.5) # Get purple inbetween red and blue
            sRGB(127.5, 0.0, 127.5)
            >>> grad.perc(0.2) # Get very "reddish" purple
        """

        i = int(p * (len(self.colors) - 1))
        new_rgba = self._linear_interp(
            self.colors[i],
            self.colors[min([i + 1, len(self.colors) - 1])],
            p * (len(self.colors) - 1) - i
        )
        return self.color_format._from_rgba(new_rgba)

    def n_colors(self, n: int, stripped=True):
        colors = []
        sub = 1 if stripped else -1
        for i in range(n):
            p = (i + stripped) / (n + sub)
            colors.append(self.color_format._from_rgba(self.perc(p)))
        return colors

    def _linear_interp(self, color_1: ColorBase, color_2: ColorBase, p: float):
        if self.use_linear_RGB:
            rgba_1 = self._to_linear_RGB(color_1._rgba)
            rgba_2 = self._to_linear_RGB(color_2._rgba)
        else:
            rgba_1 = color_1._rgba
            rgba_2 = color_2._rgba

        new_rgba = [rgba_1[i] + (rgba_2[i] - rgba_1[i]) * p for i in range(4)]
        return new_rgba if not self.use_linear_RGB else self._to_sRGB(new_rgba)

    # https://entropymine.com/imageworsener/srgbformula/
    @staticmethod
    def _to_linear_RGB(rgba):
        rgba = list(rgba)
        for i in range(3):
            if rgba[i] <= 0.04045:
                rgba[i] /= 12.92
            else:
                rgba[i] = pow(((rgba[i] + 0.055) / 1.055), 2.4)
        return rgba

    @staticmethod
    def _to_sRGB(rgba):
        rgba = list(rgba)
        for i in range(3):
            if rgba[i] <= 0.0031308:
                rgba[i] *= 12.92
            else:
                rgba[i] = 1.055 * pow(rgba[i], 1/2.4) - 0.055
        return rgba


