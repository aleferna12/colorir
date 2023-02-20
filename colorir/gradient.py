"""Gradients between colors.

Examples:
    Get purple inbetween red and blue:

    >>> grad = Grad(["ff0000", "0000ff"])
    >>> grad.perc(0.5)
    Hex('#be0090')

    Depending on your use-case, it may be useful to rather interpolate colors in a cilindrical
    color space, such as :class:`~colorir.color_class.HSV` or :class:`~colorir.color_class.HCLuv`.
    To do this, use :class:`PolarGrad`, which supports color lerping through polar coordinate
    color components:

    >>> p_grad = PolarGrad(["ff0000", "0000ff"])
    >>> p_grad.perc(0.5)
    Hex('#f000cc')

    Get 5 colors interspaced in the gradient:

    >>> grad.n_colors(5)
    [Hex('#ff0000'), Hex('#e00066'), Hex('#be0090'), Hex('#9400b9'), Hex('#0000ff')]
"""
import numpy as np
from typing import Iterable, Type

from . import config, utils
from .color_class import sRGB, CIELuv, ColorBase, HCLuv, ColorPolarBase, Hex
from .color_format import ColorLike

__all__ = [
    "Grad",
    "PolarGrad",
    "RGBGrad",
    "RGBLinearGrad"
]


class Grad:
    """Linear interpolation gradient.

    Args:
        colors: Iterable of colors that compose the gradient.
        color_format: Color format specifying how to output colors. Defaults to
            :const:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        color_sys: Color system in which the colors will be interpolated.
        domain: Range (inclusive on both ends) from which colors can be interpolated.
        color_coords: A list of the coordinates where each color in 'colors' is located in the gradient.
            If left empty, interspaced points will be automatically generated. For example,
            the default for a list of three colors with domain == [0, 1] is [0, 0.5, 1].
            Must start/end in the values specified as boundaries in `domain`.
            Also must have the same length as the `colors` argument.
    """

    def __init__(self,
                 colors: Iterable[ColorLike],
                 color_sys: Type[ColorBase] = CIELuv,
                 color_format=None,
                 color_coords: list[float] = None,
                 domain=(0, 1)):
        if color_sys == Hex:
            raise ValueError("only tuple-based color systems are supported")
        if domain[0] >= domain[1]:
            raise ValueError("'domain' must follow the format [lower_bound, upper_bound]")
        if len(color_coords) != len(colors):
            raise ValueError("'color_coords' must have same length as 'colors'")
        if sorted([color_coords[0], color_coords[-1]]) != list(domain):
            raise ValueError("the boundaries of 'domain' must be present in 'color_coords' as the first and "
                             "last values")

        if color_coords is None:
            color_coords = np.linspace(domain[0], domain[1], len(colors))
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self.color_format = color_format
        self.color_sys = color_sys
        self.colors = [self.color_format.format(color) for color in colors]
        self._conv_colors = [self.color_sys._from_rgba(color._rgba,
                                                       include_a=True,
                                                       round_to=-1) for color in self.colors]
        self.domain = list(domain)
        self.color_coords = np.array(color_coords)

    def __str__(self):
        return f"{self.__class__.__name__}({self.colors})"

    def __repr__(self):
        if config.REPR_STYLE in ["traditional", "inherit"]:
            return str(self)
        return utils.swatch(self, file=None)

    def __call__(self, x, restrict_domain=False):
        return self.at(x, restrict_domain=restrict_domain)

    def at(self, x, restrict_domain=False):
        if restrict_domain and (x < self.domain[0] or x > self.domain[1]):
            raise ValueError("'x' is out of the gradient domain")
        i = min(np.digitize(x, self.color_coords), len(self.colors) - 1)
        new_color = self._linear_interp(
            self._conv_colors[i - 1],
            self._conv_colors[i],
            (x - self.color_coords[i - 1]) / (self.color_coords[i] - self.color_coords[i - 1])
        )
        # Sometimes this reinterpretation makes colors seem to not be linearly-interpolated
        # HCLuv(287, 99, 31) -> sRGB(131, 0, 185) -> HCLuv(286, 95, 35)
        # This is okay though
        return self.color_format._from_rgba(new_color._rgba)

    def perc(self, p: float, restrict_domain=False):
        """Returns the color placed in a given percentage of the gradient.

        Args:
            restrict_domain:
            p: Percentage of the gradient expressed in a range of 0-1 from which a color will be
                drawn.

        Examples:
            Get purple inbetween red and blue:

            >>> grad = Grad([sRGB(255, 0, 0), sRGB(0, 0, 255)])
            >>> grad.perc(0.5)
            Hex('#be0090')

            Get a very "reddish" purple:

            >>> grad.perc(0.2)
            Hex('#e6005c')
        """
        x = self.domain[0] + self.domain[1] * p
        return self.at(x, restrict_domain=restrict_domain)

    def n_colors(self, n: int, include_ends=True):
        """Return `n` interspaced colors from the gradient.

        Args:
            n: Number of colors to retrieve.
            include_ends: Stops the colors at the extreme of the gradient from being sampled.
                This allows sampling a small number of colors (such as two) without having it
                return the same colors that were used to create the gradient in the first place.
        """
        if n < 1:
            raise ValueError("'n' must be a positive integer")
        if n == 1:
            ps = [0.5]
        elif include_ends:
            ps = np.linspace(0, 1, n)
        else:
            ps = np.linspace(0, 1, n + 2)[1:-1]
        return [self.perc(p) for p in ps]

    def to_cmap(self, name, N=256, gamma=1.0):
        """Converts this gradient into a matplotlib LinearSegmentedColormap.

        Args:
            name: Passed down to LinearSegmentedColormap constructor.
            N: Passed down to LinearSegmentedColormap constructor.
            gamma: Passed down to LinearSegmentedColormap constructor.
        """
        from matplotlib.colors import LinearSegmentedColormap

        colors = [color.hex(include_a=True, tail_a=True) for color in self.n_colors(N)]
        return LinearSegmentedColormap.from_list(name=name, colors=colors, N=N, gamma=gamma)

    def _linear_interp(self, color1, color2, p: float):
        """Receives two colors in 'self.color_sys' format (expected to include_a) and returns a
        new color in the same format."""
        color1, color2 = np.array(color1), np.array(color2)
        return self.color_sys(
            *(color1 + (color2 - color1) * p)
        )


