from typing import Type
# color is a common parameter name and we cant use relative imports due to circular dependencies
import color as colorm


class ColorFormat:
    def __init__(self, color_sys: Type["colorm.ColorBase"], **kwargs):
        self.color_sys = color_sys
        self._format_params = kwargs

    def __getattr__(self, item):
        # __getattr__ is called only when super().__getattribute__ fails
        try:
            return self._format_params[item]
        except LookupError as e:
            raise AttributeError(f"AttributeError: '{self.__class__.__name__}' object has no "
                                 f"attribute '{item}'") from e

    def __call__(self, *args, **kwargs):
        return self.new_color(*args, **kwargs)

    def __repr__(self):
        opener_str = f"{self.__class__.__name__}("
        arguments_str = f"color_sys={self.color_sys.__name__}"
        for param, param_v in self._format_params.items():
            arguments_str += f",\n{' ' * len(opener_str)}{param}={param_v.__repr__()}"
        return f"{opener_str}{arguments_str})"

    # TODO: Doc
    def new_color(self, *args, **kwargs) -> "colorm.ColorBase":
        kwargs.update(self._format_params)
        return self.color_sys(*args, **kwargs)

    def _from_rgba(self, rgba):
        # Factory method to be called when reading the palette files or reconstructing colors
        return self.color_sys._from_rgba(rgba, **self._format_params)

    def format(self, color: colorm.ColorLike) -> "colorm.ColorBase":
        """Tries to format the `color` parameter into this format."""
        if isinstance(color, colorm.ColorBase):
            return self._from_rgba(color._rgba)
        elif isinstance(color, str):
            # Try to preserve formatting options
            if self.color_sys == colorm.HexRGB:
                return self.new_color(color)
            # Fallback to HexRGB default args
            return self._from_rgba(colorm.HexRGB(color)._rgba)
        # Assume that the color space accepts multiple unnamed mandatory parameters for construction
        try:
            return self.new_color(*color)
        except Exception as e:
            raise ValueError(
                f"Failed to interpret '{color}' as a '{self.color_sys}'. Using colors defined in "
                f"the 'color' submodule as a parameter instead may help") from e


PYGAME_COLOR_FORMAT = ColorFormat(color_sys=colorm.sRGB, max_rgba=255, include_a=False)
KIVY_COLOR_FORMAT = ColorFormat(color_sys=colorm.sRGB, max_rgba=1, include_a=True)
WEB_COLOR_FORMAT = ColorFormat(color_sys=colorm.HexRGB, include_a=False)