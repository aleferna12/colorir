"""Palettes to hold collections of colors that can be shared between projects.

The :class:`Palette` class provides an easy way to manage your favorite colors in different
projects. In this context, a palette should be understood as any collection of colors that
can be grouped due to a common feature, not only colors that necessarily "look good" together.

Every color in a :class:`Palette` has a name associated with it. If unnamed colors are better fit
to your particular use case, you may want to use a :class:`StackPalette` instead.

Examples:
    Create a palette:

    >>> palette = Palette(red="#ff0000")

    Add colors:

    >>> palette.add("blue", "#0000ff")

    Get the value of colors:

    >>> palette.red
    Hex('#ff0000')

    Manipulate colors in the palette (see the :mod:`~colorir.color_class` module for details on how this works):

    >>> palette = palette * HSL(1, 0.5, 1)  # Desaturate the whole palette 50%
    >>> palette
    Palette(red=#bf4040, blue=#4040bf)

    Remove colors:

    >>> palette.remove("red")
    >>> "red" in palette.color_names
    False

    Save a palette:

    >>> palette.save(name="single_blue")

    Load saved palettes:

    >>> palette = Palette.load("single_blue")

    Concatenate two palettes together:

    >>> Palette(red="f00", blue="00f") & Palette(green="0f0", yellow="0ff")
    Palette(red=#ff0000, blue=#0000ff, green=#00ff00, yellow=#00ffff)
"""
import abc
import json
import operator
import os
import numpy as np
from pathlib import Path
from typing import Union, List, Dict, Iterable, Type
from warnings import warn
from . import config
from . import utils
from .color_class import ColorBase, RGB, HSL, HSV, ColorLike
from .color_format import ColorFormat
from .gradient import Grad

_throw_exception = object()
_builtin_palettes_dir = Path(__file__).resolve().parent / "builtin_palettes"

__all__ = [
    "Palette",
    "StackPalette",
    "find_palettes",
    "delete_palette"
]


class PaletteBase(metaclass=abc.ABCMeta):
    def __init__(self, color_format=None):
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self._color_format = color_format

    @property
    @abc.abstractmethod
    def colors(self):
        """A list of all color values currently stored in the palette."""
        pass

    @property
    def color_format(self) -> ColorFormat:
        """Color format specifying how the colors of this palette are stored."""
        return self._color_format

    @color_format.setter
    @abc.abstractmethod
    def color_format(self, color_format):
        self._color_format = color_format

    @abc.abstractmethod
    def _for_each_color(self, func, obj=None, *args, **kwargs):
        pass

    def __len__(self):
        """Returns the number of colors in the palette."""
        return len(self.colors)

    def __contains__(self, item):
        """Returns ```True`` if the color is found in the palette and ``False`` otherwise."""
        return self.color_format.format(item) in self.colors

    def __iter__(self):
        """Iterates over the colors in the palette."""
        return iter(self.colors)

    def __invert__(self):
        """Returns a copy of the palette but with its colors inverted in RGB space.

        Examples:

            >>> palette = Palette(red="ff0000", yellow="ffff00")
            >>> ~palette
            Palette(red=#00ffff, yellow=#0000ff)
        """
        return self._for_each_color(operator.invert)

    def __add__(self, obj):
        return self._for_each_color(operator.add, obj=obj)

    def __sub__(self, obj):
        return self._for_each_color(operator.sub, obj=obj)

    def __mul__(self, obj):
        return self._for_each_color(operator.mul, obj=obj)

    def __truediv__(self, obj):
        return self._for_each_color(operator.truediv, obj=obj)

    def __mod__(self, obj):
        return self._for_each_color(operator.mod, obj=obj)

    def blend(self, obj, perc=0.5, grad_class: Type[Grad] = Grad):
        return self._for_each_color(utils.blend, obj=obj, perc=perc, grad_class=grad_class)


