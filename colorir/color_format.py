"""Color format specifications for creating and interpreting representations of colors.

Often only describing a color system is not enough when dealing with libraries and frameworks
specifications. For example, both Kivy [1]_ and PyGame [2]_ use mostly RGB colors as inputs when
building applications. However, Kivy expects the colors to have a maximum value of 1, while PyGame
expects it to be 255. To bridge these expectations and allow the use of the same set of colors for
multiple projects across different frameworks, the :class:`ColorFormat` class was created.
This class can be used to build strictly defined formats which act as a template for the creation and
interpretation of colors using :meth:`ColorFormat.new_color()` and :meth:`ColorFormat.format()`
respectively.

Interpreting color-like objects
-------------------------------

Most functions and classes of colorir can take as a parameter a type called
:const:`ColorLike`. This type stands for any common representation of color, such as those using
strings or tuples. The function/class is then able to interpret such a format using a color format
we provide or the default color format (see notes section at the end).

However, not all representation of a color can be understood by all :class:`ColorFormat` instances.
A tuple representation of red in RGB such as ``(255, 0, 0)``, for example, cannot be understood
by a color format such as ``ColorFormat(Hex)``. This is because there are many ways to represent
red as a tuple of three elements, such as ``(0, 1, 0.5)`` in HSL or as ``(1, 0, 0)`` in RGB with
a maximum value of 1 for each color spectrum, and a color format based on the Hex system is
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
          - Any tuple-based color format (e.g.: ``ColorFormat(sRGB)``,
            ``ColorFormat(HSL)``)

        * - Hex string with six elements (e.g.: ``"#ff0000"``)
          - Any

        * - Hex string with eight elements (e.g.: ``"#ff0000"``)
          - Hex string color format (e.g.: ``ColorFormat(Hex)``)

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

    >>> hsl_format = ColorFormat(color_class.HSL, max_h=100, max_sla=100, round_to=0)

    We can then create colors using the :meth:`ColorFormat.new_color()` and
    :meth:`ColorFormat.format()` methods:

    >>> hsl_format.new_color(30, 70, 70)
    HSL(30, 70, 70)

    >>> hsl_format.format((30, 70, 70))
    HSL(30, 70, 70)

Notes:
    To change the default color format to a custom or pre-built color format, take
    a look at :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.

References:
    .. [1] Kivy: Cross-platform Python Framework for NUI Development at https://kivy.org/.
    .. [2] PyGame library at https://www.pygame.org/.
"""
from typing import Type
from . import color_class

__all__ = [
    "ColorFormat",
    "FormatError",
    "PYGAME_COLOR_FORMAT",
    "TKINTER_COLOR_FORMAT",
    "KIVY_COLOR_FORMAT",
    "WEB_COLOR_FORMAT",
    "MATPLOTLIB_COLOR_FORMAT"
]


