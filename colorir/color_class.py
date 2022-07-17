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

References:
    .. [#] Wikipedia at https://en.wikipedia.org/wiki/Color_model.
"""
import abc
# TODO get rid of colorsys
import colorsys

import numpy as np
from colormath.color_objects import LabColor, LuvColor, LCHuvColor, sRGBColor, LCHabColor
from colormath.color_conversions import convert_color

import colorir


class ColorBase(metaclass=abc.ABCMeta):
    """Base class from which all color classes inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """

    # Factory method to be called when reading the palette files or reconstructing colors
    @classmethod
    @abc.abstractmethod
    def _from_rgba(cls, rgba, **kwargs):
        pass

    # Must be called by constructors
    def _add_attrs(self, rgba, **format_):
        self._rgba = tuple(round(spec) for spec in rgba)
        self._format_params = list(format_)
        for param, value in format_.items():
            setattr(self, param, value)

    def __eq__(self, other):
        return self._rgba == other._rgba if isinstance(other, ColorBase) else False

    def __hash__(self):
        return hash(self._rgba)

    def get_format(self) -> "colorir.color_format.ColorFormat":
        """Returns a :class:`~colorir.color_format.ColorFormat` representing the format of this
        color object."""
        format_ = {param: getattr(self, param) for param in self._format_params}
        return colorir.color_format.ColorFormat(self.__class__, **format_)

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


class ColorTupleBase(ColorBase, tuple, metaclass=abc.ABCMeta):
    """Base class from which all color classes that are represented by tuples inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """

    @abc.abstractmethod
    def __new__(cls, iterable, rgba, include_a, round_to, **format_):
        if not include_a:
            iterable = iterable[:-1]
        if round_to == 0:
            iterable = (round(val) for val in iterable)
        elif round_to > 0:
            iterable = (round(val, round_to) for val in iterable)
        obj = tuple.__new__(cls, iterable)
        format_["include_a"] = include_a
        format_["round_to"] = round_to
        obj._add_attrs(rgba, **format_)
        return obj

    def __repr__(self):
        return f"{self.__class__.__name__}{tuple.__repr__(self)}"

    # It would be very dangerous to change str conversion as the target framework could call it
    # expecting (255, 0, 0) and get sRGB(255, 0, 0)
    def __str__(self):
        return tuple.__repr__(self)

    def __eq__(self, other):
        if isinstance(other, ColorBase):
            return ColorBase.__eq__(self, other)
        return tuple.__eq__(self, other)

    def __hash__(self):
        return ColorBase.__hash__(self)


# TODO finish
class PolarColorBase(ColorTupleBase, metaclass=abc.ABCMeta):
    """Base class from which all color classes that are represented by tuples and have at least
    one polar component (which is usually hue) inherit.

    Notes:
        This class is abstract and should not be instantiated.
    """

    def __new__(cls, polar_index, polar_max, iterable, *args, **kwargs):
        iterable = list(iterable)
        polar_unbound = iterable[polar_index]
        iterable[polar_index] = iterable[polar_index] % polar_max

        obj = super().__new__(iterable, *args, **kwargs)
        obj._polar_unbound = polar_unbound
        obj._polar_index = polar_index
        obj._polar_max = polar_max
        return obj

    def get_unbound(self):
        iterable = list(self)
        iterable[self._polar_index] = self._polar_unbound
        return super().__new__(
            iter
        )


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
        max_rgb: What is the maximum value for the `r`, `g` and `b` components. Some common
            values for this parameter would be 255 or 1.
        max_a : What is the maximum value for the `a` component. Some common
            values for this parameter would be 100 or 1.
        include_a: Whether to include the opacity parameter `a` in the constructed tuple.
            Setting it to ``True`` may result in an object such as :code:`sRGB(255, 255, 0,
            255)` instead of :code:`sRGB(255, 255, 0)`, for exemple.
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type `int`. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls,
                r: float,
                g: float,
                b: float,
                a: float = None,
                max_rgb=255,
                max_a=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not all(0 <= spec <= max_rgb for spec in (r, g, b)):
            raise ValueError("'r', 'g' and 'b' must be greater than 0 and smaller than 'max_rgb'")

        return super().__new__(
            cls,
            (r, g, b, a),
            (r / max_rgb * 255, g / max_rgb * 255, b / max_rgb * 255, a / max_a * 255),
            include_a=include_a,
            round_to=round_to,
            max_rgb=max_rgb,
            max_a=max_a
        )

    @classmethod
    def _from_rgba(cls,
                   rgba,
                   max_rgb=255,
                   max_a=1,
                   include_a=False,
                   round_to=-1):
        rgba_ = [spec / 255 * max_rgb for spec in rgba[:3]] + [rgba[-1] / 255 * max_a]
        return super().__new__(
            cls,
            rgba_,
            rgba,
            include_a=include_a,
            round_to=round_to,
            max_rgb=max_rgb,
            max_a=max_a
        )


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

        rgba = colorsys.hls_to_rgb(h / max_h, l / max_sla, s / max_sla) + (a / max_sla,)
        return super().__new__(cls,
                               (h, s, l, a),
                               [spec * 255 for spec in rgba],
                               include_a=include_a,
                               round_to=round_to,
                               max_h=max_h,
                               max_sla=max_sla)

    @classmethod
    def _from_rgba(cls,
                   rgba,
                   max_h=360,
                   max_sla=1,
                   include_a=False,
                   round_to=-1):
        hls = colorsys.rgb_to_hls(*[spec / 255 for spec in rgba[:-1]])
        hsla = (hls[0] * max_h, hls[2] * max_sla, hls[1] * max_sla, rgba[-1] / 255 * max_sla)

        return super().__new__(cls,
                               hsla,
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_h=max_h,
                               max_sla=max_sla)


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
        round_to: Rounds the value of each color component to this many decimal places. Setting
            this parameter to 0 ensures that the components will be of type `int`. -1
            means that the components won't be rounded at all.
    """

    def __new__(cls, h: float, s: float, v: float, a: float = None, max_h=360, max_sva=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_sva
        if h > max_h:
            raise ValueError(
                "'h' parameter of HSL can't be larger than the defined 'max_h' parameter'"
            )
        if not all(0 <= spec <= max_sva for spec in (s, v, a)):
            raise ValueError("'s', 'v' and 'a' must be greater than 0 and smaller than 'max_sva'")

        rgba = colorsys.hsv_to_rgb(h / max_h, s / max_sva, v / max_sva) + (a / max_sva,)
        rgba = [spec * 255 for spec in rgba]
        return super().__new__(cls,
                               (h, s, v, a),
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_h=max_h,
                               max_sva=max_sva)

    @classmethod
    def _from_rgba(cls,
                   rgba,
                   max_h=360,
                   max_sva=1,
                   include_a=False,
                   round_to=-1):
        hsv = colorsys.rgb_to_hsv(*[spec / 255 for spec in rgba[:-1]])
        hsva = (hsv[0] * max_h, hsv[1] * max_sva, hsv[2] * max_sva, rgba[-1] / 255 * max_sva)

        return super().__new__(cls,
                               hsva,
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_h=max_h,
                               max_sva=max_sva)


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

    def __new__(cls,
                c: float,
                m: float,
                y: float,
                k: float,
                a: float = None,
                max_cmyka=1,
                include_a=False,
                round_to=-1):
        if a is None:
            a = max_cmyka
        if not all(0 <= spec <= max_cmyka for spec in (c, m, y, k, a)):
            raise ValueError("'c', 'm', 'y', 'k', and 'a' must be greater than 0 and smaller than "
                             "'max_cmyka'")

        r = (1 - c / max_cmyka) * (1 - k / max_cmyka) * 255
        g = (1 - m / max_cmyka) * (1 - k / max_cmyka) * 255
        b = (1 - y / max_cmyka) * (1 - k / max_cmyka) * 255

        return super().__new__(cls,
                               (c, m, y, k, a),
                               (r, g, b, a / max_cmyka * 255),
                               include_a=include_a,
                               round_to=round_to,
                               max_cmyka=max_cmyka)

    @classmethod
    def _from_rgba(cls,
                   rgba,
                   max_cmyka=1,
                   include_a=False,
                   round_to=-1):
        if sum(rgba[:-1]) == 0:
            cmyka = (0.0, 0.0, 0.0, max_cmyka, rgba[-1] / 255 * max_cmyka)
        else:
            c = 1 - rgba[0] / 255
            m = 1 - rgba[1] / 255
            y = 1 - rgba[2] / 255

            k = min(c, m, y)
            c = (c - k) / (1 - k)
            m = (m - k) / (1 - k)
            y = (y - k) / (1 - k)
            cmyka = [spec * max_cmyka for spec in (c, m, y, k, rgba[-1] / 255)]

        return super().__new__(cls,
                               cmyka,
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_cmyka=max_cmyka)


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

        return super().__new__(
            cls,
            (c, m, y, a),
            (
                255 - c / max_cmya * 255,
                255 - m / max_cmya * 255,
                255 - y / max_cmya * 255,
                a / max_cmya * 255
            ),
            include_a=include_a,
            round_to=round_to,
            max_cmya=max_cmya
        )

    @classmethod
    def _from_rgba(cls,
                   rgba,
                   max_cmya=1,
                   include_a=False,
                   round_to=-1):
        cmya = [spec / 255 * max_cmya for spec in
                (255 - rgba[0], 255 - rgba[1], 255 - rgba[2], rgba[-1])]
        return super().__new__(cls,
                               cmya,
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_cmya=max_cmya)


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
        return super().__new__(cls,
                               (l, u, v, a),
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_a=max_a)

    @classmethod
    def _from_rgba(cls, rgba, max_a=1, include_a=False, round_to=-1):
        luva = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LuvColor,
            target_illuminant="d65"
        ).get_value_tuple() + (rgba[-1] / 255 * max_a,)
        return super().__new__(cls,
                               luva,
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_a=max_a)


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
        return super().__new__(cls,
                               (l, a_, b, a),
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_a=max_a)

    @classmethod
    def _from_rgba(cls, rgba, max_a=1, include_a=False, round_to=-1):
        laba = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LabColor,
            target_illuminant="d65"
        ).get_value_tuple() + (rgba[-1] / 255 * max_a,)
        return super().__new__(cls,
                               laba,
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_a=max_a)


