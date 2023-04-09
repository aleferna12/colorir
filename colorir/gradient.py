"""Gradients between colors.

Examples:
    Get purple inbetween red and blue:

    >>> grad = Grad(["ff0000", "0000ff"])
    >>> grad(0.5)  # By default interpolates in CIELuv
    Hex('#be0090')

    Depending on your use-case, it may be useful to rather interpolate colors in a cilindrical
    color space, such as :class:`~colorir.color_class.HSV` or :class:`~colorir.color_class.HCLuv`.
    To do this, use :class:`PolarGrad`, which supports color lerping through polar coordinate
    color components:

    >>> p_grad = PolarGrad(["ff0000", "0000ff"])
    >>> p_grad(0.5)
    Hex('#f000cc')

    You can control how the hue is interpolated with the `hue_lerp` attribute:

    >>> p_grad.hue_lerp = "longest"  # Calculates the longest distance between the hue of red and blue
    >>> p_grad(0.5)  # Now we get green instead of purple
    Hex('#008800')

    Get 5 colors interspaced in the gradient:

    >>> grad.n_colors(5)
    [Hex('#ff0000'), Hex('#e00066'), Hex('#be0090'), Hex('#9400b9'), Hex('#0000ff')]

    You can use the 'domain' argument to change the range in which values are interpolated:

    >>> grad = Grad(["ff0000", "0000ff"], domain=[4, 8])
    >>> grad(6)
    Hex('#be0090')

    And the 'color_coords' argument to specify the position of the input colors in the gradient:

    >>> grad = Grad(["ff0000", "00ff00", "0000ff"], color_coords=[0, 0.75, 1])  # Green sits closer to blue than to red
    >>> grad(0.75)
    Hex('#00ff00')
"""