class ColorFormat:
    """Class to create color format specifications.

    Args:
        color_sys: The color system that is the basis of this color format.
        format_kwargs: Keyword arguments that further specify the color format. These are specific
            to each color system and can be consulted in their respective documentations.

    Examples:
        >>> c_format = ColorFormat(color_class.sRGB, max_rgb=1)
        >>> c_format.new_color(1, 0, 0)
        RGB(1, 0, 0)

        For more examples see the documentation of the :mod:`~colorir.color_format` module.
    """
    def __init__(self, color_sys: Type["color_class.ColorBase"], **format_kwargs):
        self.color_sys = color_sys
        self.format_params = format_kwargs

    def __getattr__(self, item):
        # __getattr__ is called only when super().__getattribute__ fails
        try:
            return self.format_params[item]
        except LookupError as e:
            raise AttributeError(f"AttributeError: '{self.__class__.__name__}' object has no "
                                 f"attribute '{item}'") from e

    def __call__(self, *args, **kwargs):
        return self.new_color(*args, **kwargs)

    def __repr__(self):
        param_strs = [f"{param}={val.__repr__()}" for param, val in self.format_params.items()]
        color_sys_str = f"color_sys={self.color_sys.__name__}"
        if param_strs:
            color_sys_str += ", "
        return f"{self.__class__.__name__}({color_sys_str}{', '.join(param_strs)})"

    def new_color(self, *args, **kwargs) -> "color_class.ColorBase":
        """Creates a new color by filling the remaining parameters of a color constructor with the
        provided arguments.

        Examples:
            >>> c_format = ColorFormat(color_class.sRGB,
            ...                        max_rgb=1,
            ...                        max_a=1,
            ...                        include_a=True)
            >>> c_format.new_color(1, 0, 0)
            RGB(1, 0, 0, 1)
        """
        kwargs.update(self.format_params)
        return self.color_sys(*args, **kwargs)

    # Factory method to be called when reading the palette files or reconstructing colors
    def _from_rgba(self, rgba):
        return self.color_sys._from_rgba(rgba, **self.format_params)

    def format(self, color: "color_class.ColorLike") -> "color_class.ColorBase":
        """Tries to format a color-like object into this color format.

        Because there are multiple implementations of tuple-based color systems, the `color`
        parameter is always allowed to be a subclass of :class:`~colorir.color_class.ColorBase` or
        a hex string with length == 6, but can only be a tuple if :attr:`ColorFormat.color_sys` is
        a tuple-based color system, such as :class:`~colorir.color_class.sRGB` for example.

        Examples:
            >>> rgb_format = ColorFormat(color_class.sRGB, round_to=0)
            >>> rgb_format.format("#ff0000")
            RGB(1, 0, 0)
            >>> rgb_format.format((1, 0, 0))
            RGB(1, 0, 0)
            >>> hex_format = ColorFormat(color_class.Hex)
            >>> hex_format.format("#ff0000")
            Hex('#ff0000')
            >>> hex_format.format((1, 0, 0)) # Can't understand how to parse this tuple
            Traceback (most recent call last):
              ...
            colorir.color_format.FormatError: tried to interpret a tuple-formatted color with a Hex-based ColorFormat

        Args:
            color: The value of the color to be formatted. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the format of the color you want to format.
        """
        if isinstance(color, color_class.ColorBase):
            with _wrap_format_error():
                return self._from_rgba(color._rgba)
        if isinstance(color, str):
            # Try to preserve input options
            if self.color_sys == color_class.Hex:
                with _wrap_format_error():
                    return self.new_color(color)
            # No alpha in the string, safe to interpret with Hex
            if len(color) < 8:
                # Fallback to Hex default args
                with _wrap_format_error():
                    return self._from_rgba(color_class.Hex(color)._rgba)
            raise FormatError("tried to interpret a string-formatted color that contains an alpha"
                              "component with a non-Hex ColorFormat")
        if hasattr(color, "__iter__"):
            if self.color_sys == color_class.Hex:
                raise FormatError("tried to interpret a tuple-formatted color with a Hex-based ColorFormat")
            with _wrap_format_error():
                return self.new_color(*color)
        raise FormatError()


class FormatError(Exception):
    def __init__(self, message="An error occurred when trying to format this color"):
        super().__init__(message)


class _wrap_format_error:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            raise FormatError()


PYGAME_COLOR_FORMAT = ColorFormat(color_sys=color_class.RGB, max_rgb=255, max_a=255, round_to=0)
"""Color format compatible with PyGame standards."""

KIVY_COLOR_FORMAT = ColorFormat(color_sys=color_class.sRGB,
                                max_rgb=1,
                                max_a=1,
                                round_to=-1,
                                include_a=True)
"""Color format compatible with Kivy standards."""

MATPLOTLIB_COLOR_FORMAT = ColorFormat(color_sys=color_class.Hex, include_a=True, tail_a=True)
"""Color format compatible with Matplotlib."""

WEB_COLOR_FORMAT = ColorFormat(color_sys=color_class.Hex, tail_a=True)
"""Color format compatible with HTML and CSS standards."""

TKINTER_COLOR_FORMAT = WEB_COLOR_FORMAT
"""Color format compatible with Tkinter standards."""