# TODO doc
class HCLuv(ColorTupleBase):
    def __new__(cls, h, c, l, a=None, max_h=360, max_a=1, include_a=False, round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not 0 <= l <= 100:
            raise ValueError("'l' must be greater than 0 and smaller than 100")

        rgb = convert_color(
            LCHuvColor(l, c, h, illuminant="d65"),
            sRGBColor
        )
        rgba = (rgb.clamped_rgb_r * 255,
                rgb.clamped_rgb_g * 255,
                rgb.clamped_rgb_b * 255,
                a / max_a * 255)
        return super().__new__(cls,
                               (h, c, l, a),
                               rgba,
                               include_a=include_a,
                               round_to=round_to,
                               max_h=max_h,
                               max_a=max_a)

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_a=1, include_a=False, round_to=-1):
        lch = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LCHuvColor,
            target_illuminant="d65"
        ).get_value_tuple()
        return super().__new__(
            cls,
            (lch[2], lch[1], lch[0], rgba[-1] / 255 * max_a),
            rgba,
            include_a=include_a,
            round_to=round_to,
            max_h=max_h,
            max_a=max_a
        )


# TODO doc
class HCLab(ColorTupleBase):
    def __new__(cls, h, c, l, a=None, max_h=360, max_a=1, include_a=False, round_to=-1):
        if a is None:
            a = max_a
        elif not 0 <= a <= max_a:
            raise ValueError("'a' must be greater than 0 and smaller than 'max_a'")
        if not 0 <= l <= 100:
            raise ValueError("'l' must be greater than 0 and smaller than 100")

        rgb = convert_color(
            LCHabColor(l, c, h, illuminant="d65"),
            sRGBColor
        )
        rgba = (rgb.clamped_rgb_r * 255,
                rgb.clamped_rgb_g * 255,
                rgb.clamped_rgb_b * 255,
                a / max_a * 255)
        return super().__new__(
            cls,
            (h, c, l, a),
            rgba,
            include_a=include_a,
            round_to=round_to,
            max_h=max_h,
            max_a=max_a
        )

    @classmethod
    def _from_rgba(cls, rgba, max_h=360, max_a=1, include_a=False, round_to=-1):
        lch = convert_color(
            sRGBColor(*rgba[:3], is_upscaled=True),
            LCHabColor,
            target_illuminant="d65"
        ).get_value_tuple()
        return super().__new__(
            cls,
            (lch[2], lch[1], lch[0], rgba[-1] / 255 * max_a),
            rgba,
            include_a=include_a,
            round_to=round_to,
            max_h=max_h,
            max_a=max_a
        )


