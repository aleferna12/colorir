import numpy as np
import matplotlib.pyplot as plt
from colorir import *

fig, axes = plt.subplots(2, 2)
imdata = np.outer(np.linspace(-1, 1, 100), np.linspace(-1, 1, 100))
colors = Palette.load()  # Load all colors available

# Divergent purple and yellow gradient
grad = PolarGrad([colors.cyan, colors.eggyolk, colors.magenta])
im1 = axes[0, 0].imshow(imdata, cmap=grad.to_cmap())
plt.colorbar(im1)
axes[0, 0].set_title("Divergent purple and blue")

# Non-linear gradient
grad = PolarGrad(grad.colors, color_coords=[0, 0.6, 1])  # Place the yellow slightly closer to the end of the gradient
im2 = axes[0, 1].imshow(imdata, cmap=grad.to_cmap())
plt.colorbar(im2)
axes[0, 1].set_title("Non-linear gradient")

# Discrete colormap from palette
pal = StackPalette.load("spectral").resize(15)  # Loads spectral palette and resize it to get 11 color categories
im3 = axes[1, 0].imshow(imdata, cmap=pal.to_cmap())
plt.colorbar(im3)
axes[1, 0].set_title("Discrete spectral")

grad = Grad(grad.colors, domain=[-1, 1])
grad = StackPalette([grad((1 - p) ** 2) for p in np.linspace(-1, 1, 100)])
im4 = axes[1, 1].imshow(imdata, cmap=grad.to_cmap())
plt.colorbar(im4)
axes[1, 1].set_title("Discrete spectral")

fig.tight_layout()
plt.show()
