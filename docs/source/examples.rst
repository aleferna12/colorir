Examples
========

After installing colorir, example applications can be executed from the shell with:

.. code-block:: shell

	$ python -m colorir <app>

Where `app` is one of:

- `simple_turtle_1`_
- `simple_turtle_2`_
- `simple_pygame`_
- `color_picker`_
- `color_wheel`_

Simple Example: Sharing Colors Between Turtle and PyGame Projects
-----------------------------------------------------------------

In this example we will combine python's turtle package with colorir to draw basic shapes.

For starters, we will load one of the palettes that come with colorir for convenience:

.. code-block:: python

	from colorir import Palette
	colors = Palette.load("basic")

The "basic" palette contains colors like blue, green, black etc.

That's it! We are done and ready to use our basic colors:

.. _simple_turtle_1:

.. literalinclude:: ../../colorir/examples/simple_turtle_1.py

You should now hopefully see a red square in your screen.

Let's modify our example to add some personal favorite colors to our `colors` object:

.. code-block:: python

	colors = Palette.load("basic")
	colors.add("dreamblue", "#4287f5")
	colors.add("swampgreen", "#096b1c")
	colors.add("woodbrown", "#8c6941")

This should be enough. Now, instead of a red square, we can draw more interesting stuff:

.. _simple_turtle_2:

.. literalinclude:: ../../colorir/examples/simple_turtle_2.py

You should see something resembling this (but with no text):

.. image:: images/simple_turtle_2.png
	:width: 300px

Ok! We are done with the turtles for right now. We should save our colors so we can use them next time we feel like drawing turtles:

.. code-block:: python

	colors.name = "turtles" # First we give the palette a name
	colors.save() # Then save it

A few weeks later we suddenly have a brilliant idea: what if we could draw actual turtles, instead of the stupid arrow we've been pretending to be a turtle?

But we also would like to keep the colors from our last project since we took so long choosing turtle-fitting colors.

Let's put that on paper with PyGame:

.. _simple_pygame:

.. literalinclude:: ../../colorir/examples/simple_pygame.py

.. image:: images/simple_pygame.png
	:width: 300px

Ha! And Mom said I wouldn't make money with NFTs...

Anyway, I hope you could get I very basic idea of how to use colorir. For more examples and insights on how to use this package, see the documentation of each module and the other examples bellow.

.. _color_picker:

Color Picker with Tkinter
-------------------------

A simple color picker that shows all the palettes available on our current directory (+ the built-in palettes) and copies the names of a color to the clipboard when we click on it.

Just like with any other example, the color picker can be executed with:

.. code-block:: shell

	$ python -m colorir color_picker

.. literalinclude:: ../../colorir/examples/color_picker.py

.. _color_wheel:

Color Wheel with Kivy
---------------------

A color wheel viewer (not a color picker) showcasing :class:`~colorir.gradient.Grad`.

.. literalinclude:: ../../colorir/examples/color_wheel.py

.. image:: images/color_wheel.png
	:width: 300px