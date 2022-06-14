"""Color format specifications for creating and interpreting representations of colors.

Often only describing a color system is not enough when dealing with libraries and frameworks
specifications. For example, both Kivy [1]_ and PyGame [2]_ use mostly RGB colors as inputs when
building applications. However, Kivy expects the colors to have a maximum value of 1, while PyGame
expects it to be 255. To bridge these expectations and allow the use of the same set of colors for
multiple projects across different frameworks, the :class:`ColorFormat` class was created.
This class can be used to build strictly defined formats which allows the creation and
interpretation of colors using :meth:`ColorFormat.new_color()` and :meth:`ColorFormat.format()`
respectively.

Interpreting color-like objects
-------------------------------

Most functions and classes of :mod:`colorir` can take as a parameter a type called
:const:`ColorLike`. This type stands for any common representation of color, such as those using
strings or tuples. The function/class is then able to interpret such a format using a color format
we provide or the default color format (see notes section at the end).

However, not all representation of a color can be understood by all :class:`ColorFormat` instances.
A tuple representation of red in RGB such as ``(255, 0, 0)``, for example, cannot be understood
by a color format such as ``ColorFormat(HexRGB)``. This is because there are many ways to represent
red as a tuple of three elements, such as ``(0, 1, 0.5)`` in HSL or as ``(1, 0, 0)`` in RGB with
a maximum value of 1 for each color spectrum, and a color format based on the HexRGB system is
incapable of diferentiating them. Because of this, for a color format to understand a tuple
(or list) representation of a color, it must itself be based on a tuple representation.

Other representations of color are unambiguous, and can safely be interpreted by any
:class:`ColorFormat`. A hex string of six elements such as ``"#ff0000"`` or ``"ff0000"`` is
understood universally, for example.

    .. list-table::
        :header-rows: 1

        * - Color representation
          - :class:`ColorFormat` that can understand it

        * - Tuple or list (e.g.: ``(255, 0, 0)``, ``(0, 1, 0.5)``)
          - Any tuple-based color format (e.g.: ``ColorFormat(sRGB, ...)``,
            ``ColorFormat(HSL, ...)``)

        * - Hex string with six elements (e.g.: ``"#ff0000"``)
          - Any

        * - Hex string with eight elements (e.g.: ``"#ff0000"``)
          - Hex string color format (e.g.: ``ColorFormat(HexRGB, ...)``)

Built-in color formats
----------------------

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

    >>> from colorir import WEB_COLOR_FORMAT
    >>> config.DEFAULT_COLOR_FORMAT = WEB_COLOR_FORMAT
    >>> basic_colors = Palette.load("basic") # Loads colors as hex codes
    >>> # ... code

    Create our own color format to work with HSL colors:

    >>> hsl_format = ColorFormat(colorir.color.HSL, max_h=100, max_sla=100, round_to=0)

    We can then create colors using the :meth:`ColorFormat.new_color()` and
    :meth:`ColorFormat.format()` methods:

    >>> hsl_format.new_color(30, 70, 70)
    HSL(30, 70, 70)

    >>> hsl_format.format((30, 70, 70))
    HSL(30, 70, 70)

Notes:
    To change the default color format to a custom or pre-built color format, take
    a look at :const:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.

References:
    .. [1] Kivy: Cross-platform Python Framework for NUI Development at https://kivy.org/.
    .. [2] PyGame library at https://www.pygame.org/.
"""
from typing import Type, Union, NewType
import colorir

ColorLike = NewType("ColorLike", Union["colorir.color.ColorBase", str, tuple, list])
"""Type constant that describes common representations of colors in python."""


