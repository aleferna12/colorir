"""Common color spaces and systems.

This module contains different classes that represent a few of the most common color spaces [#]_.
Colors can be compared, converted to and passed as arguments to different classes.

Examples:
    Create some colors and compare them:

    >>> sRGB(255, 0, 0) == HSL(0, 1 , 0.5)
    True

    Convert an RGB color to CMYK:

    >>> rgb_red = sRGB(255, 0, 0)
    >>> rgb_red.cmyk()
    CMYK(0.0, 1.0, 1.0, 0.0)

    Compare the perceived distance between two colors:

    >>> simplified_dist(HexRGB("#ff0000"), HexRGB("#ffff00"))
    2.0

References:
    .. [#] Wikipedia at https://en.wikipedia.org/wiki/Color_model.
"""
import colorsys
import abc
import math
from math import sqrt
from typing import Union
import colorir

ColorLike = Union["ColorBase", str, tuple]


class ColorBase(metaclass=abc.ABCMeta):
    """Base class from which all color classes inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """

    @abc.abstractmethod
    def __new__(cls, rgba: tuple, **kwargs):
        obj = super().__new__(cls)
        obj._rgba = tuple(rgba)
        return obj

    def __eq__(self, other):
        return self._rgba == other._rgba if isinstance(other, ColorBase) else False

    def get_format(self):
        """Returns a :class:`~colorir.color_format.ColorFormat` representing the format of this
        color object."""
        format_ = {k: v for k, v in self.__dict__.items() if k != "_rgba"}
        return colorir.color_format.ColorFormat(self.__class__, **format_)

    @classmethod
    @abc.abstractmethod
    def _from_rgba(cls, rgba, **kwargs):
        # Factory method to be called when reading the palette files or reconstructing colors
        pass

    def hex(self, **kwargs) -> "HexRGB":
        """Converts the current color to a hexadecimal representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`HexRGB` constructor.
        """
        return HexRGB._from_rgba(self._rgba, **kwargs)

    def rgb(self, **kwargs) -> "sRGB":
        """Converts the current color to an sRGB representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`sRGB` constructor.
        """
        return sRGB._from_rgba(self._rgba, **kwargs)

    def hsl(self, **kwargs) -> "HSL":
        """Converts the current color to an HSL representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`HSL` constructor.
        """
        return HSL._from_rgba(self._rgba, **kwargs)

    def hsv(self, **kwargs) -> "HSV":
        """Converts the current color to an HSV representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`HSV` constructor.
        """
        return HSV._from_rgba(self._rgba, **kwargs)

    def cmyk(self, **kwargs) -> "CMYK":
        """Converts the current color to a CMYK representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`CMYK` constructor.
        """
        return CMYK._from_rgba(self._rgba, **kwargs)

    def cmy(self, **kwargs) -> "CMY":
        """Converts the current color to a CMY representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`CMY` constructor.
        """
        return CMY._from_rgba(self._rgba, **kwargs)


class ColorTupleBase(ColorBase, tuple, metaclass=abc.ABCMeta):
    """Base class from which all color classes that are represented by tuples inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """

    @abc.abstractmethod
    def __new__(cls, iterable, rgba, include_a=False, round_to=-1):
        if not include_a:
            iterable = iterable[:-1]
        if round_to == 0:
            iterable = [round(val) for val in iterable]
        elif round_to > 0:
            iterable = [round(val, round_to) for val in iterable]
        obj = tuple.__new__(cls, iterable)
        obj._rgba = tuple(rgba)
        obj.include_a = include_a
        obj.round_to = round_to

        return obj

    def __repr__(self):
        return f"{self.__class__.__name__}{tuple.__repr__(self)}"

    def __eq__(self, other):
        if isinstance(other, ColorBase):
            return ColorBase.__eq__(self, other)
        return tuple.__eq__(self, other)


