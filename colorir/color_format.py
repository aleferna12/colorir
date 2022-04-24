"""Color format specifications.

Often describing the color system is not enough when dealing with other libraries and frameworks.
For example, both Kivy [1]_ and PyGame [2]_ use mostly RGB colors as inputs when building
applications. However, Kivy expects the colors to have a maximum value of 1, while PyGame expects it
to be 255. To bridge these expectations and allow you to use the same colors in all of your
projects, one may use the :class:`ColorFormat` class.

Besides being able to specify your own color formats, a few pre-defined formats for popular
frameworks can be imported from this module, such as :const:`PYGAME_COLOR_FORMAT` and
:const:`WEB_COLOR_FORMAT`.

Examples:
    Import basic colors into a palette to work in a PyGame project:

    >>> from colorir import config, Palette, PYGAME_COLOR_FORMAT
    >>> config.DEFAULT_COLOR_FORMAT = PYGAME_COLOR_FORMAT
    >>> basic_colors = Palette.load("basic") # Loads colors as RGB values
    >>> # ... code

    Import the same colors but to work in a web project:

    >>> from colorir import config, Palette, WEB_COLOR_FORMAT
    >>> config.DEFAULT_COLOR_FORMAT = WEB_COLOR_FORMAT
    >>> basic_colors = Palette.load("basic") # Loads colors as hex codes
    >>> # ... code

    Create our own color format to work with HSL colors:

    >>> hsl_format = ColorFormat(HSL, max_h=100, max_sla=100, round_to=0)

    We can then pass the `hsl_format` to a palette or create colors directly with it:

    >>> hsl_format.new_color(30, 70, 70)
    HSL(30, 70, 70)

Attributes:
    WEB_COLOR_FORMAT (ColorFormat): Color format compatible with HTML and CSS standards.
    MATPLOTLIB_COLOR_FORMAT (ColorFormat): Color format compatible with Matplotlib.
    TKINTER_COLOR_FORMAT (ColorFormat): Color format compatible with Tkinter standards.
    PYGAME_COLOR_FORMAT (ColorFormat): Color format compatible with PyGame standards.
    KIVY_COLOR_FORMAT (ColorFormat): Color format compatible with Kivy standards.

References:
    .. [1] Kivy: Cross-platform Python Framework for NUI Development at https://kivy.org/.
    .. [2] PyGame library at https://www.pygame.org/.
"""
from typing import Type

from .color import sRGB, HexRGB, HSL, ColorBase, ColorLike


class ColorFormat:
    """Class to create color format specifications.

    Args:
        color_sys: The color system that is the basis of this color format.
        kwargs: Keyword arguments that further specify the color format. These are specific to each
        color system and can be consulted in their respective documentations.

    Examples:
        >>> c_format = ColorFormat(sRGB, max_rgba=1, include_a=True)
        >>> c_format.new_color(1, 0, 0)
        sRGB(1, 0, 0, 1)

        For more examples see the documentation of the :mod:`color_format` module.
    """
    def __init__(self, color_sys: Type["ColorBase"], **kwargs):
        self.color_sys = color_sys
        self._format_params = kwargs

    def __getattr__(self, item):
        # __getattr__ is called only when super().__getattribute__ fails
        try:
            return self._format_params[item]
        except LookupError as e:
            raise AttributeError(f"AttributeError: '{self.__class__.__name__}' object has no "
                                 f"attribute '{item}'") from e

    def __call__(self, *args, **kwargs):
        return self.new_color(*args, **kwargs)

    def __repr__(self):
        opener_str = f"{self.__class__.__name__}("
        arguments_str = f"color_sys={self.color_sys.__name__}"
        for param, param_v in self._format_params.items():
            arguments_str += f",\n{' ' * len(opener_str)}{param}={param_v.__repr__()}"
        return f"{opener_str}{arguments_str})"

    def new_color(self, *args, **kwargs) -> "ColorBase":
        """Creates a new color by filling the remaining parameters of a color constructor with the
        provided arguments.

        Examples:
            >>> c_format = ColorFormat(sRGB, max_rgba=1, include_a=True)
            >>> c_format.new_color(1, 0, 0)
            sRGB(1, 0, 0, 1)
        """
        kwargs.update(self._format_params)
        return self.color_sys(*args, **kwargs)

    def _from_rgba(self, rgba):
        # Factory method to be called when reading the palette files or reconstructing colors
        return self.color_sys._from_rgba(rgba, **self._format_params)

    def format(self, color: ColorLike) -> "ColorBase":
        """Tries to format a color-like object into this color format.

        Because there are multiple implementations of tuple-based color systems, the `color`
        parameter is always allowed to be a subclass of :class:`~colorir.color.ColorBase` or a hex
        string, but can only be a tuple if :attr:`ColorFormat.color_sys` is a tuple-based color
        system, such as :class:`~colorir.color.sRGB` for example.

        Examples:
            >>> rgb_format = ColorFormat(sRGB, round_to=0)
            >>> rgb_format.format("#ff0000")
            sRGB(255, 0, 0)
            >>> rgb_format.format((255, 0, 0))
            sRGB(255, 0, 0)
            >>> hex_format = ColorFormat(HexRGB)
            >>> hex_format.format("#ff0000")
            HexRGB(#ff0000)
            >>> hex_format.format((255, 0, 0)) # Can't know how to parse this tuple
            Traceback (most recent call last):
              ...
            ValueError: tried to interpret a tuple-formatted color object with a HexRGB ColorFormat

        Args:
            color: The value of the color to be formatted. Can be an instance of any
                :mod:`~colorir.color` class or, alternatively, a color-like object that
                resembles the format of the color you want to format.
        """
        if isinstance(color, ColorBase):
            return self._from_rgba(color._rgba)
        elif isinstance(color, str):
            # Try to preserve input options (none implemented now but who knows)
            if self.color_sys == HexRGB:
                return self.new_color(color)
            # Fallback to HexRGB default args
            return self._from_rgba(HexRGB(color)._rgba)
        if self.color_sys != HexRGB:
            # Assume that the color system is tuple-based
            return self.new_color(*color)
        else:
            raise ValueError("tried to interpret a tuple-formatted color object with a HexRGB "
                             "ColorFormat")


PYGAME_COLOR_FORMAT = ColorFormat(color_sys=sRGB, max_rgba=255, round_to=0)
KIVY_COLOR_FORMAT = ColorFormat(color_sys=sRGB, max_rgba=1, include_a=True)
WEB_COLOR_FORMAT = TKINTER_COLOR_FORMAT = MATPLOTLIB_COLOR_FORMAT = ColorFormat(color_sys=HexRGB)