class ColorFormat:
    """Class to create color format specifications.

    Args:
        color_sys: The color system that is the basis of this color format.
        kwargs: Keyword arguments that further specify the color format. These are specific to each
        color system and can be consulted in their respective documentations.

    Examples:
        >>> c_format = ColorFormat(colorir.color.sRGB, max_rgb=1)
        >>> c_format.new_color(1, 0, 0)
        sRGB(1, 0, 0)

        For more examples see the documentation of the :mod:`color_format` module.
    """
    def __init__(self, color_sys: Type["colorir.color.ColorBase"], **kwargs):
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
        param_strs = [f"{param}={val.__repr__()}" for param, val in self._format_params.items()]
        color_sys_str = f"color_sys={self.color_sys.__name__}"
        if param_strs:
            color_sys_str += ", "
        return f"{self.__class__.__name__}({color_sys_str}{', '.join(param_strs)})"

    def new_color(self, *args, **kwargs) -> "colorir.color.ColorBase":
        """Creates a new color by filling the remaining parameters of a color constructor with the
        provided arguments.

        Examples:
            >>> c_format = ColorFormat(colorir.color.sRGB,
            ...                        max_rgb=1,
            ...                        max_a=1,
            ...                        include_a=True)
            >>> c_format.new_color(1, 0, 0)
            sRGB(1, 0, 0, 1)
        """
        kwargs.update(self._format_params)
        return self.color_sys(*args, **kwargs)

    def _from_rgba(self, rgba):
        # Factory method to be called when reading the palette files or reconstructing colors
        return self.color_sys._from_rgba(rgba, **self._format_params)

    def format(self, color: ColorLike) -> "colorir.color.ColorBase":
        """Tries to format a color-like object into this color format.

        Because there are multiple implementations of tuple-based color systems, the `color`
        parameter is always allowed to be a subclass of :class:`~colorir.color.ColorBase` or a hex
        string with length == 6, but can only be a tuple if :attr:`ColorFormat.color_sys` is a
        tuple-based color system, such as :class:`~colorir.color.sRGB` for example.

        Examples:
            >>> rgb_format = ColorFormat(colorir.color.sRGB, round_to=0)
            >>> rgb_format.format("#ff0000")
            sRGB(255, 0, 0)
            >>> rgb_format.format((255, 0, 0))
            sRGB(255, 0, 0)
            >>> hex_format = ColorFormat(colorir.color.HexRGB)
            >>> hex_format.format("#ff0000")
            HexRGB('#ff0000')
            >>> hex_format.format((255, 0, 0)) # Can't understand how to parse this tuple
            Traceback (most recent call last):
              ...
            ValueError: tried to interpret a tuple-formatted color object with a HexRGB ColorFormat

        Args:
            color: The value of the color to be formatted. Can be an instance of any
                :mod:`~colorir.color` class or, alternatively, a color-like object that
                resembles the format of the color you want to format.
        """
        if isinstance(color, colorir.color.ColorBase):
            return self._from_rgba(color._rgba)
        elif isinstance(color, str):
            # Try to preserve input options (none implemented now but who knows)
            if self.color_sys == colorir.color.HexRGB:
                return self.new_color(color)
            # No alpha in the string, safe to interpret with HexRGB
            if len(color) < 8:
                # Fallback to HexRGB default args
                return self._from_rgba(colorir.color.HexRGB(color)._rgba)
            raise ValueError("tried to interpret a string-formatted color that contains an alpha"
                             "component with a non-HexRGB ColorFormat")
        if self.color_sys != colorir.color.HexRGB:
            # Assume that the color system is tuple-based
            return self.new_color(*color)
        else:
            raise ValueError("tried to interpret a tuple-formatted color object with a HexRGB "
                             "ColorFormat")


PYGAME_COLOR_FORMAT = ColorFormat(color_sys=colorir.color.sRGB, max_rgb=255, max_a=255, round_to=0)
"""Color format compatible with PyGame standards."""

KIVY_COLOR_FORMAT = ColorFormat(color_sys=colorir.color.sRGB, max_rgb=1, max_a=1, include_a=True)
"""Color format compatible with Kivy standards."""

WEB_COLOR_FORMAT = ColorFormat(color_sys=colorir.color.HexRGB)
"""Color format compatible with HTML and CSS standards."""

TKINTER_COLOR_FORMAT = WEB_COLOR_FORMAT
"""Color format compatible with Tkinter standards."""

MATPLOTLIB_COLOR_FORMAT = WEB_COLOR_FORMAT
"""Color format compatible with Matplotlib."""