class Palette(PaletteBase):
    """Class that holds colors values associated with names.

    Examples:
        >>> palette = Palette(red="#ff0000") # Uses default color format
        >>> palette.red
        Hex('#ff0000')

        For more examples see the documentation of the :mod:`~colorir.palette` module.

    Args:
        name: Name of the palette which will be used to save it with :meth:`Palette.save()`.
        color_format: Color format specifying how the colors of this :class:`Palette` should be
            stored. Defaults to the value specified in
            :const:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        colors: Colors that will be stored in this palette.
    """
    def __init__(self,
                 colors: Union["Palette", Dict[str, ColorLike]] = None,
                 color_format: ColorFormat = None,
                 **color_kwargs: ColorLike):
        super().__init__(color_format)
        if colors is None:
            colors = color_kwargs
        elif color_kwargs:
            raise ValueError("colors can be passed either through the 'colors' parameter or through kwargs "
                             "but not both")
        if isinstance(colors, Palette):
            colors = colors.to_dict()

        self._color_dict = {}
        for k, v in colors.items():
            self.add(k, v)

    @property
    def colors(self) -> List[ColorBase]:
        return list(self._color_dict.values())

    @property
    def color_names(self) -> List[str]:
        """A list of all color names currently stored in the palette."""
        return list(self._color_dict.keys())

    # color_format could be used to build a color on every Palette.color call, but that is
    # computationally intensive. That's why the colors are stored as ready objects and are
    # re-created if needed
    @PaletteBase.color_format.setter
    def color_format(self, color_format):
        PaletteBase.color_format.fset(self, color_format)

        self._color_dict = {c_name: color_format._from_rgba(c_value._rgba)
                            for c_name, c_value in self._color_dict.items()}

    @classmethod
    def load(cls,
             palettes: Union[str, List[str]] = None,
             palettes_dir: str = None,
             search_builtins=True,
             search_cwd=True,
             color_format: ColorFormat = None,
             warnings=True) -> "Palette":
        """Factory method that loads previously created palettes into a :class:`Palette` instance.

        A palette is a file containing json-formatted information about colors that ends with the
        '.palette' extension. You should not create such files manually but rather through the
        :meth:`Palette.save()` method.

        If multiple palettes define different color values under the same name, only the first one
        will be kept. You can define the order in which the palettes are loaded by ordering them in
        the `palettes` parameter. By default this occurrence logs a warning, but this behaviour can
        be changed through the `warnings` parameter.

        Args:
            palettes: List of palettes located in the location represented by `palettes_dir` that
                should be loaded by this :class:`Palette` instance. Additionally may include
                built-in palettes such as 'css' if `search_builtins` is set to ``True``. By
                default, loads all palettes found in the specified directory.
            palettes_dir: The directory from which the palettes specified in the `palettes`
                parameter will be loaded. Defaults to the value specified in
                :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
            search_builtins: Whether `palettes` may also include built-in palettes such as 'css'
                or 'basic'.
            search_cwd: Whether `palettes` may also include palettes located in the current
                working directory.
            color_format: Color format specifying how the colors of this :class:`Palette` should be
                stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
            warnings: Whether to emit a warning if two colors with the same name but different
                color values were found in the `palettes`.

        Examples:
            Loads the default CSS palette:

            >>> css_palette = Palette.load('css')

            Loads both the basic and fluorescent palettes into a new palette:

            >>> colorful = Palette.load(['basic', 'fluorescent'])
        """
        if isinstance(palettes, str):
            palettes = [palettes]
        palettes_dir = _resolve_palettes_dirs(palettes_dir, search_builtins=search_builtins, search_cwd=search_cwd)

        found_palettes = {}
        for path in palettes_dir:
            path = Path(path)
            palette_files = path.glob("*.palette")
            for palette_file in palette_files:
                palette_name = palette_file.name.replace(".palette", '')
                found_palettes[palette_name] = json.loads(palette_file.read_text())

        palette_obj = cls(color_format=color_format)
        if palettes is None:
            palettes = list(found_palettes)
        # Reiterates based on user input order
        for palette_name in palettes:
            for c_name, c_rgba in found_palettes[palette_name].items():
                c_rgba = np.array([int(c_rgba[3:5], 16),
                                   int(c_rgba[5:7], 16),
                                   int(c_rgba[7:9], 16),
                                   int(c_rgba[1:3], 16)])
                new_color = palette_obj.color_format._from_rgba(c_rgba)
                old_color = palette_obj.get_color(c_name, None)
                if old_color is None:
                    palette_obj.add(c_name, new_color)
                elif new_color != old_color and warnings:
                    warn(
                        f"a discrepancy was detected when adding color '{c_name}' "
                        f"({new_color}) from palette named '{palette_name}': '{c_name}' is "
                        f"already present with a different value ({old_color})")
        return palette_obj

    def __getattr__(self, item):
        return self.get_color(item)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_color(item)
        elif isinstance(item, list):
            pal = Palette(color_format=self.color_format)
            pal._color_dict = {c_name: self._color_dict[c_name] for c_name in item}
            return pal
        raise TypeError(f"'Palette' indices must be 'str' or 'list', not '{type(item)}'")

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if key in self._color_dict:
            self.update(key, value)
            return
        self.add(key, value)

    def __delitem__(self, key):
        self.remove(key)

    def __dir__(self) -> List[str]:
        return dir(Palette) + list(self.__dict__) + list(self._color_dict.keys())

    def __str__(self):
        colors_str = ', '.join(
            f"{c_name}={str(c_val)}" for c_name, c_val in self._color_dict.items()
        )
        return f"{self.__class__.__name__}({colors_str})"

    def __repr__(self):
        if config.REPR_STYLE in ["traditional", "inherit"]:
            return str(self)
        return utils.swatch(self, file=None)

    def __eq__(self, other):
        return self._color_dict.items() == other._color_dict.items()

    def __and__(self, other):
        """Join two palettes sequentially.

        Repeated color names wil raise an exception.

        Examples:

            >>> Palette(red="ff0000") & Palette(blue="0000ff")
            Palette(red=#ff0000, blue=#0000ff)
        """
        pal = Palette(self, color_format=self.color_format)
        for c_name, c_val in other.to_dict().items():
            pal.add(c_name, c_val)
        return pal

    def get_color(self,
                  name: Union[str, List[str]],
                  fallback=_throw_exception) -> Union[ColorBase, List[ColorBase]]:
        """Retrieves one or more colors from the :class:`Palette` given their names.

        Args:
            name: One or more names of colors in this palette.
            fallback: What to return instead of colors that are not found in the palette. By
                default, throws an exception.

        Examples:
            >>> palette = Palette(red="#ff0000", blue="#0000ff")
            >>> palette.get_color("red")
            Hex('#ff0000')
            >>> palette.get_color(["red", "blue"])
            [Hex('#ff0000'), Hex('#0000ff')]

        Returns:
            A single :class:`~colorir.color_class.ColorBase` if `name` is a string or a list of
            :class:`~colorir.color_class.ColorBase` if `name` is a list of strings.
        """
        if fallback is _throw_exception:
            if isinstance(name, str):
                return self._color_dict[name]
            return [self._color_dict[name_i] for name_i in name]
        if isinstance(name, str):
            return self._color_dict.get(name, fallback)
        return [self._color_dict.get(name_i, fallback) for name_i in name]

    def get_names(self, color: ColorLike) -> list:
        """Finds all names of the provided color in this :class:`Palette`.

        Compares the provided `color` to every color the :class:`Palette` contains and returns the
        names of the colors that are equivalent to the one provided.

        Args:
            color: The value of the color to be searched for. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the color you want to search for.

        Examples:
            >>> palette = Palette(red="#ff0000")
            >>> palette.get_names(HSL(0, 1, 0.5))
            ['red']
        """
        color = self.color_format.format(color)
        color_list = []
        for name in self.color_names:
            if self.get_color(name) == color:
                color_list.append(name)
        return color_list

    def add(self, name: str, color: ColorLike):
        """Adds a color to the palette.

        Two colors with the same name but different values are invalid and can not coexist in a
        same :class:`Palette`. You should therefore avoid reusing names of already existing
        colors.

        Args:
            name: Name to be assigned to the new color.
            color: The value of the color to be created. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the color you want to add.

        Examples:
            Adding a new blue color to the palette:

            >>> palette = Palette()
            >>> palette.add("bestblue", "4287f5")
            >>> palette.bestblue
            Hex('#4287f5')
        """
        # Test to detect invalid color names
        if name in dir(self):
            raise ValueError(f"'{name}' is a reserved attribute name of Palette or is already "
                             "in use by another color. 'Palette.update()' might help in that case")
        color = self.color_format.format(color)
        self._color_dict[name] = color

    def update(self, name: str, color: ColorLike):
        """Updates a color to a new value.

        Args:
            name: Name of the color to be updated.
            color: The value of the color to be updated. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the format of the color you want to update.

        Examples:
            Create a slightly dark shade of red:
            
            >>> palette = Palette(myred="dd0000")
            >>> palette.myred
            Hex('#dd0000')
            
            Change it to be even a bit darker:
            
            >>> palette.update("myred", "800000")
            >>> palette.myred
            Hex('#800000')
        """
        if name in self._color_dict:
            self._color_dict[name] = self.color_format.format(color)
        else:
            raise ValueError(f"provided 'name' parameter is not a color loaded in this 'Palette'")

    def remove(self, name):
        """Removes a color from the palette.

        Args:
            name: Name of the color to be removed.

        Examples:
            >>> palette = Palette(red=RGB(1, 0, 0))
            >>> palette.remove("red")
            >>> "red" in palette.color_names
            False
        """
        if name in self._color_dict:
            del self._color_dict[name]
        else:
            raise ValueError(f"provided 'name' parameter is not a color stored in this 'Palette'")

    def save(self, name: str, palettes_dir: str = None):
        """Saves the changes made to this :class:`Palette` instance.

        If this method is not called after modifications made by :meth:`Palette.add()`,
        :meth:`Palette.update()` and :meth:`Palette.remove()`, the modifications on the palette
        will not be permanent.

        Examples:
            Loads both the basic and fluorescent palettes into a new palette called 'colorful':

            >>> colorful = Palette.load(['basic', 'fluorescent'])

            Save the palette to the default palette directory:

            >>> colorful.save(name='colorful')
        """
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        with open(Path(palettes_dir) / (name + ".palette"), "w") as file:
            formatted_colors = {}
            for c_name, c_val in self._color_dict.items():
                c_rgba = c_val.hex(include_a=True, tail_a=False)
                formatted_colors[c_name] = c_rgba
            json.dump(formatted_colors, file, indent=4)

    def to_stackpalette(self) -> "StackPalette":
        """Converts this palette into a :class:`StackPalette`."""
        return StackPalette(colors=self._color_dict.values(), color_format=self.color_format)

    def to_dict(self):
        """Converts this palette into a python `dict`."""
        return dict(self._color_dict)

    def grayscale(self):
        """Returns a copy of this object but with its colors in grayscale.

        Examples:

            >>> palette = Palette(red="ff0000", yellow="ffff00")
            >>> palette.grayscale()
            Palette(red=#7f7f7f, yellow=#f7f7f7)
        """
        pal = Palette(color_format=self.color_format)
        for c_name, c_val in self.to_dict().items():
            pal.add(c_name, c_val.grayscale())
        return pal

    def most_similar(self, color: ColorLike, n=1, method="CIE76"):
        """Finds the `n` most similar colors to `color` in this palette.

        Args:
            color: The value of the color of reference.
            n: How many colors to be retrieved from most similar to least. -1 means all colors will be returned.
            method: Method for calculating color distance. See the documentation of the function `color_dist`.

        Examples:
            >>> palette = Palette(red="#ff0000", blue="#0000ff")
            >>> palette.most_similar("#880000")
            ('red', Hex('#ff0000'))

        Returns:
            A tuple (color_name, color) if `n` == 1 or a `Palette` if `n` != 1.
        """
        closest = sorted(zip(self.color_names, self.colors),
                         key=lambda tup: utils.color_dist(color, tup[1], method))
        if n == 1:
            return closest[0]
        if n < 1:
            n = len(self)
        pal = Palette(color_format=self.color_format)
        pal._color_dict = dict(closest[:n])
        return pal

    def _for_each_color(self, func, obj=None, *args, **kwargs):
        pal = Palette(color_format=self.color_format)
        if obj is None:
            for colork, colorv in self._color_dict.items():
                pal.add(colork, func(colorv, *args, **kwargs))
            return pal
        if isinstance(obj, dict):
            for colork, colorv in self._color_dict.items():
                color2 = obj.get(colork, None)
                if color2 is None:
                    pal.add(colork, colorv)
                else:
                    pal.add(colork, func(colorv, color2, *args, **kwargs))
            return pal
        # Assume color-like
        for colork, colorv in self._color_dict.items():
            pal.add(colork, func(colorv, obj, *args, **kwargs))
        return pal