import numpy as np
from copy import copy, deepcopy
from typing import Iterable, Type, List
from . import config, utils
from .color_class import RGB, CIELuv, ColorBase, HCLuv, ColorPolarBase, Hex, ColorLike
from .color_format import MATPLOTLIB_COLOR_FORMAT

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
            Must have the same length as the `colors` argument.
        discrete: If ``True``, does not interpolate the colors and instead return the
            closest color to the input value (according to `color_coords`). Useful to plot
            categorical data.
    """

    def __init__(self,
                 colors: Iterable[ColorLike],
                 color_sys: Type[ColorBase] = CIELuv,
                 color_format=None,
                 color_coords: List[float] = None,
                 domain=(0, 1),
                 discrete=False):
        if color_sys == Hex:
            raise ValueError("only tuple-based color systems are supported")
        if domain[0] >= domain[1]:
            raise ValueError("'domain' must follow the format [lower_bound, upper_bound]")
        if color_coords is None:
            color_coords = np.linspace(domain[0], domain[1], len(colors))
        if len(color_coords) != len(colors):
            raise ValueError("'color_coords' must have same length as 'colors'")
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self.color_sys = color_sys
        self.color_format = color_format
        self.domain = list(domain)
        self.color_coords = np.array(color_coords)
        self.discrete = discrete
        self.colors = colors

    @property
    def colors(self):
        return list(self._colors)

    @colors.setter
    def colors(self, value):
        self._colors = [self.color_format.format(color) for color in value]
        self._update_conv_colors()

    @property
    def color_edges(self):
        edges = []
        for c1, c2 in zip(self.color_coords, self.color_coords[1:]):
            edges.append((c1 + c2) / 2)
        return edges

    def __str__(self):
        return f"{self.__class__.__name__}({self._colors})"

    def __repr__(self):
        if config.REPR_STYLE in ["traditional", "inherit"]:
            return str(self)
        return utils.swatch(self, file=None)

    def __call__(self, x, restrict_domain=False):
        return self.at(x, restrict_domain=restrict_domain)

    # noinspection PyDefaultArgument
    def __deepcopy__(self, memodict={}):
        obj = copy(self)
        obj._colors = list(obj._colors)
        obj._conv_colors = list(obj._conv_colors)
        obj.domain = list(obj.domain)
        obj.color_coords = np.array(obj.color_coords)
        return obj

    def __invert__(self):
        obj = deepcopy(self)
        obj.colors = [~color for color in obj._colors]
        return obj

    def grayscale(self):
        obj = deepcopy(self)
        obj.colors = [color.grayscale() for color in obj._colors]
        return obj

    def at(self, x, restrict_domain=False) -> ColorBase:
        if restrict_domain and (x < self.domain[0] or x > self.domain[1]):
            raise ValueError("'x' is out of the gradient domain")
        i = min(np.digitize(x, self.color_coords), len(self._colors) - 1)
        if i == 0:
            return self.color_format._from_rgba(self._conv_colors[0]._rgba)
        p = (x - self.color_coords[i - 1]) / (self.color_coords[i] - self.color_coords[i - 1])
        if p > 1:
            return self.color_format._from_rgba(self._conv_colors[-1]._rgba)
        if self.discrete:
            return self.color_format._from_rgba(self._conv_colors[i - 1 + round(p)]._rgba)
        new_color = self._linear_interp(
            self._conv_colors[i - 1],
            self._conv_colors[i],
            p
        )
        # Sometimes this reinterpretation makes colors seem to not be linearly-interpolated
        # HCLuv(287, 99, 31) -> RGB(131, 0, 185) -> HCLuv(286, 95, 35)
        # This is okay though
        return self.color_format._from_rgba(new_color._rgba)

    def perc(self, p: float, restrict_domain=False) -> ColorBase:
        """Returns the color placed in a given percentage of the gradient.

        Args:
            restrict_domain:
            p: Percentage of the gradient expressed in a range of 0-1 from which a color will be
                drawn.

        Examples:
            Get purple inbetween red and blue:

            >>> grad = Grad([RGB(1, 0, 0), RGB(0, 0, 1)])
            >>> grad.perc(0.5)
            Hex('#be0090')

            Get a very "reddish" purple:

            >>> grad.perc(0.2)
            Hex('#e6005c')
        """
        x = p * (self.domain[1] - self.domain[0]) + self.domain[0]
        return self.at(x, restrict_domain=restrict_domain)

    def n_colors(self, n: int, include_ends=True) -> List[ColorBase]:
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

    def to_cmap(self, name=None, n=256):
        """Converts this gradient into a matplotlib ListedColormap.

        Args:
            n: Number of discrete colors in the resulting color map.
            name: Passed down to color map constructor.
        """
        from matplotlib.colors import ListedColormap

        colors = [MATPLOTLIB_COLOR_FORMAT.format(color) for color in self.n_colors(n)]
        return ListedColormap(colors, N=n, name=name)

    def to_plotly_colorscale(self, n=256):
        """Make a color scale according to plotly's format definition.

        Args:
            n: Number of internal interpolations to perform before creating the color scale. Increases
                the accuracy of the color scale. This argument is not used if the gradient is discrete.
        """
        colorscale = []
        if not self.discrete:
            for p in np.linspace(0, 1, n):
                colorscale.append((p, self.perc(p).hex()))
            return colorscale
        scale_pos = [0] + self.color_edges + [1]
        for i, pos in enumerate(scale_pos[:-1]):
            color = self.colors[i].hex()
            colorscale.append((pos, color))
            colorscale.append((scale_pos[i + 1], color))
        return colorscale

    def _linear_interp(self, color1, color2, p: float) -> ColorBase:
        """Receives two colors in 'self.color_sys' format (expected to include_a) and returns a
        new color in the same format."""
        color1, color2 = np.array(color1), np.array(color2)
        return self.color_sys(
            *(color1 + (color2 - color1) * p)
        )

    def _update_conv_colors(self):
        self._conv_colors = []
        for color in self._colors:
            color = self.color_format.format(color)
            color = self.color_sys._from_rgba(color._rgba, include_a=True, round_to=-1)
            self._conv_colors.append(color)


class PolarGrad(Grad):
    """Similar to `Grad` but can calculate the shortest path for hue interpolation.

    Args:
        hue_lerp: Which method to apply to hue interpolation. Options are: ``None``, "increase",
            "decrease", "shortest" and "longest".
            ``None`` means that the hue will be treated as any other color component and interpolated normally.
            "increment" and "decrement" indicate that the hue can only be incremented or
            decremented respectively.
            "shortest" and "longest" make sure that the hue is interpolated in the shortest or longest
            paths between the colors. Default is "shortest".
        colors: Iterable of colors that compose the gradient.
        color_sys: Color system in which the colors will be interpolated.
    """
    def __init__(self,
                 colors,
                 color_sys=HCLuv,
                 hue_lerp="shortest",
                 **kwargs):
        if not issubclass(color_sys, ColorPolarBase):
            raise ValueError("'color_sys' must be a subclass of 'ColorPolarBase'")
        if hue_lerp not in [None, "increment", "decrement", "shortest", "longest"]:
            raise ValueError("'hue_lerp' must be None, 'increment', 'decrement', 'shortest' or 'longest'")

        super().__init__(colors=colors, color_sys=color_sys, **kwargs)
        self.hue_lerp = hue_lerp

    def _linear_interp(self, color1, color2, p: float) -> ColorBase:
        d = abs(color1.h - color2.h)
        if self.hue_lerp is None \
                or (self.hue_lerp == "shortest" and d <= color1.max_h / 2) \
                or (self.hue_lerp == "longest" and d > color1.max_h / 2):
            return super()._linear_interp(color1=color1, color2=color2, p=p)

        array1, array2 = np.array(color1), np.array(color2)
        if self.hue_lerp == "increment" or (self.hue_lerp != "decrement" and color1.h > color2.h):
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
            Defaults to ``True``.

    Notes:
        Often using linear RGB may result in a gradient that looks more natural to the human eye
        [#]_. THIS IS THE DEFAULT.

    References:
        .. [#] Ayke van Laethem at https://aykevl.nl/2019/12/colors
    """

    def __init__(self, colors: Iterable[ColorLike], use_linear_rgb=True, **kwargs):
        super().__init__(colors=colors, color_sys=RGB, **kwargs)
        self.use_linear_rgb = use_linear_rgb

    def _linear_interp(self, color1, color2, p: float) -> ColorBase:
        rgba_1 = color1._rgba
        rgba_2 = color2._rgba
        if self.use_linear_rgb:
            rgba_1 = utils._to_linear_rgb(rgba_1 / 255)
            rgba_2 = utils._to_linear_rgb(rgba_2 / 255)

        new_rgba = rgba_1 + (rgba_2 - rgba_1) * p
        if self.use_linear_rgb:
            new_rgba = utils._to_srgb(new_rgba) * 255
        return RGB._from_rgba(new_rgba)


# Alias
RGBLinearGrad = RGBGrad
