"""Palettes to hold collections of colors that can be shared between projects.

The :class:`Palette` class provides an easy way to manage your favorite colors in different
projects. In this context, a palette should be understood as any collection of colors that
can be grouped due to a common feature, not only colors that necessarily "look good" together.

Every color in a :class:`Palette` has a name associated with it. If unnamed colors are better fit
to your particular use case, you may want to use a :class:`StackPalette` instead.

Examples:
    Create a palette with the color red:

    >>> palette = Palette(red="#ff0000")

    Add the color blue:

    >>> palette.add("blue", "#0000ff")

    Get the value for red:

    >>> palette.red
    Hex('#ff0000')

    Get names of all colors:

    >>> palette.color_names
    ['red', 'blue']

    Remove red:

    >>> palette.remove("red")
    >>> "red" in palette.color_names
    False

    Name the palette and save it to the default directory:

    >>> palette.name = "single_blue"
    >>> palette.save()

    Load it again from elsewhere later:

    >>> palette = Palette.load("single_blue")
"""
import abc
import json
import os
from pathlib import Path
from typing import Union, List
from warnings import warn

from . import config
from . import utils
from .color_class import ColorBase, sRGB, HSL, HSV
from .color_format import ColorFormat, ColorLike

_throw_exception = object()
_builtin_palettes_dir = Path(__file__).resolve().parent / "builtin_palettes"

__all__ = [
    "Palette",
    "StackPalette",
    "find_palettes",
    "delete_palette"
]


