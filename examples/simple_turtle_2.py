import turtle
from colorir import Palette

colors = Palette.load("basic")
colors.add("dreamblue", "#4287f5")
colors.add("swampgreen", "#096b1c")
colors.add("woodbrown", "#8c6941")

turtle.pensize(3)
n_colors = len(colors)  # Get how many colors we currently have
for color in colors:  # Iterate over every color value
    turtle.color(color)
    turtle.forward(800 / n_colors)
    turtle.left(360 / n_colors)
turtle.done()