class StackPalette(PaletteBase):
    """Class that handles anonymous indexed colors stored as a stack.

    This class may be used as a replacement for :class:`Palette` when the name of the colors is
    irrelevant.

    Examples:
        >>> spalette = StackPalette(["ff0000", "00ff00", "0000ff"])
        >>> spalette[0]
        Hex('#ff0000')

    Args:
        color_format: Color format specifying how the colors of this :class:`StackPalette` should
            be stored. Defaults to the value specified in
            :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        colors: Colors that will be stored in this palette.
    """

    def __init__(self,
                 colors: Iterable[ColorLike] = None,
                 color_format: ColorFormat = None):
        super().__init__(color_format=color_format)
        if colors is None:
            colors = []

        self._color_stack = []
        for color in colors:
            self.add(color)

    @property
    def colors(self) -> List[ColorBase]:
        """colors: A list of all color values currently stored in the :class:`StackPalette`."""
        return list(self._color_stack)

    @PaletteBase.color_format.setter
    def color_format(self, color_format):
        PaletteBase.color_format.fset(self, color_format)
        self._color_stack = [color_format._from_rgba(color._rgba) for color in self._color_stack]

    @classmethod
    def load(cls,
             palettes: Union[str, List[str]] = None,
             palettes_dir: str = None,
             search_builtins=True,
             search_cwd=True,
             color_format: ColorFormat = None) -> "StackPalette":
        """Factory method that loads previously created stack palettes into a
        :class:`StackPalette` instance.

        A stack palette is a file containing json-formatted information about colors that ends
        with the '.spalette' extension. You should not create such files manually but rather
        through the :meth:`StackPalette.save()` method.

        Examples:
            Load a stack palette called "project_interface" from the default directory:

            >>> spalette = StackPalette.load("project_interface")  # doctest: +SKIP

        Args:
            palettes: List of stack palettes located in the location represented by `palettes_dir`
                that should be loaded by this :class:`StackPalette` instance. By default,
                loads all palettes found in the specified directory.
            palettes_dir: The directory from which the palettes specified in the `palettes`
                parameter will be loaded. Defaults to the value specified in
                :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
            search_builtins: Whether `palettes` may also include built-in palettes such as 'tab10'
                or 'dark2'.
            search_cwd: Whether `palettes` may also include palettes located in the current
                working directory.
            color_format: Color format specifying how the colors of this :class:`Palette` should be
                stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        """
        if isinstance(palettes, str):
            palettes = [palettes]
        palettes_dir = _resolve_palettes_dirs(palettes_dir, search_builtins=search_builtins, search_cwd=search_cwd)

        found_palettes = {}
        for path in palettes_dir:
            path = Path(path)
            palette_files = path.glob("*.spalette")
            for palette_file in palette_files:
                palette_name = palette_file.name.replace(".spalette", '')
                found_palettes[palette_name] = json.loads(palette_file.read_text())

        palette_obj = cls(color_format=color_format)
        if palettes is None:
            palettes = list(found_palettes)
        # Reiterates based on user input order
        for palette_name in palettes:
            for c_rgba in found_palettes[palette_name]:
                c_rgba = np.array([int(c_rgba[3:5], 16),
                                   int(c_rgba[5:7], 16),
                                   int(c_rgba[7:9], 16),
                                   int(c_rgba[1:3], 16)])
                new_color = palette_obj.color_format._from_rgba(c_rgba)
                palette_obj.add(new_color)
        return palette_obj

    # TODO enhance to allow different color systems and variance param (prob. 1.4.0)
    @classmethod
    def new_complementary(cls,
                          n: int,
                          color: ColorLike = None,
                          color_format: ColorFormat = None):
        """Creates a new palette with `n` complementary colors.

        Colors are considered complementary if they are interspaced in the additive from .colormath color
        wheel.

        Examples:
             Make a palette from red and its complementary color, cyan:

             >>> spalette = StackPalette.new_complementary(2, RGB(1, 0, 0))
             >>> spalette
             StackPalette([#ff0000, #00ffff])

             Make a tetradic palette of random colors:

             >>> spalette = StackPalette.new_complementary(4)

        Args:
            n: The number of colors in the new palette.
            color: A color from which the others will be generated against. By default, a color is
                randomly chosen.
            color_format: Color format specifying how the colors of this :class:`StackPalette`
                should be stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        """
        n_spalette = cls(color_format=color_format)
        if color is None:
            hsv = utils.random_color(color_format=ColorFormat(HSV, max_h=360))
        else:
            hsv = n_spalette.color_format.format(color).hsv(max_h=360)

        step = 360 / n
        for i in range(n):
            hue = (hsv[0] + i * step) % 360
            n_spalette.add(HSV(hue, hsv[1], hsv[2]))
        return n_spalette

    @classmethod
    def new_analogous(cls,
                      n: int,
                      sections=12,
                      start=0,
                      color: ColorLike = None,
                      color_format: ColorFormat = None):
        """Creates a new palette with `n` analogous colors.

        Colors are considered analogous if they are side-by-side in the additive from .colormath color wheel.

        Examples:
             Make a palette from red and its analogous color, orange:

             >>> spalette = StackPalette.new_analogous(2, start=1, color=RGB(1, 0, 0))
             >>> spalette
             StackPalette([#ff0000, #ff8000])

             Make a palette of four similar colors:

             >>> spalette = StackPalette.new_analogous(4, sections=24)

        Args:
            n: The number of colors in the new palette.
            sections: The number of sections in which the additive from .colormath color wheel will be divided
                before sampling colors. The bigger this number, the more similar the colors will
                be.
            start: Where the color described in the 'color' parameter will be placed with respect
                to the others. If '0', 'color' will be in the center of the generated palette, and
                colors will be sampled from both its sides in the from .colormath wheel. If '1', colors will
                be sampled clockwise from 'color'. If '-1', they will be sampled counter-clockwise.
            color: A color from which the others will be generated against. By default, a color is
                randomly chosen.
            color_format: Color format specifying how the colors of this :class:`StackPalette`
                should be stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        """
        if n > sections:
            raise ValueError("'n' parameter cannot be larger than 'sections' parameter")
        if start == 0:
            first = -int(n / 2)
            iterator = range(first, first + n)
        elif start == 1:
            iterator = range(n)
        elif start == -1:
            iterator = range(-n + 1, 1)
        else:
            raise ValueError("'starting_point' must be either 0, 1 or -1")

        n_spalette = cls(color_format=color_format)
        if color is None:
            hsv = utils.random_color(color_format=ColorFormat(HSV, max_h=360))
        else:
            hsv = n_spalette.color_format.format(color).hsv(max_h=360)

        step = 360 / sections
        for index, i in enumerate(iterator):
            hue = (hsv[0] + i * step) % 360
            n_spalette.add(HSV(hue, hsv[1], hsv[2]))
        return n_spalette

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._color_stack[item]
        if isinstance(item, list):
            pal = StackPalette(color_format=self.color_format)
            pal._color_stack = [self._color_stack[i] for i in item]
            return pal
        if isinstance(item, slice):
            indexes = list(range(*item.indices(len(self))))
            return self[indexes]
        raise TypeError(f"'StackPalette' indices must be 'int', 'list' or 'slice', not '{type(item)}'")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.update(key, value)
        elif isinstance(key, list):
            if len(key) != len(value):
                raise ValueError("length of indexes and provided values must match")
            for i, val in zip(key, value):
                self.update(i, val)
        elif isinstance(key, slice):
            indexes = list(range(*key.indices(len(self))))
            self[indexes] = value
        else:
            raise TypeError("index must be 'int', 'list' or 'slice'")

    def __str__(self):
        colors_str = ', '.join(str(c_val) for c_val in self._color_stack)
        return f"{self.__class__.__name__}([{colors_str}])"

    def __repr__(self):
        if config.REPR_STYLE in ["traditional", "inherit"]:
            return str(self)
        return utils.swatch(self, file=None)

    def __eq__(self, other):
        return self._color_stack == other._color_stack

    def __and__(self, other):
        """Join two palettes sequentially.

        Examples:

            >>> StackPalette(["ff0000"]) & StackPalette(["0000ff"])
            StackPalette([#ff0000, #0000ff])
        """
        c_list = self.colors + other.colors
        return StackPalette(c_list, color_format=self.color_format)

    def resize(self, n: int, repeat=False, grad_class=Grad, **kwargs):
        """Resizes the palette to be `n` elements long by interpolating or repeating colors.

        Args:
            repeat: If ``True``, repeats the colors intead of interpolating them to reach the length goal.
            grad_class: Which gradient class to use for interpolation.
            n: Number of elements in the final palette.
            kwargs: Key-word arguments passed down to the internal gradient object.

        Examples:

            >>> StackPalette(["000000", "ffffff"]).resize(3)
            StackPalette([#000000, #777777, #ffffff])
            >>> StackPalette(["000000", "ffffff"]).resize(3, repeat=True)
            StackPalette([#000000, #ffffff, #000000])

        Returns:
            A resized copy of this stack palette.
        """
        if repeat:
            color_indices = [i % len(self) for i in range(n)]
            return self[color_indices]
        colors = grad_class(colors=self.colors, **kwargs).n_colors(n)
        return StackPalette(colors=colors, color_format=self.color_format)

    def add(self, color: ColorLike, i=None):
        """Adds a color to the end of the stack palette.

        Args:
            color: The value of the color to be created. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the color you want to add.
            i: Index of the new color. It is added at the end of the palette by default.

        Examples:
            Adding a new blue color to the palette:

            >>> spalette = StackPalette()
            >>> spalette.add("4287f5")
            >>> spalette[0]
            Hex('#4287f5')
        """
        if i is None:
            i = len(self)
        self._color_stack.insert(i, self.color_format.format(color))

    def update(self, index: int, color: ColorLike):
        """Updates a color to a new value.

        Args:
            index: Index of the color to be updated.
            color: The value of the color to be updated. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the format of the color you want to update.

        Examples:
            Create a slightly dark shade of red:

            >>> spalette = StackPalette(["dd0000"])
            >>> spalette[0]
            Hex('#dd0000')

            Change it to be even a bit darker:

            >>> spalette.update(0, "800000")
            >>> spalette[0]
            Hex('#800000')
        """
        self._color_stack[index] = self.color_format.format(color)

    def remove(self):
        """Removes a color from the end of the palette.

        Colors can only be removed from the last index of the stack palette, just like in a normal
        stack.

        Examples:
            >>> spalette = StackPalette(["#ff0000"])
            >>> "#ff0000" in spalette
            True
            >>> spalette.remove()
            >>> "#ff0000" in spalette
            False
        """
        self._color_stack.pop()

    def save(self, name: str, palettes_dir: str = None):
        """Saves the changes made to this :class:`StackPalette` instance.

        If this method is not called after modifications made by :meth:`StackPalette.add()`,
        :meth:`StackPalette.update()` and :meth:`StackPalette.remove()`, the modifications on the
        palette will not be permanent.

        Examples:
            Create a new :class:`StackPalette` and save it to the current directory:

            >>> spalette = StackPalette(["ff0000", "00ff00", "0000ff"])
            >>> spalette.save(name="elementary")
        """
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        with open(Path(palettes_dir) / (name + ".spalette"), "w") as file:
            formatted_colors = []
            for c_val in self._color_stack:
                c_rgba = tuple(spec for spec in c_val._rgba)
                c_rgba = "#%02x" % c_rgba[-1] + "%02x%02x%02x" % c_rgba[:3]
                formatted_colors.append(c_rgba)
            json.dump(formatted_colors, file, indent=4)

    def to_palette(self, names: List[str]) -> Palette:
        """Converts this stack palette into a :class:`Palette`.

        Args:
            names: Names that will be given to the colors in the same order they appear in this
                stack palette.
        """
        if len(names) == len(set(names)) == len(self._color_stack):
            return Palette(dict(zip(names, self._color_stack)), color_format=self.color_format)
        raise ValueError("'names' must have the same length as this 'StackPalette' and no "
                         "duplicates")

    def grayscale(self):
        """Returns a copy of this object but with its colors in grayscale.

        Examples:

            >>> spalette = StackPalette(["ff0000", "ffff00"])
            >>> spalette.grayscale()
            StackPalette([#7f7f7f, #f7f7f7])
        """
        pal = StackPalette(color_format=self.color_format)
        for color in self.colors:
            pal.add(color.grayscale())
        return pal

    def most_similar(self, color: ColorLike, n=1, method="CIE76"):
        """Finds the `n` most similar colors to `color` in this palette.

        Args:
            color: The value of the color of reference.
            n: How many colors to be retrieved from most similar to least. -1 means all colors will be returned.
            method: Method for calculating color distance. See the documentation of `color_dist`.

        Examples:
            >>> palette = StackPalette(["#ff0000", "#0000ff"])
            >>> palette.most_similar("#880000")
            Hex('#ff0000')

        Returns:
            A single color object if `n` == 1 or a `StackPalette` if `n` != 1.
        """
        color = self.color_format.format(color)
        closest = sorted(self.colors,
                         key=lambda color2: utils.color_dist(color, color2, method=method))
        if n == 1:
            return closest[0]
        pal = StackPalette(color_format=self.color_format)
        pal._color_stack = closest
        if n < 0:
            return pal
        return pal[:n]

    def _for_each_color(self, func, obj=None, *args, **kwargs):
        pal = StackPalette(color_format=self.color_format)
        if obj is None:
            for color in self.colors:
                pal.add(func(color, *args, **kwargs))
            return pal
        if isinstance(obj, list):
            for color1, color2 in zip(self.colors, obj):
                pal.add(func(color1, color2, *args, **kwargs))
            return pal
        # Assume color-like
        for color in self.colors:
            pal.add(func(color, obj, *args, **kwargs))
        return pal


