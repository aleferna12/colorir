from . import config
from .color_format import ColorFormat
from .color import ColorLike, random_color, HSV


class SwatchBook:
    """Class that handles anonymous indexed colors."""
    def __init__(self,
                 name: str = None,
                 color_format: ColorFormat = None,
                 **colors: ColorLike):
        if color_format is None:
            color_format = config.DEFAULT_COLOR_FORMAT

        self.name = name
        self._color_format = color_format
        self._color_stack = []
        for color in colors:
            self.add(color)

    # TODO: doc
    @classmethod
    def new_complementary(cls,
                          n: int,
                          color: ColorLike = None,
                          name: str = None,
                          color_format: ColorFormat = None):
        swatches = cls(name=name, color_format=color_format)
        if color is None:
            hsv = random_color(color_format=ColorFormat(HSV, max_h=360))
        else:
            hsv = swatches.color_format.format(color).hsv(max_h=360)

        step = 360 / n
        for i in range(n):
            hue = (hsv[0] + i * step) % 360
            swatches.add(HSV(hue, hsv[1], hsv[2]))
        return swatches

    # TODO: doc
    @classmethod
    def new_analogous(cls,
                      n: int,
                      sections=12,
                      start=0,
                      color: ColorLike = None,
                      name: str = None,
                      color_format: ColorFormat = None):
        if n > sections:
            raise ValueError("'n' parameter cannot be larger than 'sections' parameter")
        if start == 0:
            first = -int(n/2)
            iterator = range(first, first + n)
        elif start == 1:
            iterator = range(n)
        elif start == -1:
            iterator = range(-n + 1, 1)
        else:
            raise ValueError("'starting_point' must be either 0, 1 or -1")

        swatches = cls(name=name, color_format=color_format)
        if color is None:
            hsv = random_color(color_format=ColorFormat(HSV, max_h=360))
        else:
            hsv = swatches.color_format.format(color).hsv(max_h=360)

        step = 360 / sections
        for index, i in enumerate(iterator):
            hue = (hsv[0] + i * step) % 360
            swatches.add(HSV(hue, hsv[1], hsv[2]))
        return swatches
    
    @property
    def colors(self):
        """colors: A list of all color values currently stored in the :class:`SwatchBook`.

        Equivalent to :code:`list(SwatchBook())`
        """
        return list(self._color_stack)

    @property
    def color_format(self):
        """color_format: Color format specifying how the colors of this :class:`SwatchBook` are
        stored.
        """
        return self._color_format

    # color_format could be used to build a color on every SwatchBook[color] call, but that is
    # computationally intensive. That's why the colors are stored as ready objects and are
    # re-created if needed
    @color_format.setter
    def color_format(self, value):
        self._color_stack = [value._from_rgba(color._rgba) for color in self._color_stack]
        self._color_format = value

    def __getitem__(self, item: int):
        return self._color_stack[item]

    def add(self, color: ColorLike):
        self._color_stack.append(self.color_format.format(color))

    def remove(self):
        self._color_stack.pop()

    def update(self, index: int, color: ColorLike):
        self._color_stack[index] = self.color_format.format(color)

    # TODO:
    #   save
    #   load