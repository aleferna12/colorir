"""Gradients between colors.

For now only an RGB linear gradient is available.

Examples:
    Get purple inbetween red and blue:

    >>> grad = RGBLinearGrad([sRGB(255, 0, 0), sRGB(0, 0, 255), sRGB(255, 255, 255)])
    >>> grad.perc(0.25)
    sRGB(127.5, 0.0, 127.5)

    Get 2 colors interspaced in the gradient:

    >>> grad.n_colors(3)
    [sRGB(127.5, 0.0, 127.5), sRGB(0.0, 0.0, 255.0), sRGB(127.5, 127.5, 255.0)]
"""
from typing import Iterable
from math import pow
from . import config
from .color import ColorBase, sRGB


class RGBLinearGrad:
    """Poly-linear interpolation gradient using the RGB color space [1]_.

    Args:
        colors: List of colors that compose the gradient There can be more than two colors in this
            list.
        color_format: Color format specifying how to store and create colors.
        use_linear_RGB: Whether to use linear RGB rather than sRGB to create the gradient.

    Notes:
        Often using linear RGB may result in a gradient that looks more natural to the human eye
        [2]_

    References:
        .. [1] Wikipedia at https://en.wikipedia.org/wiki/SRGB.
        .. [2] Ayke van Laethem at https://aykevl.nl/2019/12/colors
    """

    def __init__(self, colors: Iterable[ColorBase], color_format=None, use_linear_RGB=False):
        colors = list(colors)
        if color_format is None:
            if colors and isinstance(colors[0], ColorBase):
                color_format = colors[0].get_format()
            else:
                color_format = config.DEFAULT_COLOR_FORMAT
        self.color_format = color_format
        self.colors = [self.color_format.format(color) for color in colors]
        self.use_linear_RGB = use_linear_RGB

    def perc(self, p: float) -> ColorBase:
        """Returns the color placed in a given percentage of the gradient.

        Args:
            p: Percentage of the gradient expressed in a range of 0-1 from which a color will be
                drawn.

        Examples:
            Get purple inbetween red and blue:

            >>> grad = RGBLinearGrad([sRGB(255, 0, 0), sRGB(0, 0, 255)])
            >>> grad.perc(0.5)
            sRGB(127.5, 0.0, 127.5)

            Get a very "reddish" purple:

            >>> grad.perc(0.2)
            sRGB(204.0, 0.0, 51.0)
        """

        i = int(p * (len(self.colors) - 1))
        new_rgba = self._linear_interp(
            self.colors[i],
            self.colors[min([i + 1, len(self.colors) - 1])],
            p * (len(self.colors) - 1) - i
        )
        return self.color_format._from_rgba(new_rgba)

    def n_colors(self, n: int, no_ends=True):
        """Return `n` interspaced colors from the gradient.

        Args:
            n: Number of colors to retrieve.
            no_ends: By default, color values returned by this method will never include the very
                extremes of the gradient. This allows sampling a small number of colors (such as
                two) without having it return the same colors that were used to create the
                gradient in the first place.
        """
        colors = []
        sub = 1 if no_ends else -1
        for i in range(n):
            p = (i + no_ends) / (n + sub)
            colors.append(self.perc(p))
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


