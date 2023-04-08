import numpy as np
import matplotlib.pyplot as plt
from colorir import *

fig, axes = plt.subplots(2, 2)
imdata = (np.outer(np.linspace(-1, 1, 100), np.linspace(-1, 1, 100)) + 1) / 2
cs = Palette.load()  # Load all colors available

# Discrete colormap from palette
pal = StackPalette.load("carnival").resize(8)  # Load the palette and resize it to get 8 color categories
ys = [np.random.random(10) + 1 for i in range(len(pal))]
axes[0, 0].stackplot(np.arange(10), *ys, colors=pal)
axes[0, 0].set_title("Stacked data")

# Discrete PuBu & GnBu
pubu = StackPalette.load("pubu")
gnbu = StackPalette.load("gnbu")
# Fuse palettes with the & operator
pal = pubu & gnbu[::-1]
# Make a discrete gradient from the palette
grad = Grad(pal.resize(13), discrete=True)
im1 = axes[0, 1].imshow(imdata, cmap=grad.to_cmap())
axes[0, 1].set_title("Discrete PuBu & GnBu")

# Divergent purple and yellow gradient
grad = PolarGrad([cs.cyan, cs.eggyolk, cs.magenta])
im2 = axes[1, 0].imshow(imdata, cmap=grad.to_cmap())
axes[1, 0].set_title("Divergent cyan magenta")

# Non-linear gradient
# Place the white closer to the end of the gradient instead of in the middle by setting 'color_coords'
grad = PolarGrad([cs.darkred, cs.white, cs.darkblue], color_coords=[0, 2 / 3, 1])
im3 = axes[1, 1].imshow(imdata, cmap=grad.to_cmap())
axes[1, 1].set_title("Non-linear gradient")

# Make stuff look good
axes[0, 0].set_aspect(1/2)
axes[0, 0].set_xlim([0, 9])
plt.colorbar(im1)
plt.colorbar(im2)
plt.colorbar(im3)

fig.tight_layout()
plt.show()