class PaletteBase(metaclass=abc.ABCMeta):
    def __init__(self, name=None, color_format=None):
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self.name = name
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

    def __len__(self):
        return len(self.colors)

    def __contains__(self, item):
        return self.color_format.format(item) in self.colors

    def __iter__(self):
        return iter(self.colors)

    def most_similar(self, color: ColorLike, n=1, method="CIE76"):
        """Finds the `n` most similar colors to `color` in this palette.

        Args:
            color: The value of the color of reference. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the color to which others will be compared in search of similar results.
            n: How many similar colors to be retrieved. -1 means all colors from the palette will
                be returned from most similar to least.
            method: Method for calculating color distance. See the documentation of
                :func:`~colorir.utils.color_dist()`.

        Examples:
            >>> palette = Palette(red="#ff0000", blue="#0000ff")
            >>> palette.most_similar("#880000")
            Hex('#ff0000')

        Returns:
            A single :class:`~colorir.color_class.ColorBase` if `n` == 1 or a list of
            :class:`~colorir.color_class.ColorBase` if `n` != 1. If the return type is a list, the
            colors will be ordered from most similar to least.
        """
        color = self.color_format.format(color)
        closest = sorted(self.colors,
                         key=lambda color2: utils.color_dist(color, color2, method=method))
        if n == 1:
            return closest[0]
        elif n < 0:
            n = len(self)
        return closest[:n]

    def to_cmap(self, N: int = None):
        """Converts this palette into a matplotlib ListedColormap.

        Args:
            N: Passed down to ListedColormap constructor.
        """
        from matplotlib.colors import ListedColormap

        colors = [color.hex(include_a=True, tail_a=True) for color in self.colors]
        if self.name is None:
            return ListedColormap(colors, N=N)
        return ListedColormap(colors, N=N, name=self.name)


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
                 name: str = None,
                 color_format: ColorFormat = None,
                 **colors: ColorLike):
        super().__init__(name, color_format)

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
             name: str = None,
             color_format: ColorFormat = None,
             warnings=True):
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
                built-in palettes such as 'css' if `search_builtins` is set to ``True``. If this
                parameter is a string, the :attr:`Palette.name` will be inferred from it. By
                default, loads all palettes found in the specified directory.
            palettes_dir: The directory from which the palettes specified in the `palettes`
                parameter will be loaded. Defaults to the value specified in
                :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
            search_builtins: Whether `palettes` may also include built-in palettes such as 'css'
                or 'basic'.
            search_cwd: Whether `palettes` may also include palettes located in the current
                working directory.
            name: Name of the palette which will be used to save it with the
                :meth:`Palette.save()`. If the `palettes` parameter is a single string, defaults
                to that.
            color_format: Color format specifying how the colors of this :class:`Palette` should be
                stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
            warnings: Whether to emit a warning if two colors with the same name but different
                color values were found in the `palettes`.

        Examples:
            Loads the default CSS palette:

            >>> css_palette = Palette.load('css')

            Loads both the basic and fluorescent palettes into a new palette called 'colorful':

            >>> colorful = Palette.load(['basic', 'fluorescent'], name='colorful')
        """
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        palettes_dir = [palettes_dir]
        if search_builtins:
            palettes_dir.append(_builtin_palettes_dir)
        if search_cwd:
            palettes_dir.append(os.getcwd())
        if isinstance(palettes, str):
            if name is None:
                name = palettes
            palettes = [palettes]

        found_palettes = {}
        for path in palettes_dir:
            path = Path(path)
            palette_files = path.glob("*.palette")
            for palette_file in palette_files:
                palette_name = palette_file.name.replace(".palette", '')
                found_palettes[palette_name] = json.loads(palette_file.read_text())

        palette_obj = cls(name=name, color_format=color_format)
        if palettes is None: palettes = list(found_palettes)
        # Reiterates based on user input order
        for palette_name in palettes:
            for c_name, c_rgba in found_palettes[palette_name].items():
                c_rgba = (int(c_rgba[3:5], 16),
                          int(c_rgba[5:7], 16),
                          int(c_rgba[7:9], 16),
                          int(c_rgba[1:3], 16))
                new_color = palette_obj.color_format._from_rgba(c_rgba)
                old_color = palette_obj.get_color(c_name, new_color)
                if new_color != old_color and warnings:
                    warn(
                        f"a discrepancy was detected when adding color '{c_name}' "
                        f"({new_color}) from palette named '{palette_name}': '{c_name}' is "
                        f"already present with a different value ({old_color})")
                else:
                    palette_obj.add(c_name, new_color)
        return palette_obj

    def __getattr__(self, item):
        return self._color_dict[item]

    def __str__(self):
        name_str = self.name + ", " if self.name else ""
        colors_str = ', '.join(
            f"{c_name}={c_val}" for c_name, c_val in self._color_dict.items()
        )
        return f"{self.__class__.__name__}({name_str}{colors_str})"

    def __repr__(self):
        if config.REPR_STYLE in ["traditional", "inherit"]:
            return str(self)
        return utils.swatch(self, stdout=False)

    def __eq__(self, other):
        return self._color_dict.items() == other._color_dict.items()

    def __add__(self, other):
        c_dict = dict(self._color_dict)
        c_dict.update(other._color_dict)
        return Palette(**c_dict)

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
            >>> palette = Palette(red=sRGB(255, 0, 0))
            >>> palette.remove("red")
            >>> "red" in palette.color_names
            False
        """
        if name in self._color_dict:
            del self._color_dict[name]
        else:
            raise ValueError(f"provided 'name' parameter is not a color stored in this 'Palette'")

    def save(self, palettes_dir: str = None):
        """Saves the changes made to this :class:`Palette` instance.

        If this method is not called after modifications made by :meth:`Palette.add()`,
        :meth:`Palette.update()` and :meth:`Palette.remove()`, the modifications on the palette
        will not be permanent.

        Examples:
            Loads both the basic and fluorescent palettes into a new palette called 'colorful':

            >>> colorful = Palette.load(['basic', 'fluorescent'], name='colorful')

            Save the palette to the default palette directory:

            >>> colorful.save()
        """
        if self.name is None:
            raise AttributeError(
                "the 'name' attribute of a 'Palette' instance must be defined to save it")
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        with open(Path(palettes_dir) / (self.name + ".palette"), "w") as file:
            formatted_colors = {}
            for c_name, c_val in self._color_dict.items():
                c_rgba = c_val.hex(include_a=True, tail_a=False)
                formatted_colors[c_name] = c_rgba
            json.dump(formatted_colors, file, indent=4)

    def to_stackpalette(self) -> "StackPalette":
        """Converts this palette into a :class:`StackPalette`."""
        return StackPalette(self.name, self.color_format, *self._color_dict.values())

    def to_dict(self):
        """Converts this palette into a python `dict`."""
        return dict(self._color_dict)


