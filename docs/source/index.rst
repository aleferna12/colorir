.. raw:: html

    <style> .rainbow {background-image: linear-gradient(to left, blue, green, yellow, red); -webkit-background-clip: text; color: transparent;} </style>

.. role:: rainbow

Welcome to :rainbow:`colorir`'s documentation!
==============================================

API
---

.. toctree::
    :maxdepth: 2

    api
    examples
    builtin_palettes
    palette_picker

What is colorir?
----------------

colorir is a package used to create and manipulate palettes and colors.
What makes colorir different from other similar packages like `colour <https://pypi.org/project/colour/>`_ and
`palettable <https://pypi.org/project/palettable/>`_ is that colorir focuses on personalization and interoperability:
you can create your own color palettes and use them with any other python package such as matplotlib, tkinter
or flask.

Main features
-------------

- Create color schemes and save them to use in different projects
- Interpolate colors in different formats (such as RGB, CIELab etc) to make gradients and color maps
- Have access to a curated selection of unique color palettes and color names
- Easily visualize swatches of colors in the terminal

Installation
------------

.. note::

    If you encounter permission errors when using colorir, please consider re-installing the package in user mode (by including the :code:`--user` flag in the pip install command).

To install colorir with pip use following command:

.. code-block:: shell

    $ python -m pip install colorir

Quick-Start
-----------

Create a palette with the additive elementary colors:

>>> palette = Palette(red="#ff0000",
...                   green="#00ff00",
...                   blue="#0000ff")

Following CSS color-naming conventions, our color names are all lowercase with no
underscores, but you may name a color as you wish as long as it complies with python's
syntax for attribute names.

Let's take a look at our palette in the terminal:

>>> palette  # Prints swatches representing the palette

.. raw:: html

    <p style="margin-bottom:0px; padding:0px; line-height:1;">
      <span style="background-color:#ff0000"> &emsp; </span> &nbsp; <span style="color:#ff0000"> red #ff0000 </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#00ff00"> &emsp; </span> &nbsp; <span style="color:#00ff00"> green #00ff00 </span>
    </p>
    <p style="margin-top:0px; padding:0px; line-height:1;">
      <span style="background-color:#0000ff"> &emsp; </span> &nbsp; <span style="color:#0000ff"> blue #0000ff </span>
    </p>

To add colors to a palette use the :meth:`Palette.add() <colorir.palette.Palette.add()>`
method:

>>> palette.add("cyan", "#00ffff")
>>> palette.add("yellow", HSL(60, 1, 0.5))  # We can pass colors in formats other than hex as well
>>> palette.add("magenta", CIELAB(60, -98, -60))  # They will be internally converted to match the rest of the palette
>>> palette

.. raw:: html

    <p style="margin-bottom:0px; padding:0px; line-height:1;">
      <span style="background-color:#ff0000"> &emsp; </span> &nbsp; <span style="color:#ff0000"> red #ff0000 </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#00ff00"> &emsp; </span> &nbsp; <span style="color:#00ff00"> green #00ff00 </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#0000ff"> &emsp; </span> &nbsp; <span style="color:#0000ff"> blue #0000ff </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#00ffff"> &emsp; </span> &nbsp; <span style="color:#00ffff"> cyan #00ffff </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#ffff00"> &emsp; </span> &nbsp; <span style="color:#ffff00"> yellow #ffff00 </span>
    </p>
    <p style="margin-top:0px; padding:0px; line-height:1;">
      <span style="background-color:#ff00ff"> &emsp; </span> &nbsp; <span style="color:#ff00ff"> magenta #ff00ff </span>
    </p>

To access the colors in a palette we can use dot attribute syntax:

>>> palette.cyan  # palette['cyan'] also works

.. raw:: html

    <p>
        <span style="background-color:#00ffff"> &emsp; </span> &nbsp; <span style="color:#00ffff"> #00ffff </span>
    </p>

We can make manipulate the properties of a color by adding and removing color
components from other color systems:

>>> palette.cyan - CIELab(50, 0, 0)  # Remove 50 CIELab lightness from cyan

.. raw:: html

    <p><span style="background-color:#007477"> &emsp; </span> &nbsp; <span style="color:#007477"> #007477 </span></p>

>>> palette.cyan - HCLab(0, 25, 0)  # Remove 25 HCLab saturation from cyan

.. raw:: html

    <p><span style="background-color:#a5f3f2"> &emsp; </span> &nbsp; <span style="color:#a5f3f2"> #a5f3f2 </span></p>

To interpolate colors we can use :func:`~colorir.utils.blend()`:

>>> blend(palette.yellow, palette.magenta, 0.5)  # Get color at 50% between yellow and magenta

.. raw:: html

    <p><span style="background-color:#f9afbe"> &emsp; </span> &nbsp; <span style="color:#f9afbe"> #f9afbe </span></p>

:func:`~colorir.utils.blend()` is actually a wrapper around the :class:`~colorir.gradient.Grad` class, which supports
interpolation in different color systems:

>>> Grad([palette.yellow, palette.magenta], color_sys=CIELab).n_colors(5)  # Interpolates 5 colors from yellow to magenta

.. raw:: html

    <p style="margin-bottom:0px; padding:0px; line-height:1;">
      <span style="background-color:#ffff00"> &emsp; </span> &nbsp; <span style="color:#ffff00"> #ffff00 </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#ffd471"> &emsp; </span> &nbsp; <span style="color:#ffd471"> #ffd471 </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#ffa6a6"> &emsp; </span> &nbsp; <span style="color:#ffa6a6"> #ffa6a6 </span>
    </p>
    <p style="margin:0px; padding:0px; line-height:1;">
      <span style="background-color:#ff71d3"> &emsp; </span> &nbsp; <span style="color:#ff71d3"> #ff71d3 </span>
    </p>
    <p style="margin-top:0px; padding:0px; line-height:1;">
      <span style="background-color:#ff00ff"> &emsp; </span> &nbsp; <span style="color:#ff00ff"> magenta #ff00ff </span>
    </p>

To save a palette use :meth:`Palette.save() <colorir.palette.Palette.save()>`:

>>> palette.save(name="elementary")  # Name palette 'elementary' and save it in the default palette directory

You can then later reload the palette in another script with :meth:`Palette.load() <colorir.palette.Palette.load()>`:

>>> palette = Palette.load("elementary")

When loading or creating a palette, a :class:`~colorir.color_format.ColorFormat` may be
passed to the constructor to specify how we want its colors to be represented:

>>> c_format = ColorFormat(color_sys=HSL)
>>> css = Palette.load("css", color_format=c_format)
>>> css.red
HSL(0.0, 1.0, 0.5)  # Tuple HSL representation

Alternatively, we can temporarily change the default color format project-wide so that new
palettes default to it:

>>> from colorir import config, PYGAME_COLOR_FORMAT
>>> config.DEFAULT_COLOR_FORMAT = PYGAME_COLOR_FORMAT  # Change default format to a pre-defined PyGame-compatible color format
>>> pygame_palette = Palette(red=(255, 0, 0), green="#00ff00")
>>> pygame_palette.red
RGB(255, 0, 0)
>>> pygame_palette.green
RGB(0, 255, 0)  # The green hex code is now converted to RGB format

It is worth noting that all color classes inherit either ``tuple`` or ``str``, meaning that
no conversion is needed when passing them to other frameworks such as PyGame, Kivy and HTML embedding
templates like Jinja.

For more information, see the :doc:`examples` and consult colorir's :doc:`api`.