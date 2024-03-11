"""Common color spaces and systems.

This module contains different classes that represent a few of the most common color spaces [#]_.
Colors can be compared, converted to and passed as arguments to different classes.

Examples:
    Create some colors and compare them:

    >>> RGB(1, 0, 0) == HSL(0, 1 , 0.5)
    True

    Convert an RGB color to CMYK:

    >>> rgb_red = RGB(1, 0, 0)
    >>> rgb_red.cmyk()
    CMYK(0.0, 1.0, 1.0, 0.0)

    Color arithmetic makes it easy to change the properties of a color.
    The operations are performed element-wise in the format of the color used as the right operand,
    allowing specific color components to be changed in the color on the left of the operator.
    If the right operand is not a color, but rather a tuple, than the left color is not converted
    prior to the operation being performed.

    Add some CIE lightness to the color black (right operand is CIELab, meaning that the Hex color will be converted
    to CIELab before adding 50 to its lighness value and then converted back to Hex):

    >>> Hex("#000000") + CIELab(50, 0, 0)
    Hex('#777777')

    Make a red 50% less saturated by multiplying its saturation component by 0.5 (here no conversion is performed
    because the right operand is a tuple rather than a color class):

    >>> HSV(0.0, 1.0, 1.0) * (1, 0.5, 1)
    HSV(0.0, 0.5, 1.0)

References:
    .. [#] Wikipedia at https://en.wikipedia.org/wiki/Color_model.
"""
import abc
import colorsys
import operator
import warnings

import numpy as np
from typing import List, Union
from .colormath.color_objects import (
    LabColor,
    LuvColor,
    LCHuvColor,
    sRGBColor,
    LCHabColor,
    CMYColor,
    CMYKColor
)
from .colormath.color_conversions import convert_color

import colorir

__all__ = [
    "ColorLike",
    "ColorBase",
    "ColorTupleBase",
    "ColorPolarBase",
    "RGB",
    "sRGB",
    "HSV",
    "HSL",
    "CMY",
    "CMYK",
    "CIELuv",
    "CIELab",
    "HCLuv",
    "HCLab",
    "Hex"
]


class ColorBase(metaclass=abc.ABCMeta):
    """Base class from which all color classes inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """
    _rgba: np.ndarray
    _format_params: List[str]

    # Factory method to be called when reading the palette files or reconstructing colors
    @classmethod
    @abc.abstractmethod
    def _from_rgba(cls, rgba, **kwargs):
        pass

    @property
    def format(self) -> "colorir.color_format.ColorFormat":
        """Returns a :class:`~colorir.color_format.ColorFormat` representing the format of this
        color object."""
        format_ = {param: getattr(self, param) for param in self._format_params}
        return colorir.color_format.ColorFormat(self.__class__, **format_)

    def __eq__(self, other):
        try:
            if not isinstance(other, ColorBase):
                other = colorir.config.DEFAULT_COLOR_FORMAT.format(other)
            return np.all(np.rint(self._rgba) == np.rint(other._rgba))
        except colorir.color_format.FormatError:
            return NotImplemented

    def __hash__(self):
        return hash(tuple(self._rgba))

    def __invert__(self):
        """Gets the inverse RGB of this color."""
        return self.format._from_rgba(np.append(255 - self._rgba[:-1], self._rgba[-1]))

    def __mod__(self, other):
        """Blends two colors at 50% using :func:`colorir.utils.blend()`."""
        return colorir.blend(self, other)

    def __add__(self, other):
        """Adds two colors or a color (as the left operand) and a tuple (as the right operand) together."""
        return self._arithm_func(other, operator.add)

    def __sub__(self, other):
        """Subtracts one color from another or a tuple (the right operand) from a color (the left operand)."""
        return self._arithm_func(other, operator.sub)

    def __mul__(self, other):
        """Multiplies two colors or a color (as the left operand) and a tuple (as the right operand) together."""
        return self._arithm_func(other, operator.mul)

    def __truediv__(self, other):
        """Divides two colors or a color (as the left operand) and a tuple (as the right operand) together."""
        return self._arithm_func(other, operator.truediv)

    def grayscale(self):
        """Converts this color to a grayscale representation in the same format using CIE
        lightness component."""
        return self.format.format(CIELuv(self.cieluv().l, 0, 0))

    def hex(self, **kwargs) -> "Hex":
        """Converts the current color to a hexadecimal representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`Hex` constructor.
        """
        return Hex._from_rgba(self._rgba, **kwargs)

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

    def cieluv(self, **kwargs) -> "CIELuv":
        """Converts the current color to a CIELuv representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`CIELuv` constructor.
        """
        return CIELuv._from_rgba(self._rgba, **kwargs)

    def cielab(self, **kwargs) -> "CIELab":
        """Converts the current color to a CIELab representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`CIELab` constructor.
        """
        return CIELab._from_rgba(self._rgba, **kwargs)

    def hcluv(self, **kwargs) -> "HCLuv":
        """Converts the current color to a HCLuv representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`HCLuv` constructor.
        """
        return HCLuv._from_rgba(self._rgba, **kwargs)

    def hclab(self, **kwargs) -> "HCLab":
        """Converts the current color to a HCLab representation.

        Args:
            **kwargs: Keyword arguments wrapped in this function will be passed on to the
                :class:`HCLab` constructor.
        """
        return HCLab._from_rgba(self._rgba, **kwargs)

    def _arithm_func(self, other, foo):
        if not isinstance(other, ColorTupleBase):
            raise ValueError("operations are only possible if one of the colors is tuple-based")
        vals = tuple(map(foo, other.format.format(self), other))
        return self.format.format(other.format.format(vals))


