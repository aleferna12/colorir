import pygame as pg
from colorir import Palette, PYGAME_COLOR_FORMAT
# Since pygame doesn't accept hex strings, we will change the color format of our palette to match
colors = Palette.load("turtles", color_format=PYGAME_COLOR_FORMAT)

pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((720, 480))
while True:
    clock.tick()
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quit()
    screen.fill(colors.dreamblue)  # Draw background
    # Draw legs
    pg.draw.rect(screen, colors.woodbrown, (300, 200, 75, 200))
    pg.draw.rect(screen, colors.woodbrown, (500, 200, 75, 200))
    # Draw shell
    pg.draw.ellipse(screen, colors.swampgreen, (275, 100, 325, 200))
    # Draw head
    pg.draw.circle(screen, colors.swampgreen, (275, 100), 70)
    pg.display.update()