def find_palettes(palettes_dir: str = None,
                  search_builtins=True,
                  search_cwd=True,
                  kind=(Palette, StackPalette)) -> List[str]:
    """Returns the names of the palettes found in `directory`.

    Args:
        palettes_dir: The directory from which the palettes will be searched for. Defaults to the
            value specified in
            :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
        search_builtins: Whether to also include built-in palettes such as 'css' or
            'basic' in the search.
        search_cwd: Whether to also search palettes in the current working directory.
        kind: The kinds of palettes to include in the search. Can be either :class:`Palette`,
            :class:`StackPalette`, or a list of any of those.
    """
    palettes_dir = _resolve_palettes_dirs(palettes_dir, search_builtins=search_builtins, search_cwd=search_cwd)
    globs = []
    if not isinstance(kind, (tuple, list)):
        kind = [kind]
    if Palette in kind:
        globs.append("*.palette")
    if StackPalette in kind:
        globs.append("*.spalette")

    palettes = []
    for path in palettes_dir:
        path = Path(path)
        for glob in globs:
            for file in path.glob(glob):
                palettes.append(file.name[:file.name.index('.')])
    return palettes


def delete_palette(palette: str, palettes_dir: str = None):
    """Permanently deletes the file associated with a palette.

    Be careful when using this function, there is no way to recover a palette after it has been
    deleted.

    Args:
        palette: The name of the palette that will be deleted.
        palettes_dir: The directory containing the palette to be deleted.
            Defaults to the value specified in
            :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
    """
    if palettes_dir is None:
        palettes_dir = config.DEFAULT_PALETTES_DIR

    path = Path(palettes_dir)
    palettes = list(path.glob(f"{palette}.*"))
    if len(palettes) == 1:
        os.remove(path / palettes[0])
    elif len(palettes) == 0:
        raise ValueError(f"couldn't find palette '{palette}' in '{palettes_dir}'")
    else:
        raise ValueError(f"palette name '{palette}' is ambiguous (more than one palette share it)")


def _resolve_palettes_dirs(palettes_dir, search_builtins, search_cwd):
    if palettes_dir is None:
        palettes_dir = config.DEFAULT_PALETTES_DIR
    palettes_dir = [palettes_dir]
    if search_builtins:
        palettes_dir.append(_builtin_palettes_dir)
    if search_cwd:
        palettes_dir.append(os.getcwd())
    return palettes_dir