class ColorTupleBase(ColorBase, tuple, metaclass=abc.ABCMeta):
    """Base class from which all color classes that are represented by tuples inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """

    @abc.abstractmethod
    def __new__(cls, specs, a, rgba, include_a, round_to):
        specs = list(specs)
        if round_to == 0:
            specs = [round(val) for val in specs]
            a = round(a)
        elif round_to > 0:
            specs = [round(val, round_to) for val in specs]
            a = round(a, round_to)
        if include_a:
            specs.append(a)
        obj = tuple.__new__(cls, specs)
        obj.a = a
        obj.include_a = include_a
        obj.round_to = round_to
        obj._rgba = np.rint(rgba).astype(int)
        obj._format_params = ["include_a", "round_to"]

        return obj

    # It would be dangerous to change str conversion as the target framework could call it
    # expecting (255, 0, 0) and get RGB(255, 0, 0)
    def __str__(self):
        return tuple.__repr__(self)

    def __repr__(self):
        if colorir.config.REPR_STYLE == "traditional":
            return f"{self.__class__.__name__}{tuple.__repr__(self)}"
        if colorir.config.REPR_STYLE == "inherit":
            return str(self)
        return colorir.utils.swatch(self, file=None)

    def __hash__(self):
        return ColorBase.__hash__(self)

    def __eq__(self, other):
        colorbase_eq = ColorBase.__eq__(self, other)
        # If other is ColorBase than we trust the result of eq
        if isinstance(other, ColorBase):
            return colorbase_eq
        # Otherwise we also try tuple.__eq__
        return any([colorbase_eq is True, tuple.__eq__(self, other) is True])

    def __add__(self, other):
        return self._tup_arithm_func(other, operator.add)

    def __sub__(self, other):
        return self._tup_arithm_func(other, operator.sub)

    def __mul__(self, other):
        return self._tup_arithm_func(other, operator.mul)

    def __truediv__(self, other):
        return self._tup_arithm_func(other, operator.truediv)

    # If right side of the operator is not a tuple-based color, we perform the operation element-wise
    def _tup_arithm_func(self, other, foo):
        if not isinstance(other, ColorBase):
            vals = tuple(map(foo, self, other))
            return self.format.format(vals)
        return ColorBase._arithm_func(self, other, foo)


class ColorPolarBase(ColorTupleBase, metaclass=abc.ABCMeta):
    """Mixin tag indicating that the color contains a polar hue component.

    Notes:
        This class is abstract and should not be instantiated.
    """
    h: float
    max_h: float