class Hex(ColorBase, str):
    """Represents a color in the RGB color space [#]_ as a hexadecimal string.

    Is mostly used for representing colors in web applications [#]_.

    References:
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/SRGB.
        .. [#] Wikipedia at https://en.wikipedia.org/wiki/Web_colors

    Args:
        hex_str: Hexadecimal string from which the :class:`Hex` instance will be built.
            May or may not include a "#" character in its beginning.
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
                tail_a=False):
        hex_str = hex_str.lstrip("#")
        if not 6 <= len(hex_str) <= 9:
            raise ValueError("'hex_str' length must be between 6 and 9 (inclusive)")
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
    def _from_rgba(cls, rgba, uppercase=False, include_hash=True, include_a=False, tail_a=False):
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
        obj._add_attrs(rgba,
                       uppercase=uppercase,
                       include_hash=include_hash,
                       include_a=include_a,
                       tail_a=tail_a)
        return obj

    def __repr__(self):
        return f"{self.__class__.__name__}({str.__repr__(self)})"

    # It would be very dangerous to change str conversion as the target framework could call it
    # expecting #ff0000 and get Hex('#ff0000')
    def __str__(self):
        return str.__str__(self)

    def __eq__(self, other):
        if isinstance(other, ColorBase):
            return ColorBase.__eq__(self, other)
        return str.__eq__(self, other)

    def __hash__(self):
        return ColorBase.__hash__(self)


# Alias
HexRGB = Hex
