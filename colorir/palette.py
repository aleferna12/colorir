"""Palettes to hold collections of colors that can be shared between projects.

The :class:`Palette` class provides an easy way to create and manage your favorite colors in
different projects. In this context, a palette should be understood as any collection of colors that
can be grouped due to a common feature, not only colors that necessarily look good together.

Examples:
    Create a palette with the additive elementary colors and call it 'elementary':

    >>> palette = Palette(name="elementary",
    ...                   redadd=sRGB(255, 0, 0),
    ...                   greenadd=sRGB(0, 255, 0),
    ...                   blueadd=sRGB(0, 0, 255))

    Following CSS color-naming conventions, our color names are all lowercase with no
    underscores, but you may name a color as you wish as long as it complies with python's
    syntax for attribute names

    Add subtractive elementary colors from their hex codes:

    >>> palette.add("cyansub", "#00ffff")
    >>> palette.add("magentasub", "#ff00ff")
    >>> palette.add("yellowsub", "#ffff00")

    Now suppose we want to use the colors we added to our palette.

    For that we can call them individually as attributes of the palette:

    >>> palette.magentasub
    sRGB(255, 0, 255)

    Or we can get them all at once with the :attr:`Palette.color` attribute:

    >>> palette.colors
    [sRGB(255, 0, 0), sRGB(0, 255, 0), sRGB(0, 0, 255), sRGB(0, 255, 255), sRGB(255, 0, 255), \
sRGB(255, 255, 0)]

    Since we are done using our palette for now, let's save it to the default palette directory
    so that we can load it latter with :meth:`Palette.load()` when needed:

    >>> palette.save()

    To load the palette latter:

    >>> palette = Palette.load("elementary")

    When loading or instantiating a palette, an :class:`ColorFormat` may be passed to the
    function:

    >>> c_format = ColorFormat(color_sys=HexRGB, uppercase=True)
    >>> css = Palette.load("css", color_format=c_format)
    >>> css.red
    HexRGB(#FF0000)

    You can also temporarily change the default color format system-wide so that new palettes
    default to it:

    >>> from colorir import config
    >>> from colorir.color_format import WEB_COLOR_FORMAT, PYGAME_COLOR_FORMAT
    >>> config.DEFAULT_COLOR_FORMAT = WEB_COLOR_FORMAT
    >>> web_palette = Palette.load("css")
    >>> web_palette.red
    HexRGB(#ff0000)
    >>> config.DEFAULT_COLOR_FORMAT = PYGAME_COLOR_FORMAT
    >>> pygame_palette = Palette.load("rainbow")
    >>> pygame_palette.red
    sRGB(255, 0, 0)
"""

import json
from pathlib import Path
from typing import Dict, Union, List, Tuple
from logging import warning
import config
from color import ColorBase, ColorLike, sRGB, HexRGB
from color_format import ColorFormat

_throw_exception = object()
_builtin_palettes_dir = Path(__file__).resolve().parent / "builtin_palettes"


