from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '400')
from kivy.app import App
from kivy.graphics import Ellipse, Rectangle, Color
from kivy.uix.widget import Widget
from colorir import config, KIVY_COLOR_FORMAT, Grad, HSV

# Define the default color format to work with kivy
config.DEFAULT_COLOR_FORMAT = KIVY_COLOR_FORMAT

# You can play around with these variables to change the appearance of the color wheel
ELLIPSE_STEPS = 150
ELLIPSE_SEGMENTS = 50


class WheelScreen(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        iter_angle = 360 / ELLIPSE_STEPS
        with self.canvas:
            Rectangle(pos=(0, 0), size=(400, 400))  # Draw background

            for j in range(ELLIPSE_SEGMENTS + 1):
                s = 1 - j / ELLIPSE_SEGMENTS
                # Sample colors throughout the hue range for this saturation
                outer_colors = Grad(
                    [HSV(0, s, 1), HSV(355, s, 1)],
                    color_sys=HSV
                ).n_colors(ELLIPSE_STEPS)
                for i, color in enumerate(outer_colors):
                    Color(*color)
                    width = 400 * (ELLIPSE_SEGMENTS - j) / ELLIPSE_SEGMENTS
                    height = 400 * (ELLIPSE_SEGMENTS - j) / ELLIPSE_SEGMENTS
                    Ellipse(
                        pos=(200 - width / 2, 200 - height / 2),
                        size=(width, height),
                        angle_start=i * iter_angle,
                        angle_end=(i + 1) * iter_angle
                    )


class WheelApp(App):
    def build(self):
        return WheelScreen()


app = WheelApp()
app.run()