class StackPalette(PaletteBase):
    """Class that handles anonymous indexed colors stored as a stack.

    This class may be used as a replacement for :class:`Palette` when the name of the colors is
    irrelevant.

    Examples:
        >>> spalette = StackPalette("elementary", None, "ff0000", "00ff00", "0000ff")
        >>> spalette[0]
        Hex('#ff0000')

    Args:
        name: Name of the palette which will be used to save it with
            :meth:`StackPalette.save()`.
        color_format: Color format specifying how the colors of this :class:`StackPalette` should
            be stored. Defaults to the value specified in
            :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        colors: Colors that will be stored in this palette.
    """

    def __init__(self,
                 name: str = None,
                 color_format: ColorFormat = None,
                 *colors: ColorLike):
        super().__init__(name=name, color_format=color_format)

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
             name: str = None,
             color_format: ColorFormat = None):
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
                that should be loaded by this :class:`StackPalette` instance. If this parameter is
                a string, the :attr:`StackPalette.name` will be inferred from it. By default,
                loads all palettes found in the specified directory.
            palettes_dir: The directory from which the palettes specified in the `palettes`
                parameter will be loaded. Defaults to the value specified in
                :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
            search_builtins: Whether `palettes` may also include built-in palettes such as 'tab10'
                or 'dark2'.
            search_cwd: Whether `palettes` may also include palettes located in the current
                working directory.
            name: Name of the palette which will be used to save it with the
                :meth:`StackPalette.save()`. If the `palettes` parameter is a single string,
                defaults to that.
            color_format: Color format specifying how the colors of this :class:`Palette` should be
                stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        """
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        palettes_dir = [palettes_dir]
        if search_builtins:
            palettes_dir.append(_builtin_palettes_dir)
        if search_cwd:
            palettes_dir.append(os.getcwd())
        if isinstance(palettes, str):
            if name is None:
                name = palettes
            palettes = [palettes]

        found_palettes = {}
        for path in palettes_dir:
            path = Path(path)
            palette_files = path.glob("*.spalette")
            for palette_file in palette_files:
                palette_name = palette_file.name.replace(".spalette", '')
                found_palettes[palette_name] = json.loads(palette_file.read_text())

        palette_obj = cls(name=name, color_format=color_format)
        if palettes is None: palettes = list(found_palettes)
        # Reiterates based on user input order
        for palette_name in palettes:
            for c_rgba in found_palettes[palette_name]:
                c_rgba = (int(c_rgba[3:5], 16),
                          int(c_rgba[5:7], 16),
                          int(c_rgba[7:9], 16),
                          int(c_rgba[1:3], 16))
                new_color = palette_obj.color_format._from_rgba(c_rgba)
                palette_obj.add(new_color)
        return palette_obj

    # TODO enhance to allow different color systems and variance param (prob. 1.4.0)
    @classmethod
    def new_complementary(cls,
                          n: int,
                          color: ColorLike = None,
                          name: str = None,
                          color_format: ColorFormat = None):
        """Creates a new palette with `n` complementary colors.

        Colors are considered complementary if they are interspaced in the additive HUE color
        wheel.

        Examples:
             Make a palette from red and its complementary color, cyan:

             >>> spalette = StackPalette.new_complementary(2, sRGB(255, 0, 0))
             >>> spalette
             StackPalette(Hex('#ff0000'), Hex('#00ffff'))

             Make a tetradic palette of random colors:

             >>> spalette = StackPalette.new_complementary(4)

        Args:
            n: The number of colors in the new palette.
            color: A color from which the others will be generated against. By default, a color is
                randomly chosen.
            name: Name of the palette which will be used to save it with
                :meth:`StackPalette.save()`.
            color_format: Color format specifying how the colors of this :class:`StackPalette`
                should be stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        """
        n_spalette = cls(name=name, color_format=color_format)
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
                      name: str = None,
                      color_format: ColorFormat = None):
        """Creates a new palette with `n` analogous colors.

        Colors are considered analogous if they are side-by-side in the additive HUE color wheel.

        Examples:
             Make a palette from red and its analogous color, orange:

             >>> spalette = StackPalette.new_analogous(2, start=1, color=sRGB(255, 0, 0))
             >>> spalette
             StackPalette(Hex('#ff0000'), Hex('#ff8000'))

             Make a palette of four similar colors:

             >>> spalette = StackPalette.new_analogous(4, sections=24)

        Args:
            n: The number of colors in the new palette.
            sections: The number of sections in which the additive HUE color wheel will be divided
                before sampling colors. The bigger this number, the more similar the colors will
                be.
            start: Where the color described in the 'color' parameter will be placed with respect
                to the others. If '0', 'color' will be in the center of the generated palette, and
                colors will be sampled from both its sides in the HUE wheel. If '1', colors will
                be sampled clockwise from 'color'. If '-1', they will be sampled counter-clockwise.
            color: A color from which the others will be generated against. By default, a color is
                randomly chosen.
            name: Name of the palette which will be used to save it with
                :meth:`StackPalette.save()`.
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

        n_spalette = cls(name=name, color_format=color_format)
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
        if isinstance(item, list):
            return [self._color_stack[i] for i in item]
        return self._color_stack[item]

    def __setitem__(self, key, value):
        if isinstance(key, list):
            for i, val in zip(key, value):
                self.update(i, val)
        else:
            self.update(key, value)

    def __str__(self):
        name_str = self.name + ", " if self.name else ""
        colors_str = ', '.join(c_val.__repr__() for c_val in self._color_stack)
        return f"{self.__class__.__name__}({name_str}{colors_str})"

    def __repr__(self):
        if config.REPR_STYLE in ["traditional", "inherit"]:
            return str(self)
        return utils.swatch(self, stdout=False)

    def __eq__(self, other):
        return self._color_stack == other._color_stack

    def __add__(self, other):
        c_list = self.colors + other.colors
        return StackPalette(None, None, *c_list)

    def swap(self, index1: int, index2: int):
        """Swap the places of two colors in the palette.

        Can be used to reorganize the palette if needed.

        Examples:
            >>> spalette = StackPalette(None, None, "ff0000", "0000ff")
            >>> spalette
            StackPalette(Hex('#ff0000'), Hex('#0000ff'))
            >>> spalette.swap(0, 1)
            >>> spalette
            StackPalette(Hex('#0000ff'), Hex('#ff0000'))

        Args:
            index1: The index of the first color.
            index2: The index of the second color.
        """
        c_temp = self._color_stack[index1]
        self._color_stack[index1] = self._color_stack[index2]
        self._color_stack[index2] = c_temp

    def add(self, color: ColorLike):
        """Adds a color to the end of the stack palette.

        Colors can only be added to the last index of the stack palette, just like in a normal
        stack.

        Args:
            color: The value of the color to be created. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the color you want to add.

        Examples:
            Adding a new blue color to the palette:

            >>> spalette = StackPalette()
            >>> spalette.add("4287f5")
            >>> spalette[0]
            Hex('#4287f5')
        """
        self._color_stack.append(self.color_format.format(color))

    def update(self, index: int, color: ColorLike):
        """Updates a color to a new value.

        Args:
            index: Index of the color to be updated.
            color: The value of the color to be updated. Can be an instance of any
                :mod:`~colorir.color_class` class or, alternatively, a color-like object that
                resembles the format of the color you want to update.

        Examples:
            Create a slightly dark shade of red:

            >>> spalette = StackPalette(None, None, "dd0000")
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
            >>> spalette = StackPalette(None, None, "#ff0000")
            >>> "#ff0000" in spalette
            True
            >>> spalette.remove()
            >>> "#ff0000" in spalette
            False
        """
        self._color_stack.pop()

    def save(self, palettes_dir: str = None):
        """Saves the changes made to this :class:`StackPalette` instance.

        If this method is not called after modifications made by :meth:`StackPalette.add()`,
        :meth:`StackPalette.update()` and :meth:`StackPalette.remove()`, the modifications on the
        palette will not be permanent.

        Examples:
            Create a new :class:`StackPalette` and save it to the current directory:

            >>> spalette = StackPalette("elementary", None, "ff0000", "00ff00", "0000ff")
            >>> spalette.save()
        """
        if self.name is None:
            raise AttributeError(
                "the 'name' attribute of a 'StackPalette' instance must be defined to save it"
            )
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        with open(Path(palettes_dir) / (self.name + ".spalette"), "w") as file:
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
            return Palette(self.name, self.color_format, **dict(zip(names, self._color_stack)))
        raise ValueError("'names' must have the same length as this 'StackPalette' and no "
                         "duplicates")


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
    if palettes_dir is None:
        palettes_dir = config.DEFAULT_PALETTES_DIR
    if isinstance(palettes_dir, str):
        palettes_dir = [palettes_dir]
    if search_builtins:
        palettes_dir.append(_builtin_palettes_dir)
    if search_cwd:
        palettes_dir.append(os.getcwd())
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