class sRGB(ColorTupleBase):
    """Represents a color in the RGB color space [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/SRGB.

    Args:
        r: Red component of the color.
        g: Green component of the color.
        b: Blue component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max_rgba` parameter.
        max_rgba: What is the maximum value for the `r`, `g`, `b`, and `a` components. Some common
            values for this parameter would be 255 or 1.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`sRGB(255, 255, 0,
            255)` instead of :code:`sRGB(255, 255, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting this
            parameter to 0 ensures that the components will be of type ``int``. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls, r: float, g: float, b: float, a: float = None, max_rgba=255, include_a=False,
                round_to=-1):
        if a is None:
            a = max_rgba

        if any(spec > max_rgba for spec in (r, g, b, a)):
            raise ValueError("'r', 'g', 'b' and 'a' parameters of sRGB can't be larger then the "
                             "defined 'max_rgba' parameter'")

        obj = super().__new__(cls,
                              (r, g, b, a),
                              (r / max_rgba, g / max_rgba, b / max_rgba, a / max_rgba),
                              include_a=include_a,
                              round_to=round_to)
        obj.max_rgba = max_rgba
        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_rgba=255, include_a=False, round_to=-1):
        rgba_ = [spec * max_rgba for spec in rgba]
        obj = super().__new__(cls,
                              rgba_,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.max_rgba = max_rgba
        return obj


class HSL(ColorTupleBase):
    """Represents a color in the HSL color space [#]_.

    .. [#] Wikipedia at https://en.wikipedia.org/wiki/HSL_and_HSV.

    Args:
        h: HUE component of the color.
        s: Saturation component of the color.
        l: Lightness component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max_sla` parameter.
        max_h:  What is the maximum value for the `h` component. Some common values for this
            parameter would be 360 or 1.
        max_sla:  What is the maximum value for the `s`, `l` and `a` components. Some common values
            for this parameter would be 1 or 100.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`HSL(360, 1, 0,
            1)` instead of :code:`HSL(360, 1, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting this
            parameter to 0 ensures that the components will be of type ``int``. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls, h: float, s: float, l: float, a: float = None, max_h=360, max_sla=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_sla

        if h > max_h:
            raise ValueError(
                "'h' parameter of HSL can't be larger then the defined 'max_h' parameter'")
        if any(spec > max_sla for spec in (s, l, a)):
            raise ValueError(
                "'s', 'l' and 'a' parameters of HSL can't be larger then the defined 'max_sla' "
                "parameter'")

        rgba = colorsys.hls_to_rgb(h / max_h, l / max_sla, s / max_sla) + (a / max_sla,)
        obj = super().__new__(cls, (h, s, l, a), rgba, include_a=include_a, round_to=round_to)
        obj.max_h = max_h
        obj.max_sla = max_sla

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_sla=1, include_a=False, round_to=-1):
        hls = colorsys.rgb_to_hls(*rgba[:-1])
        hsla = (hls[0] * max_h, hls[2] * max_sla, hls[1] * max_sla, rgba[-1] * max_sla)

        obj = super().__new__(cls,
                              hsla,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.max_h = max_h
        obj.max_sla = max_sla
        return obj


class HSV(ColorTupleBase):
    """Represents a color in the HSV color space [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/HSL_and_HSV.

    Args:
        h: HUE component of the color.
        s: Saturation component of the color.
        v: Value component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max_sva` parameter.
        max_h:  What is the maximum value for the `h` component. Some common values for this
            parameter would be 360 or 1.
        max_sva:  What is the maximum value for the `s`, `v` and `a` components. Some common values
            for this parameter would be 1 or 100.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`HSV(360, 1, 0,
            1)` instead of :code:`HSV(360, 1, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting this
            parameter to 0 ensures that the components will be of type ``int``. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls, h: float, s: float, v: float, a: float = None, max_h=360, max_sva=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_sva

        if h > max_h:
            raise ValueError(
                "'h' parameter of HSL can't be larger then the defined 'max_h' parameter'")
        if any(spec > max_sva for spec in (s, v, a)):
            raise ValueError(
                "'s', 'v' and 'a' parameters of HSL can't be larger then the defined 'max_sva' "
                "parameter'")

        rgba = colorsys.hsv_to_rgb(h / max_h, s / max_sva, v / max_sva) + (a / max_sva,)
        obj = super().__new__(cls, (h, s, v, a), rgba, include_a=include_a, round_to=round_to)
        obj.max_h = max_h
        obj.max_sva = max_sva

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_sva=1, include_a=False, round_to=-1):
        hsv = colorsys.rgb_to_hsv(*rgba[:-1])
        hsva = (hsv[0] * max_h, hsv[1] * max_sva, hsv[2] * max_sva, rgba[-1] * max_sva)

        obj = super().__new__(cls,
                              hsva,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.max_h = max_h
        obj.max_sva = max_sva
        return obj


class CMYK(ColorTupleBase):
    """Represents a color in the CMYK color space [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/CMYK_color_model.

    Args:
        c: Cyan component of the color.
        m: Magenta component of the color.
        y: Yellow component of the color.
        k: Key (black) component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max` parameter.
        max_cmyka: What is the maximum value for the `c`, `m`, `y`, `k` and `a` components. Some
            common values for this parameter would be 1 or 100.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`CMYK(1, 1, 0,
            1)` instead of :code:`CMYK(1, 1, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type ``int``. The default,
            -1, means that the components won't be rounded at all.
    """

    def __new__(cls, c: float, m: float, y: float, k: float, a: float = None, max_cmyka=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_cmyka

        if any(spec > max_cmyka for spec in (c, m, y, k, a)):
            raise ValueError("'c', 'm', 'y', 'k' and 'a' parameters of CMYK can't be larger then"
                             " the defined 'max' parameter'")

        r = (1 - c / max_cmyka) * (1 - k / max_cmyka)
        g = (1 - m / max_cmyka) * (1 - k / max_cmyka)
        b = (1 - y / max_cmyka) * (1 - k / max_cmyka)

        obj = super().__new__(cls, (c, m, y, k, a), (r, g, b, a / max_cmyka), include_a=include_a,
                              round_to=round_to)
        obj.max_cmyka = max_cmyka

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_cmyka=1, include_a=False, round_to=-1):
        if sum(rgba[:-1]) == 0:
            cmyka = (0, 0, 0, max_cmyka, rgba[-1] * max_cmyka)

        else:
            c = 1 - rgba[0]
            m = 1 - rgba[1]
            y = 1 - rgba[2]

            k = min(c, m, y)
            c = (c - k) / (1 - k)
            m = (m - k) / (1 - k)
            y = (y - k) / (1 - k)
            cmyka = [spec * max_cmyka for spec in (c, m, y, k, rgba[-1])]

        obj = super().__new__(cls,
                              cmyka,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.max_cmyka = max_cmyka
        return obj


class CMY(ColorTupleBase):
    """Represents a color in the CMY color space [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/CMY_color_model.


    Args:
        c: Cyan component of the color.
        m: Magenta component of the color.
        y: Yellow component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max` parameter.
        max_cmya: What is the maximum value for the `c`, `m`, `y` and `a` components. Some common
            values for this parameter would be 1 or 100.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`CMY(1, 1, 0,
            1)` instead of :code:`CMY(1, 1, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type ``int``. The default,
            -1, means that the components won't be rounded at all.
    """

    def __new__(cls, c: float, m: float, y: float, a: float = None, max_cmya=1, include_a=False,
                round_to=-1):
        if a is None:
            a = max_cmya

        if any(spec > max_cmya for spec in (c, m, y, a)):
            raise ValueError("'c', 'm', 'y' and 'a' parameters of CMY can't be larger then"
                             " the defined 'max' parameter'")

        obj = super().__new__(cls,
                              (c, m, y, a),
                              (1 - c / max_cmya, 1 - m / max_cmya, 1 - y / max_cmya, a / max_cmya),
                              include_a=include_a,
                              round_to=round_to)
        obj.max_cmya = max_cmya

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_cmya=1, include_a=False, round_to=-1):

        obj = super().__new__(cls,
                              [spec * max_cmya for spec in
                               (1 - rgba[0], 1 - rgba[1], 1 - rgba[2], rgba[-1])],
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.max_cmya = max_cmya
        return obj


class HexRGB(ColorBase, str):
    """Represents a color in the RGB color space [#]_ as a hexadecimal string.

    Is mostly used for representing colors in web applications [#]_.

    Be aware that printing objects of this class with ``print()`` makes it look like the object
    is a ``str``.

    >>> red = HexRGB("#ff0000")
    >>> print(red)
    #ff0000
    >>> red # red is NOT a simple string, but a subclass of it
    HexRGB(#ff0000)

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/SRGB.
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/Web_colors

    Args:
        hex_str: Hexadecimal string from which the :class:`HexRGB` instance will be built.
            May or may not include a "#" character in its beginning.
        uppercase: Whether the color will be represented in uppercase or lowercase.
        include_a: Whether to include the opacity parameter `a` in the constructed string.
            Setting it to ``True`` may result in an object such as :code:`HexRGB('#ffffff00')`
            instead of :code:`HexRGB('#ffff00')`, for exemple.
    """

    def __new__(cls, hex_str: str, uppercase=False, include_hash=True, include_a=False):
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            a = 1
        elif len(hex_str) == 8:
            a = int(hex_str[:2], 16) / 255
        else:
            raise ValueError(
                "'hex_str' parameter of 'HexRGB' class should be either 6 or 8 characters long "
                "(disregarding the '#' at the begging)")
        rgb = (int(hex_str[-6:-4], 16) / 255,
               int(hex_str[-4:-2], 16) / 255,
               int(hex_str[-2:], 16) / 255)

        if uppercase:
            hex_str = hex_str.upper()
        if include_hash:
            hex_str = '#' + hex_str
        obj = str.__new__(cls, hex_str)
        obj._rgba = rgb + (a,)
        obj.uppercase = uppercase
        obj.include_a = include_a
        return obj

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"

    def __eq__(self, other):
        return ColorBase.__eq__(self, other) if isinstance(other, ColorBase) else str.__eq__(self,
                                                                                             other)

    @classmethod
    def _from_rgba(cls, rgba, uppercase=False, include_hash=True, include_a=False):
        rgba_ = tuple([int(spec * 255) for spec in rgba])
        hex_str = '%02x%02x%02x' % rgba_[:3]

        if include_a:
            hex_str = '%02x' % rgba_[-1] + hex_str
        if uppercase:
            hex_str = hex_str.upper()
        if include_hash:
            hex_str = '#' + hex_str

        obj = str.__new__(cls, hex_str)
        obj.uppercase = uppercase
        obj.include_a = include_a
        obj._rgba = tuple(rgba)
        return obj


def simplified_dist(color1: ColorBase, color2: ColorBase):
    """Calculates the perceived distance between two colors.

    Although there are many methods to approach the similarity of colors mathematically, the
    algorithm implemented in this function [#]_ tries to provide balance between a fast and
    efficient computation.

    References:
        .. [#] Colour metric by Thiadmer Riemersma. Available on
            https://www.compuphase.com/cmetric.htm.
    """
    rgba1, rgba2 = color1._rgba, color2._rgba
    avg_r = (rgba1[0] + rgba2[0]) / 2
    d_r = rgba1[0] - rgba2[0]
    d_g = rgba1[1] - rgba2[1]
    d_b = rgba1[2] - rgba2[2]
    return sqrt((2 + avg_r) * d_r**2
                + 4 * d_g**2
                + (2 + 1 - avg_r) * d_b**2)