# TODO doc
class PolarGrad(Grad):
    """Similar to `Grad` but can calculate the shortest path for HUE interpolation.

    Args:
        shortest: Whether to use the shortest path to interpolate colors with a HUE component. If ``False``,
            acts like `Grad`.
        colors: Iterable of colors that compose the gradient.
        color_sys: Color system in which the colors will be interpolated.
    """
    def __init__(self,
                 colors,
                 color_sys=HCLuv,
                 shortest=True,
                 **kwargs):
        if not issubclass(color_sys, ColorPolarBase):
            raise ValueError("'color_sys' must be a subclass of 'ColorPolarBase'")

        super().__init__(colors=colors, color_sys=color_sys, **kwargs)
        self.shortest = shortest

    def _linear_interp(self, color1, color2, p: float):
        d = abs(color2.h - color1.h)
        if not self.shortest or d <= color1.max_h / 2:
            return super()._linear_interp(color1=color1, color2=color2, p=p)

        array1, array2 = np.array(color1), np.array(color2)
        if color1.h > color2.h:
            array1, array2 = array2, array1
            p = 1 - p
        array1[0] += color1.max_h
        new_color = array1 + (array2 - array1) * p
        new_color[0] %= color1.max_h

        return self.color_sys(*new_color)


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

    def __init__(self, colors: Iterable[ColorLike], use_linear_rgb=True, **kwargs):
        super().__init__(colors=colors, color_sys=sRGB, **kwargs)
        self.use_linear_rgb = use_linear_rgb

    def _linear_interp(self, color1, color2, p: float):
        if self.use_linear_rgb:
            rgba_1 = utils._to_linear_rgb(color1._rgba)
            rgba_2 = utils._to_linear_rgb(color2._rgba)
        else:
            rgba_1 = color1._rgba
            rgba_2 = color2._rgba

        new_rgba = tuple(rgba_1[i] + (rgba_2[i] - rgba_1[i]) * p for i in range(4))
        if self.use_linear_rgb:
            new_rgba = utils._to_srgb(new_rgba)
        return sRGB._from_rgba(new_rgba)


# Alias
RGBLinearGrad = RGBGrad
