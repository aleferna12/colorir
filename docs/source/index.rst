Welcome to colorir's documentation!
=====================================

API
---

.. toctree::

	api
	examples

What is colorir?
----------------

colorir is a package developed to unify your workflow with colors across different projects.

With colorir you can:

- Keep a unified selection of colors you like and use them in your different projects;
- Use these colors directly as input for other graphical or web frameworks;
- Easily convert between different color systems and formats;
- Create gradients between colors and sample from them;
- And much more!

colorir was designed to be your best friend when dealing with colors so that you won't ever need to write this kind of code again:

.. code-block:: python

	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)
	CSS_ALICEBLUE = (240, 248, 255)
	COOL_PURPLE = (11, 0, 51)
	MY_FAVORITE_GREEN = (113, 180, 141)
	TOP_NOTCH_RED = (131, 34, 50)
	# ... unnecessarily long and ugly list of colors

Installation
------------

To install colorir with pip use following command:

.. code-block:: shell

	$ python -m pip install colorir

Quick-Start
-----------

Create a palette with the additive elementary colors and call it 'elementary':

>>> palette = Palette(name="elementary",
...                   redadd=HexRGB("#ff0000"),
...                   greenadd=HexRGB("00ff00"), # No need to include the # symbol
...                   blueadd=HexRGB("#0000ff"))

Following CSS color-naming conventions, our color names are all lowercase with no
underscores, but you may name a color as you wish as long as it complies with python's
syntax for attribute names.

We can add colors by providing a name and a color-like object to the :meth:`Palette.add() <colorir.palette.Palette.add()>`
method:

>>> palette.add("cyansub", "#00ffff")
>>> palette.add("yellowsub", "#ffff00")
>>> palette.add("magentasub", HSL(300, 1, 0.5))

Note how in how we passed hex strings as arguments without initializing
:class:`~colorir.color.HexRGB` colors this time. Most objects in the colorir package can
interpret strings and tuples as colors implicitly!

We also passed an :class:`~colorir.color.HSL` object for "magentasub". Because we initialized
the palette with :class:`~colorir.color.HexRGB` colors, the HSL value will be internally
converted to a :class:`~colorir.color.HexRGB`, which can be useful if we don't know the hex code
of a color or want to modify attributes exposed in other color systems, such as saturation or
luminance.

For more details on how color-like objects are interpreted, visit the documentation of
:class:`~colorir.palette.Palette` and :meth:`ColorFormat.format() <colorir.color_format.ColorFormat.format()>`.

To then modify a color after it has been added, use the :meth:`Palette.update() <colorir.palette.Palette.update()>` method:

>>> palette.update("magentasub", "#ff11ff") # Mix some green component into the magenta

Now suppose we want to finally use the colors we added to our palette. For that we can get them
individually as attributes of the palette:

>>> palette.cyansub
HexRGB(#00ffff)

Or we can get them all at once with the :attr:`Palette.colors <colorir.palette.Palette.colors>` property:

>>> palette.colors
[HexRGB(#ff0000), HexRGB(#00ff00), HexRGB(#0000ff), HexRGB(#00ffff), HexRGB(#ffff00), \
HexRGB(#ff11ff)]

Since we are done using our palette for now, let's save it to the default palette directory:

>>> palette.save()

We can then latter load the palette (even from other projects if we wish!):

>>> palette = Palette.load("elementary")

When loading or instantiating a palette, a :class:`~colorir.color_format.ColorFormat` may be
passed to the constructor to specify how we want the color to be represented:

>>> c_format = ColorFormat(color_sys=HSL)
>>> css = Palette.load("css", color_format=c_format)
>>> css.red
HSL(0.0, 1.0, 0.5)

We can also change the format of all colors in a palette at any time by re-assigning its
:attr:`Palette.color_format <colorir.palette.Palette.color_format>` property:

>>> css.color_format = ColorFormat(color_sys=sRGB, max_rgba=1)
>>> css.red
sRGB(1.0, 0.0, 0.0)

Alternatively, we can temporarily change the default color format system-wide so that new
palettes (that don't already hold any :mod:`~colorir.color` objects) default to it:

>>> from colorir import config, PYGAME_COLOR_FORMAT
>>> config.DEFAULT_COLOR_FORMAT = PYGAME_COLOR_FORMAT # Change default format to PyGame
>>> pygame_palette = Palette(red=(255, 0, 0))
>>> pygame_palette.red
sRGB(255, 0, 0)

This makes it easy to configure colorir to work with any color format right out of the box!

By default, the default color format is lowercase hex strings, like what you expect to find
working with web development or matplotlib.

>>> from colorir import config, WEB_COLOR_FORMAT
>>> config.DEFAULT_COLOR_FORMAT = WEB_COLOR_FORMAT # Change default back to web-compatible
>>> web_palette = Palette.load("css")
>>> web_palette.red
HexRGB(#ff0000)

It is worth noting that all color classes inherit either ``tuple`` or ``str``, meaning that
no conversion is needed when passing them to other frameworks such as PyGame, Kivy and HTML embedding templates like Jinja.