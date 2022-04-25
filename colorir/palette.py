"""Palettes to hold collections of colors that can be shared between projects.

The :class:`Palette` class provides an easy way to manage your favorite colors in different
projects. In this context, a palette should be understood as any collection of colors that
can be grouped due to a common feature, not only colors that necessarily "look good" together.

Examples:
    Create a palette with the color red:

    >>> palette = Palette(red="#ff0000")

    Add the color blue:

    >>> palette.add("blue", "#0000ff")

    Get the value for red:

    >>> palette.red
    HexRGB(#ff0000)

    Get names of all colors:

    >>> palette.color_names
    ['red', 'blue']

    Remove red:

    >>> palette.remove("red")
    >>> "red" in palette
    False

    Name the palette and save it to the default directory:

    >>> palette.name = "single_blue"
    >>> palette.save()

    Load it again from elsewhere latter:

    >>> palette = Palette.load("single_blue")
"""

import json
from pathlib import Path
from typing import Dict, Union, List
from warnings import warn

from . import config
from .color import ColorBase, ColorLike, sRGB, HexRGB
from .color_format import ColorFormat

_throw_exception = object()
_builtin_palettes_dir = Path(__file__).resolve().parent.parent / "builtin_palettes"


class Palette:
    """Class that holds colors values associated with names.

    Examples:
        >>> palette = Palette(red="#ff0000") # Uses default color format
        >>> palette.red
        HexRGB(#ff0000)

        For more examples see the documentation of the :mod:`~colorir.palette` module.

    Args:
        name: Name of the palette which will be used to save it with the :meth:`Palette.save()`.
            If the `palettes` parameter is a single string, defaults to that.
        color_format: Color format specifying how the colors of this :class:`Palette` should be
            stored. Defaults to the value specified in
            :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
        colors: Colors that will be stored in this palette.

    Attributes:
        name: Name of the palette which will be used to save it with the :meth:`Palette.save()`.
    """

    def __init__(self,
                 name: str = None,
                 color_format: ColorFormat = None,
                 **colors: Dict[str, ColorLike]):
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self.name = name
        self._color_format = color_format
        self._color_dict = {}
        for k, v in colors.items():
            self.add(k, v)

    @classmethod
    def load(cls,
             palettes: Union[str, List[str]] = None,
             palettes_dir: str = None,
             search_builtins=True,
             name: str = None,
             color_format: ColorFormat = None,
             warnings=True):
        """Factory method that loads previously created palettes into a :class:`Palettes` instance.

        A palette is a file containing json-formatted information about colors that ends with the
        '.palettes' extension. You should not create such files manually but rather through the
        :meth:`Palette.save()` method.

        If multiple palettes define different color values under the same name, only the first one
        will be kept. You can define the order in which the palettes are loaded by ordering them in
        the `palettes` parameter. By default this occurrence logs a warning, but this behaviour can
        be changed through the `warning` parameter.

        Args:
            palettes: List of palettes located in the locations represented by `palettes_dir` that
                should be loaded by this :class:`Palette` instance. Addtionally may include built-in
                palettes such as 'css' if `search_builtins` is set to ``True``. If this parameter is
                a string, the :attr:`Palettes.name` will be inferred from it. By default, loads all
                palettes found in the specified directories.
            palettes_dir: The directory from which the palettes specified in the `palettes`
                parameter will be loaded. Defaults to the value specified in
                :data:`config.DEFAULT_PALETTES_DIR <colorir.config.DEFAULT_PALETTES_DIR>`.
            search_builtins: Whether `palettes` also includes built-in palettes such as 'css' or
                'basic'. Set to ``False`` to ensure only palette files found in `palettes_dir` are
                loaded.
            name: Name of the palette which will be used to save it with the :meth:`Palette.save()`.
                If the `palettes` parameter is a single string, defaults to that.
            color_format: Color format specifying how the colors of this :class:`Palette` should be
                stored. Defaults to the value specified in
                :data:`config.DEFAULT_COLOR_FORMAT <colorir.config.DEFAULT_COLOR_FORMAT>`.
            warnings: Whether to emit a warning if two colors with the same name but different color
                values were found in the `palettes`.

        Examples:
            Loads the default CSS palette:

            >>> css_palette = Palette.load('css')

            Loads both the basic and fluorescent palettes into a new palette called 'colorful':

            >>> colorful = Palette.load(['basic', 'fluorescent'], name='colorful')
        """
        if palettes_dir is None:
            palettes_dir = config.DEFAULT_PALETTES_DIR
        if isinstance(palettes_dir, str):
            palettes_dir = [palettes_dir]
        if search_builtins:
            palettes_dir.append(_builtin_palettes_dir)
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
                c_rgba = (int(c_rgba[3:5], 16) / 255,
                          int(c_rgba[5:7], 16) / 255,
                          int(c_rgba[7:9], 16) / 255,
                          int(c_rgba[1:3], 16) / 255)
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

    @property
    def colors(self):
        """colors: A list of all color values currently stored in the :class:`Palette`."""
        return list(self._color_dict.values())

    @property
    def color_names(self):
        """colors: A list of all color names currently stored in the :class:`Palette`."""
        return list(self._color_dict.keys())

    @property
    def color_format(self):
        """color_format: Color format specifying how the colors of this :class:`Palette` are
        stored.
        """
        return self._color_format

    # color_format could be used to build a color on every Palette.color call, but that is
    # computationally intensive. That's why the colors are stored as ready objects and are
    # re-created if needed
    @color_format.setter
    def color_format(self, value):
        self._color_dict = {c_name: value._from_rgba(c_value._rgba)
                            for c_name, c_value in self._color_dict.items()}
        self._color_format = value

    def __len__(self):
        return len(self._color_dict)

    def __contains__(self, item):
        if isinstance(item, ColorBase):
            return item in self._color_dict.values()
        if isinstance(item, str):
            return item in self._color_dict
        raise TypeError(
            f"'in <Palette>' requires string or 'ColorBase' as left operand, not "
            f"{type(item).__name__}")

    def __iter__(self):
        for c_val in self._color_dict.values():
            yield c_val

    def __getattr__(self, item):
        return self._color_dict[item]

    def __repr__(self):
        opener_str = f"{self.__class__.__name__}("
        joint = ",\n" + ' ' * len(opener_str)
        name_str = f"{self.name.__repr__()}{joint}" if self.name is not None else ""
        color_strs = [f"{c_name}={self._color_dict[c_name].__repr__()}"
                      for c_name in self._color_dict]
        if len(color_strs) <= 10:
            return opener_str + name_str + joint.join(color_strs) + ")"
        return opener_str + name_str + joint.join(color_strs[:5]) \
               + f"{joint}...{joint.lstrip(',')}" + joint.join(color_strs[-5:]) + ")"

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
            HexRGB(#ff0000)
            >>> palette.get_color(["red", "blue"])
            [HexRGB(#ff0000), HexRGB(#0000ff)]

        Returns:
            A list of
        """
        if fallback is _throw_exception:
            if isinstance(name, str):
                return self._color_dict[name]
            return [self._color_dict[name_i] for name_i in name]
        if isinstance(name, str):
            return self._color_dict.get(name, fallback)
        return [self._color_dict.get(name_i, fallback) for name_i in name]

    def get_names(self, color: ColorLike) -> list:
        """Finds the names of the provided color in this :class:`Palette`.

        Compares the provided `color` to every color the :class:`Palette` contains and returns the
        names of the colors that are equivalent to the one provided.

        Args:
            color: The value of the color to be searched for. Can be an instance of any
                :mod:`~colorir.color` class or, alternatively, a color-like object that resembles
                the color you want to search for.

        Examples:
            >>> palette = Palette(red=sRGB(255, 0, 0))
            >>> palette.get_names(HexRGB("#ff0000"))
            ['red']
            >>> palette.get_names((255, 0, 0))
            ['red']
            >>> palette.get_names("#ff0000")
            ['red']

        Returns:
            A single :class:`~colorir.color.ColorBase` if `name` is a string or a list of
            :class:`~colorir.color.ColorBase` if `name` is a list of strings.
        """
        color = self.color_format.format(color)
        color_list = []
        for name in self.color_names:
            if self.get_color(name) == color:
                color_list.append(name)
        return color_list

    def add(self, name: str, color: ColorLike):
        """Adds a color to a palette.

        Two colors with the same name but different values are invalid and can not coexist in a
        same :class:`Palette`. You should therefore avoid reusing names for already existing
        colors.

        Args:
            name: Name to be assigned to the new color.
            color: The value of the color to be created. Can be an instance of any
                :mod:`~colorir.color` class or, alternatively, a color-like object that resembles
                the color you want to add.

        Examples:
            Adding a new blue color to the palette:

            >>> palette = Palette()
            >>> palette.add("bestblue", "4287f5")
            >>> palette.bestblue
            HexRGB(#4287f5)
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
                :mod:`~colorir.color` class or, alternatively, a color-like object that
                resembles the format of the color you want to update.

        Examples:
            Create a slightly dark shade of red:
            
            >>> palette = Palette(myred="dd0000")
            >>> palette.myred
            HexRGB(#dd0000)
            
            Change it to be even a bit darker:
            
            >>> palette.update("myred", "800000")
            >>> palette.myred
            HexRGB(#800000)
        """
        if name in self._color_dict:
            self._color_dict[name] = self.color_format.format(color)
        else:
            raise ValueError(f"provided 'name' parameter is not a color loaded in this 'Palette'")

    def remove(self, name):
        """Removes a color from a palette.

        Args:
            name: Name of the color to be removed.

        Examples:
            >>> palette = Palette(red=sRGB(255, 0, 0))
            >>> palette.remove("red")
            >>> "red" in palette
            False
        """
        if name in self._color_dict:
            del self._color_dict[name]
        else:
            raise ValueError(f"provided 'name' parameter is not a color stored in this 'Palette'")

    def save(self, palettes_dir: str = None):
        """Saves the changes made to this :class:`Palette` instance.

        If this method is not called after modifications made by :meth:`Palette.add()`,
        :meth:`Palette.update()` and :meth:`Palette.remove()`, the modifications on the palette will
        not be permanent.

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
                c_rgba = tuple(round(spec * 255) for spec in c_val._rgba)
                c_rgba = "#%02x" % c_rgba[-1] + "%02x%02x%02x" % c_rgba[:3]
                formatted_colors[c_name] = c_rgba
            json.dump(formatted_colors, file, indent=4)


def find_palettes(palettes_dir: str = None, search_builtins=True):
    """Returns the names of the palettes found in `directory`. If `search_builtins` is ``True``,
    also includes builtin_palettes.
    """
    if palettes_dir is None:
        palettes_dir = config.DEFAULT_PALETTES_DIR
    if isinstance(palettes_dir, str):
        palettes_dir = [palettes_dir]
    if search_builtins:
        palettes_dir.append(_builtin_palettes_dir)

    palettes = []
    for path in palettes_dir:
        path = Path(path)
        for file in path.glob("*.palette"):
            palettes.append(file.name.replace(".palette", ""))
    return palettes