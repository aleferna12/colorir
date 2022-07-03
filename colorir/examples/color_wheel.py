from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '400')
from kivy.app import App
from kivy.graphics import Ellipse, Color
from kivy.uix.widget import Widget
from colorir import config, KIVY_COLOR_FORMAT, RGBGrad, HSV, sRGB

# Define the default color format to work with kivy
config.DEFAULT_COLOR_FORMAT = KIVY_COLOR_FORMAT

# You can play around with these variables to change the appearance of the color wheel
ELLIPSE_STEPS = 180
ELLIPSE_SEGMENTS = 40


class WheelScreen(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        iter_angle = 360 / ELLIPSE_STEPS
        with self.canvas:
            for i in range(ELLIPSE_STEPS):
                # Use HUE to create the outermost color on the wheel
                outer_color = HSV(i * iter_angle, 1, 1)
                # Create a gradient from the outer color to white
                grad = RGBGrad([outer_color, sRGB(255, 255, 255)])
                # Enumerate over the segments of the step while creating new colors with the grad
                for j, color in enumerate(grad.n_colors(ELLIPSE_SEGMENTS, include_ends=True)):
                    Color(*color)
                    width = 400 * (ELLIPSE_SEGMENTS - j) / ELLIPSE_SEGMENTS
                    height = 400 * (ELLIPSE_SEGMENTS - j) / ELLIPSE_SEGMENTS
                    Ellipse(
                        pos=(200 - width / 2, 200 - height / 2),
                        size=(width, height),
                        angle_start=i * iter_angle,
                        angle_end=(i + 1) * iter_angle,
                    )


class WheelApp(App):
    def build(self):
        return WheelScreen()


app = WheelApp()
app.run()
