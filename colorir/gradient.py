"""Gradients between colors.

For now only an RGB gradient is available.

Examples:
    Get purple inbetween red and blue:

    >>> grad = Grad(["ff0000", "0000ff", "ffffff"])
    >>> grad.perc(0.25)
    HexRGB('#be0090')

    Get 3 colors interspaced in the gradient:

    >>> grad.n_colors(3)
    [HexRGB('#be0090'), HexRGB('#0000ff'), HexRGB('#9999e8')]
"""
from typing import Iterable, Type
from . import config
from .color import sRGB, CIELUV, _to_srgb, _to_linear_rgb, ColorBase
from .color_format import ColorLike


class Grad:
    """Linear interpolation gradient.

    Args:
        colors: Iterable of colors that compose the gradient. There can be more than two colors in
            this iterable.
        color_format: Color format specifying how to output colors. Defaults to
            :const:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        color_sys: Color system in which the colors will be interpolated.
    """

    def __init__(self,
                 colors: Iterable[ColorLike],
                 color_format=None,
                 color_sys: Type[ColorBase] = CIELUV):
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self.color_format = color_format
        self.color_sys = color_sys
        self.colors = tuple(self.color_format.format(color) for color in colors)
        self._conv_colors = tuple(color_sys._from_rgba(color._rgba, include_a=True)
                                  for color in self.colors)

    def perc(self, p: float):
        """Returns the color placed in a given percentage of the gradient.

        Args:
            p: Percentage of the gradient expressed in a range of 0-1 from which a color will be
                drawn.

        Examples:
            Get purple inbetween red and blue:

            >>> grad = Grad([sRGB(255, 0, 0), sRGB(0, 0, 255)])
            >>> grad.perc(0.5)
            HexRGB('#be0090')

            Get a very "reddish" purple:

            >>> grad.perc(0.2)
            HexRGB('#e6005c')
        """
        i = int(p * (len(self._conv_colors) - 1))
        new_color = self._linear_interp(
            self._conv_colors[i],
            self._conv_colors[min([i + 1, len(self._conv_colors) - 1])],
            p * (len(self._conv_colors) - 1) - i
        )
        return self.color_format._from_rgba(new_color._rgba)

    def n_colors(self, n: int, include_ends=False):
        """Return `n` interspaced colors from the gradient.

        Args:
            n: Number of colors to retrieve.
            include_ends: By default, color values returned by this method will never include the
                very extremes of the gradient. This allows sampling a small number of colors (such
                as two) without having it return the same colors that were used to create the
                gradient in the first place.
        """
        colors = []
        sub = -1 if include_ends else 1
        for i in range(n):
            p = (i + (not include_ends)) / (n + sub)
            colors.append(self.perc(p))
        return colors

    # TODO
    # def to_cmap(self):

    def _linear_interp(self, color1, color2, p: float):
        return self.color_sys(
            *(color1[i] + (color2[i] - color1[i]) * p for i in range(len(color1)))
        )


class RGBGrad(Grad):
    """Linear interpolation gradient using the RGB color space.

    This class allows colors to be interpolated using linear RGB through the 'use_linear_rgb'
    parameter. Otherwise, ``RGBGrad(..., use_linear_rgb=False)`` is the same as
    ``Grad(..., color_sys=sRGB)``.

    Args:
        colors: Iterable of colors that compose the gradient. There can be more than two colors in
            this iterable.
        color_format: Color format specifying how to output colors. Defaults to
            :const:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        use_linear_rgb: Whether to use linear RGB rather than sRGB to create the gradient.

    Notes:
        Often using linear RGB may result in a gradient that looks more natural to the human eye
        [#]_

    References:
        .. [#] Ayke van Laethem at https://aykevl.nl/2019/12/colors
    """

    def __init__(self, colors: Iterable[ColorLike], color_format=None, use_linear_rgb=False):
        super().__init__(colors=colors, color_format=color_format, color_sys=sRGB)
        self.use_linear_rgb = use_linear_rgb

    def _linear_interp(self, color1, color2, p: float):
        if self.use_linear_rgb:
            rgba_1 = _to_linear_rgb(color1._rgba)
            rgba_2 = _to_linear_rgb(color2._rgba)
        else:
            rgba_1 = color1._rgba
            rgba_2 = color2._rgba

        new_rgba = tuple(rgba_1[i] + (rgba_2[i] - rgba_1[i]) * p for i in range(4))
        if self.use_linear_rgb:
            new_rgba = _to_srgb(new_rgba)
        return sRGB(*new_rgba)


# Alias
RGBLinearGrad = RGBGrad