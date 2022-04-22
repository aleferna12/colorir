import turtle
from colorir import Palette

colors = Palette.load("basic")

turtle.color(colors.red)  # Grab the color red from our palette
for _ in range(4):
    turtle.forward(200)
    turtle.left(90)
turtle.done()