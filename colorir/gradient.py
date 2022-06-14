"""Gradients between colors.

For now only an RGB linear gradient is available.

Examples:
    Get purple inbetween red and blue:

    >>> grad = RGBLinearGrad([sRGB(255, 0, 0), sRGB(0, 0, 255), sRGB(255, 255, 255)])
    >>> grad.perc(0.25)
    HexRGB('#800080')

    Get 3 colors interspaced in the gradient:

    >>> grad.n_colors(3)
    [HexRGB('#800080'), HexRGB('#0000ff'), HexRGB('#8080ff')]
"""
from typing import Iterable
from . import config
from .color import sRGB, _to_sRGB, _to_linear_RGB
from .color_format import ColorLike


class RGBLinearGrad:
    """Poly-linear interpolation gradient using the RGB color space [1]_.

    Args:
        colors: Iterable of colors that compose the gradient. There can be more than two colors in
            this iterable.
        color_format: Color format specifying how to store and create colors. Defaults to
            :const:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        use_linear_RGB: Whether to use linear RGB rather than sRGB to create the gradient.

    Notes:
        Often using linear RGB may result in a gradient that looks more natural to the human eye
        [2]_

    References:
        .. [1] Wikipedia at https://en.wikipedia.org/wiki/SRGB.
        .. [2] Ayke van Laethem at https://aykevl.nl/2019/12/colors
    """

    def __init__(self, colors: Iterable[ColorLike], color_format=None, use_linear_RGB=False):
        colors = list(colors)
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT
        self.color_format = color_format
        self.colors = [self.color_format.format(color) for color in colors]
        self.use_linear_RGB = use_linear_RGB

    def perc(self, p: float) -> ColorLike:
        """Returns the color placed in a given percentage of the gradient.

        Args:
            p: Percentage of the gradient expressed in a range of 0-1 from which a color will be
                drawn.

        Examples:
            Get purple inbetween red and blue:

            >>> grad = RGBLinearGrad([sRGB(255, 0, 0), sRGB(0, 0, 255)])
            >>> grad.perc(0.5)
            HexRGB('#800080')

            Get a very "reddish" purple:

            >>> grad.perc(0.2)
            HexRGB('#cc0033')
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

    def _linear_interp(self, color_1: ColorLike, color_2: ColorLike, p: float):
        if self.use_linear_RGB:
            rgba_1 = _to_linear_RGB(color_1._rgba)
            rgba_2 = _to_linear_RGB(color_2._rgba)
        else:
            rgba_1 = color_1._rgba
            rgba_2 = color_2._rgba

        new_rgba = tuple(round(rgba_1[i] + (rgba_2[i] - rgba_1[i]) * p) for i in range(4))
        return new_rgba if not self.use_linear_RGB else _to_sRGB(new_rgba)


