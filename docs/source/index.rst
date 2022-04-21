Welcome to colorir's documentation!
=====================================

API
---

.. toctree::

	palette
	color
	gradient

What is colorir?
----------------

colorir is a package developed to unify your workflow with colors across different projects.

With colorir you can:

- Keep a unified selection of colors you like and use them in your different projects
- Use these colors directly as input for other graphical or web frameworks
- Easily convert between different color systems and formats
- Create gradients between colors and sample from them
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

Now to the fun part!

For this example we will assume that you are building an amazing game in PyGame, for which you'll need, of course, equally amazing colors!

For starters, we will load one of the palettes that come with colorir for convenience (don't worry, we will see how to create our own palettes later):

.. code-block:: python

	from colorir import Palette
	colors = Palette.load("basic")

The "basic" palette contains colors like blue, green, black etc.

That's it! We are done and ready to use the colors from our palettes now:

.. code-block:: python

	import pygame
	pygame.init()
	screen = pygame.display.set_mode((720, 480))
