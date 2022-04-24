# Setup
from colorir import config
config.DEFAULT_PALETTES_DIR = "ex_palettes"

# Code
import turtle
from colorir import Palette

colors = Palette.load("basic")

turtle.color(colors.red)  # Grab the color red from our palette and paint the turtle with it
for _ in range(4):
    turtle.forward(200)
    turtle.left(90)
turtle.done()