class Palette:
    """Class that holds colors values associated with names.


    Attributes:
        name: Name of the palette which will be used to save it with the :meth:`Palette.save()`.
    """

    def __init__(self,
                 name: str = None,
                 color_format: ColorFormat = None,
                 **colors: Dict[str, ColorLike]):
        if color_format is None:
            c_vals = tuple(colors.values())
            if c_vals and isinstance(c_vals[0], ColorBase):
                color_format = c_vals[0].get_format()
            else:
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
        be changed through the `warning`parameter.

        Args:
            palettes: List of palettes located in the locations represented by `palettes_dir` that
                should be loaded by this :class:`Palette` instance. Addtionally may include built-in
                palettes such as 'css' if `search_builtins` is set to ``True``. If this parameter is
                a string, the :attr:`Palettes.name` will be inferred from it. By default, loads all
                palettes found in the specified directories.
            palettes_dir: The directory from which the palettes specified in the `palettes`
                parameter will be loaded. Defaults to the value specified in
                :data:`config.DEFAULT_PALETTES_DIR`.
            search_builtins: Whether `palettes` also includes built-in palettes such as 'css' or
                'rainbow'. Set to ``False`` to ensure only palette files found in `palettes_dir` are
                loaded.
            name: Name of the palette which will be used to save it with the :meth:`Palette.save()`.
                If the `palettes` parameter is a single string, defaults to that.
            color_format: Color format specifying how the colors of this :class:`Palette` should be
                stored. Defaults to the value specified in :data:`config.DEFAULT_COLOR_FORMAT`.
            warnings: Whether to emit a warning if two colors with the same name but different color
                values were found in the `palettes`.

        Examples:
            Loads the default CSS palette:

            >>> css_palette = Palette.load('css')

            Loads both the rainbow and fluorescent palettes into a new palette called 'colorful':

            >>> colorful = Palette.load(['rainbow', 'fluorescent'], name='colorful')
        """
        if palettes_dir is None:
            search_dirs = config.DEFAULT_PALETTES_DIR
        if isinstance(search_dirs, str):
            search_dirs = [search_dirs]
        if search_builtins:
            search_dirs.append(_builtin_palettes_dir)
        if isinstance(palettes, str):
            if name is None:
                name = palettes
            palettes = [palettes]

        found_palettes = {}
        for path in search_dirs:
            path = Path(path)
            palette_files = path.glob("*.palette")
            for palette_file in palette_files:
                palette_name = palette_file.name.replace(".palette", '')
                found_palettes[palette_name] = palette_file

        palette_obj = cls(name=name, color_format=color_format)
        if palettes is None: palettes = list(found_palettes)
        # Reiterates based on user input order
        for palette_name in palettes:
            palette_file = found_palettes[palette_name]
            with open(palette_file) as file:
                palette = json.load(file)
            for c_name, c_rgba in palette.items():
                new_color = palette_obj.color_format._from_rgba(c_rgba)
                old_color = palette_obj.get_color(c_name, new_color)
                if new_color != old_color and warnings:
                    warning(
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

    def __getattr__(self, item):
        return self._color_dict[item]

    def __repr__(self):
        arg_str = f"{self.name.__repr__()}, " if self.name is not None else ""
        arg_str += ", ".join(f"{c_name}={c_val}" for c_name, c_val in self._color_dict.items())
        return f"{self.__class__.__name__}({arg_str})"

    def get_color(self, name: str, fallback=_throw_exception) -> ColorBase:
        """Retrieves a color from the :class:`Palette` given its name.

        Args:
            name: Name of the color to be retrieved.
            fallback: What to return in case the color is not present in the palette. By default,
                throws an exception.

        Examples:
            >>> palette = Palette(red=sRGB(255, 0, 0))
            >>> palette.get_color("red")
            sRGB(255, 0, 0)
        """
        if fallback is _throw_exception:
            return self._color_dict[name]
        return self._color_dict.get(name, fallback)

    def get_names(self, color: ColorLike) -> list:
        """Finds the names of the provided color in this :class:`Palette`.

        Compares the provided `color` to every color the :class:`Palette` contains and returns the
        names of the colors that are equivalent to the one provided.

        Args:
            color: The value of the color to be created. Can be an instance of any
                :doc:`color class <color>` or, alternatively, a color-like object that resembles
                the color you want to search for.

        Examples:
            >>> palette = Palette(red=sRGB(255, 0, 0))
            >>> palette.get_names(HexRGB("#ff0000"))
            ['red']
            >>> palette.get_names((255, 0, 0))
            ['red']
            >>> palette.get_names("#ff0000")
            ['red']
        """
        color = self.color_format.format(color)
        color_list = []
        for name in self.color_names:
            if self.get_color(name) == color:
                color_list.append(name)
        return color_list

    # TODO
    def find_closest(self, color: ColorLike) -> Tuple[str, ColorBase]:
        pass

    def add(self, name: str, color: ColorLike):
        """Adds a color to a palette.

        .. warning::

            Two colors with the same name but different values are invalid and can not coexist in a
            same :class:`Palette`. You should therefore avoid reusing names for already existing
            colors.

        Args:
            name: Name to be assigned to the new color.
            color: The value of the color to be created. Can be an instance of any
                :doc:`color class <color>` or, alternatively, a color-like object that resembles
                the color you want to add.

        Examples:
            Creating a new gray color:

            >>> palette = Palette()
            >>> palette.add("gray96", (96, 96, 96))
            >>> palette.gray96
            sRGB(96, 96, 96)
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
                :mod:`color class <colordict.color>` or, alternatively, a color-like object that
                resembles the format of the color you want to update.

        Examples:
            Create a slightly dark shade of red:
            
            >>> palette = Palette(myred=sRGB(250, 0, 0))
            >>> palette.myred
            sRGB(250, 0, 0)
            
            Change it to be even a bit darker:
            
            >>> palette.update("myred", (200, 0, 0))
            >>> palette.myred
            sRGB(200, 0, 0)
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

    def save(self, directory: str = None):
        """Saves the changes made to this :class:`Palette` instance.

        If this method is not called after modifications made by :meth:`add`, :meth:`update` and
        :meth:`remove`, the modifications on the palette will not be permanent.

        Examples:
            Loads both the rainbow and fluorescent palettes into a new palette called 'colorful':

            >>> colorful = Palette.load(['rainbow', 'fluorescent'], name='colorful')

            Save the palette to the default palette directory:

            >>> colorful.save()
        """
        if self.name is None:
            raise AttributeError(
                "the 'name' attribute of a 'Palette' instance must be defined to save it")
        if directory is None:
            directory = config.DEFAULT_PALETTES_DIR
        with open(Path(directory) / (self.name + ".palette"), "w") as file:
            json.dump({c_name: c_val._rgba for c_name, c_val in self._color_dict.items()}, file,
                      indent=4)