class RGB(ColorTupleBase):
    """Represents a color in the RGB color space [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/SRGB.

    Args:
        r: Red component of the color.
        g: Green component of the color.
        b: Blue component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max_rgba` parameter.
        max_rgb: What is the maximum value for the `r`, `g` and `b` components. Some common
            values for this parameter would be 255 or 1.
        max_a : What is the maximum value for the `a` component. Some common
            values for this parameter would be 100 or 1.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`RGB(255, 255, 0,
            255)` instead of :code:`RGB(255, 255, 0)`, for example.
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type `int`. -1
            means that the components won't be rounded at all.
        linear: Whether the values are linear RGB or sRGB. It is strongly advised not to keep values as
            linear RGB, but it can be useful for quick conversions.
    """

    def __new__(cls,
                r: float,
                g: float,
                b: float,
                a: float = None,
                max_rgb=1,
                max_a=1,
                include_a=False,
                round_to=-1,
                linear=False):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not all(0 <= spec <= max_rgb for spec in (r, g, b)):
            raise ValueError("'r', 'g' and 'b' must be greater than 0 and smaller than 'max_rgb'")

        rgba = np.array((r, g, b, a), dtype=float)
        rgba[:3] /= max_rgb
        rgba[-1] /= max_a
        if linear:
            rgba = colorir.utils._to_srgb(rgba)
        rgba *= 255

        obj = super().__new__(
            cls,
            (r, g, b),
            a,
            rgba,
            include_a=include_a,
            round_to=round_to
        )
        obj.r, obj.g, obj.b = obj[:3]
        obj.max_rgb = max_rgb
        obj.max_a = max_a
        obj.linear = linear
        obj._format_params += ["max_rgb", "max_a", "linear"]

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_rgb=1, max_a=1, include_a=False, round_to=-1, linear=False):
        rgb = rgba / 255
        if linear:
            rgb = colorir.utils._to_linear_rgb(rgb)
        rgb = rgb[:-1]
        rgb *= max_rgb

        obj = super().__new__(cls,
                              rgb,
                              rgba[-1] / 255 * max_a,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.r, obj.g, obj.b = obj[:3]
        obj.max_rgb = max_rgb
        obj.max_a = max_a
        obj.linear = linear
        obj._format_params += ["max_rgb", "max_a", "linear"]
        return obj


class HSL(ColorPolarBase):
    """Represents a color in the HSL color space [#]_.

    .. [#] Wikipedia at https://en.wikipedia.org/wiki/HSL_and_HSV.

    Args:
        h: Hue component of the color.
        s: Saturation component of the color.
        l: Lightness component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max_sla` parameter.
        max_h: What is the maximum value for the `h` component. Some common values for this
            parameter would be 360 or 1.
        max_sla: What is the maximum value for the `s`, `l` and `a` components. Some common values
            for this parameter would be 1 or 100.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`HSL(360, 1, 0,
            1)` instead of :code:`HSL(360, 1, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type `int`. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls,
                h: float,
                s: float,
                l: float,
                a: float = None,
                max_h=360,
                max_sla=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_sla
        if not all(0 <= spec <= max_sla for spec in (s, l, a)):
            raise ValueError("'s', 'l' and 'a' must be greater than 0 and smaller than 'max_sla'")

        rgba = colorsys.hls_to_rgb(h % max_h / max_h, l / max_sla, s / max_sla) + (a / max_sla,)

        obj = super().__new__(cls,
                              (h, s, l),
                              a,
                              np.array(rgba) * 255,
                              include_a=include_a,
                              round_to=round_to)
        obj.h, obj.s, obj.l = obj[:3]
        obj.max_h = max_h
        obj.max_sla = max_sla
        obj._format_params += ["max_h", "max_sla"]

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_sla=1, include_a=False, round_to=-1):
        hls = colorsys.rgb_to_hls(*np.array(rgba[:-1]) / 255)
        hsl = (hls[0] * max_h, hls[2] * max_sla, hls[1] * max_sla)

        obj = super().__new__(cls,
                              hsl,
                              rgba[-1] / 255 * max_sla,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.h, obj.s, obj.l = obj[:3]
        obj.max_h = max_h
        obj.max_sla = max_sla
        obj._format_params += ["max_h", "max_sla"]

        return obj


class HSV(ColorPolarBase):
    """Represents a color in the HSV color space [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/HSL_and_HSV.

    Args:
        h: Hue component of the color.
        s: Saturation component of the color.
        v: Value component of the color.
        a: Opacity component of the color. Defaults to ``None``, which means it will be the same
            as the `max_sva` parameter.
        max_h: What is the maximum value for the `h` component. Some common values for this
            parameter would be 360 or 1.
        max_sva: What is the maximum value for the `s`, `v` and `a` components. Some common values
            for this parameter would be 1 or 100.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`HSV(360, 1, 0,
            1)` instead of :code:`HSV(360, 1, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type `int`. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls,
                h: float,
                s: float,
                v: float,
                a: float = None,
                max_h=360,
                max_sva=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_sva
        if not all(0 <= spec <= max_sva for spec in (s, v, a)):
            raise ValueError("'s', 'v' and 'a' must be greater than 0 and smaller than 'max_sva'")

        rgba = colorsys.hsv_to_rgb(h % max_h / max_h, s / max_sva, v / max_sva) + (a / max_sva,)

        obj = super().__new__(cls,
                              (h, s, v),
                              a,
                              np.array(rgba) * 255,
                              include_a=include_a,
                              round_to=round_to)
        obj.h, obj.s, obj.v = obj[:3]
        obj.max_h = max_h
        obj.max_sva = max_sva
        obj._format_params += ["max_h", "max_sva"]

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_sva=1, include_a=False, round_to=-1):
        hsv = colorsys.rgb_to_hsv(*np.array(rgba[:-1]) / 255)
        hsv = (hsv[0] * max_h, hsv[1] * max_sva, hsv[2] * max_sva)

        obj = super().__new__(cls,
                              hsv,
                              rgba[-1] / 255 * max_sva,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.h, obj.s, obj.v = obj[:3]
        obj.max_h = max_h
        obj.max_sva = max_sva
        obj._format_params += ["max_h", "max_sva"]

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
            this parameter to 0 ensures that the components will be of type `int`. The default,
            -1, means that the components won't be rounded at all.
    """

    def __new__(cls, c: float, m: float, y: float, k: float, a: float = None, max_cmyka=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_cmyka
        if not all(0 <= spec <= max_cmyka for spec in (c, m, y, k, a)):
            raise ValueError("'c', 'm', 'y', 'k', and 'a' must be greater than 0 and smaller than "
                             "'max_cmyka'")

        rgba = convert_color(
            CMYKColor(*(np.array((c, m, y, k)) / max_cmyka)),
            sRGBColor
        ).get_value_tuple() + (a / max_cmyka,)

        obj = super().__new__(cls,
                              (c, m, y, k),
                              a,
                              np.array(rgba) * 255,
                              include_a=include_a,
                              round_to=round_to)
        obj.c, obj.m, obj.y, obj.k = obj[:4]
        obj.max_cmyka = max_cmyka
        obj._format_params.append("max_cmyka")

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_cmyka=1, include_a=False, round_to=-1):
        cmyk = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            CMYKColor
        ).get_value_tuple()
        cmyk = np.array(cmyk) * max_cmyka

        obj = super().__new__(cls,
                              cmyk,
                              rgba[-1] / 255 * max_cmyka,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.c, obj.m, obj.y, obj.k = obj[:4]
        obj.max_cmyka = max_cmyka
        obj._format_params.append("max_cmyka")

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
            this parameter to 0 ensures that the components will be of type `int`. The default,
            -1, means that the components won't be rounded at all.
    """

    def __new__(cls,
                c: float,
                m: float,
                y: float,
                a: float = None,
                max_cmya=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_cmya
        if not all(0 <= spec <= max_cmya for spec in (c, m, y, a)):
            raise ValueError("'c', 'm', 'y', and 'a' must be greater than 0 and smaller than "
                             "'max_cmya'")

        rgba = convert_color(
            CMYColor(*(np.array((c, m, y)) / max_cmya)),
            sRGBColor
        ).get_value_tuple() + (a / max_cmya,)

        obj = super().__new__(
            cls,
            (c, m, y),
            a,
            np.array(rgba) * 255,
            include_a=include_a,
            round_to=round_to)
        obj.c, obj.m, obj.y = obj[:3]
        obj.max_cmya = max_cmya
        obj._format_params.append("max_cmya")

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_cmya=1, include_a=False, round_to=-1):
        cmy = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            CMYColor
        ).get_value_tuple()
        cmy = np.array(cmy) * max_cmya

        obj = super().__new__(cls,
                              cmy,
                              rgba[-1] / 255 * max_cmya,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.c, obj.m, obj.y = obj[:3]
        obj.max_cmya = max_cmya
        obj._format_params.append("max_cmya")

        return obj


# TODO doc
class CIELuv(ColorTupleBase):
    def __new__(cls, l, u, v, a=None, max_a=1, include_a=False, round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not 0 <= l <= 100:
            raise ValueError("'l' must be greater than 0 and smaller than 100")

        rgb = convert_color(LuvColor(l, u, v, illuminant="d65"), sRGBColor)
        rgba = (rgb.clamped_rgb_r * 255,
                rgb.clamped_rgb_g * 255,
                rgb.clamped_rgb_b * 255,
                a / max_a * 255)
        obj = super().__new__(cls, (l, u, v), a, rgba, include_a=include_a, round_to=round_to)
        obj.l, obj.u, obj.v = obj[:3]
        obj.max_a = max_a
        obj._format_params.append("max_a")

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_a=1, include_a=False, round_to=-1):
        luv = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LuvColor,
            target_illuminant="d65"
        ).get_value_tuple()
        obj = super().__new__(cls,
                              luv,
                              rgba[-1] / 255 * max_a,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.l, obj.u, obj.v = obj[:3]
        obj.max_a = max_a
        obj._format_params.append("max_a")

        return obj


# TODO doc
class CIELab(ColorTupleBase):
    def __new__(cls, l, a_, b, a=None, max_a=1, include_a=False, round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not 0 <= l <= 100:
            raise ValueError("'l' must be greater than 0 and smaller than 100")

        rgb = convert_color(LabColor(l, a_, b, illuminant="d65"), sRGBColor)
        rgba = (rgb.clamped_rgb_r * 255,
                rgb.clamped_rgb_g * 255,
                rgb.clamped_rgb_b * 255,
                a / max_a * 255)
        obj = super().__new__(cls, (l, a_, b), a, rgba, include_a=include_a, round_to=round_to)
        obj.l, obj.a_, obj.b = l, a_, b
        obj.max_a = max_a
        obj._format_params.append("max_a")

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_a=1, include_a=False, round_to=-1):
        lab = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LabColor,
            target_illuminant="d65"
        ).get_value_tuple()

        obj = super().__new__(cls,
                              lab,
                              rgba[-1] / 255 * max_a,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.l, obj.a_, obj.b = obj[:3]
        obj.max_a = max_a
        obj._format_params.append("max_a")

        return obj


# TODO doc
class HCLuv(ColorPolarBase):
    def __new__(cls, h, c, l, a=None, max_h=360, max_a=1, include_a=False, round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not 0 <= l <= 100:
            raise ValueError("'l' must be greater than 0 and smaller than 100")

        rgb = convert_color(
            LCHuvColor(l, c, h / max_h * 360 % 360, illuminant="d65"),
            sRGBColor
        )
        rgba = (rgb.clamped_rgb_r * 255,
                rgb.clamped_rgb_g * 255,
                rgb.clamped_rgb_b * 255,
                a / max_a * 255)
        obj = super().__new__(cls,
                              (h, c, l),
                              a,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.h, obj.c, obj.l = obj[:3]
        obj.max_h = max_h
        obj.max_a = max_a
        obj._format_params += ["max_h", "max_a"]

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_a=1, include_a=False, round_to=-1):
        hcl = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LCHuvColor,
            target_illuminant="d65"
        ).get_value_tuple()[::-1]
        hcl = np.array(hcl)
        hcl[0] *= max_h / 360
        obj = super().__new__(
            cls,
            hcl,
            rgba[-1] / 255 * max_a,
            rgba,
            include_a=include_a,
            round_to=round_to
        )
        obj.h, obj.c, obj.l = obj[:3]
        obj.max_h = max_h
        obj.max_a = max_a
        obj._format_params += ["max_h", "max_a"]

        return obj


# TODO doc
class HCLab(ColorPolarBase):
    def __new__(cls, h, c, l, a=None, max_h=360, max_a=1, include_a=False, round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not 0 <= l <= 100:
            raise ValueError("'l' must be greater than 0 and smaller than 100")

        rgb = convert_color(
            LCHabColor(l, c, h / max_h * 360 % 360, illuminant="d65"),
            sRGBColor
        )
        rgba = (rgb.clamped_rgb_r * 255,
                rgb.clamped_rgb_g * 255,
                rgb.clamped_rgb_b * 255,
                a / max_a * 255)
        obj = super().__new__(cls,
                              (h, c, l),
                              a,
                              rgba,
                              include_a=include_a,
                              round_to=round_to)
        obj.h, obj.c, obj.l = obj[:3]
        obj.max_h = max_h
        obj.max_a = max_a
        obj._format_params += ["max_h", "max_a"]

        return obj

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_a=1, include_a=False, round_to=-1):
        hcl = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LCHabColor,
            target_illuminant="d65"
        ).get_value_tuple()[::-1]
        hcl = np.array(hcl)
        hcl[0] *= max_h / 360
        obj = super().__new__(
            cls,
            hcl,
            rgba[-1] / 255 * max_a,
            rgba,
            include_a=include_a,
            round_to=round_to
        )
        obj.h, obj.c, obj.l = obj[:3]
        obj.max_h = max_h
        obj.max_a = max_a
        obj._format_params += ["max_h", "max_a"]

        return obj


default_tail = object()


def _warn_tail():
    warnings.warn("the default value for the 'tail_a' argument will be changed to 'True' "
                  "in the next release. Pass the argument explicitly with 'Hex(string, tail_a=False)' instead.",
                  FutureWarning,
                  stacklevel=3)


class Hex(ColorBase, str):
    """Represents a color in the RGB color space [#]_ as a hexadecimal string.

    Is mostly used for representing colors in web applications [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/SRGB.
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/Web_colors

    Args:
        hex_str: Hexadecimal string from which the :class:`Hex` instance will be built.
            The format can be a string of 6 digits, 8 digits (with an alpha specifier in the beginning or the end),
            or 3 digits, optionally including a '#' character.
        uppercase: Whether the color will be represented in uppercase or lowercase.
        include_a: Whether to include the opacity parameter `a` in the constructed string.
            Setting it to ``True`` may result in an object such as :code:`Hex('#ffffff00')`
            instead of :code:`Hex('#ffff00')`, for exemple.
        tail_a: Whether the alpha component is present in the tail or head of the hex string. Used
            only if `hex_str` includes an alpha component or `include_a` is ``True``.

    Examples:
        >>> Hex("#ff0000")
        Hex('#ff0000')

        >>> Hex("#FF0000", include_hash=False)
        Hex('ff0000')

        >>> Hex("ff0000", include_a=True, tail_a=True)
        Hex('#ff0000ff')
    """

    def __new__(cls,
                hex_str: str,
                uppercase=False,
                include_hash=True,
                include_a=False,
                tail_a=default_tail):
        if tail_a is default_tail:
            tail_a = False
            if include_a or len(hex_str) >= 8:
                _warn_tail()

        hex_str = hex_str.lstrip("#")
        if len(hex_str) not in (3, 6, 8):
            raise ValueError("'hex_str' length must be 3, 6 or 8 (excluding the optional '#')")
        if len(hex_str) == 3:
            hex_str = "".join(i + j for i, j in zip(hex_str, hex_str))
        if len(hex_str) < 8:
            i = 0
            a = 255
        elif tail_a:
            i = 0
            a = int(hex_str[-2:], 16)
        else:
            i = 2
            a = int(hex_str[:2], 16)
        rgb = (int(hex_str[i:i + 2], 16),
               int(hex_str[i + 2:i + 4], 16),
               int(hex_str[i + 4:i + 6], 16))
        # Rather than modifying the stored string to suit the format specifications we just
        # delegate that to the _from_rgba method
        return cls._from_rgba(rgb + (a,),
                              uppercase=uppercase,
                              include_hash=include_hash,
                              include_a=include_a,
                              tail_a=tail_a)

    @classmethod
    def _from_rgba(cls, rgba, uppercase=False, include_hash=True, include_a=False, tail_a=default_tail):
        if tail_a is default_tail:
            tail_a = False
            if include_a:
                _warn_tail()

        rgba = tuple(rgba)
        hex_str = '%02x%02x%02x' % rgba[:3]

        if include_a:
            a = '%02x' % rgba[-1]
            if not tail_a:
                hex_str = a + hex_str
            else:
                hex_str += a
        if uppercase:
            hex_str = hex_str.upper()
        if include_hash:
            hex_str = '#' + hex_str

        obj = str.__new__(cls, hex_str)
        obj.uppercase = uppercase
        obj.include_hash = include_hash
        obj.include_a = include_a
        obj.tail_a = tail_a
        obj._rgba = np.rint(rgba).astype(int)
        obj._format_params = ["uppercase", "include_hash", "include_a", "tail_a"]
        return obj

    # It would be dangerous to change str conversion as the target framework could call it
    # expecting #ff0000 and get Hex('#ff0000')
    def __str__(self):
        return str.__str__(self)

    def __repr__(self):
        if colorir.config.REPR_STYLE == "traditional":
            return f"{self.__class__.__name__}({str.__repr__(self)})"
        if colorir.config.REPR_STYLE == "inherit":
            return str(self)
        return colorir.utils.swatch(self, file=None)

    def __hash__(self):
        return ColorBase.__hash__(self)

    def __eq__(self, other):
        colorbase_eq = ColorBase.__eq__(self, other)
        # If other is ColorBase than we trust the result of eq
        if isinstance(other, ColorBase):
            return colorbase_eq
        # Otherwise we also try str.__eq__
        return any([colorbase_eq is True, str.__eq__(self, other) is True])


# Aliases
HexRGB = Hex
sRGB = RGB

ColorLike = Union[ColorBase, str, tuple]
"""Type constant that describes common representations of colors in python."""
