import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from colorir import *

palettes = {name: Palette.load(name).to_stackpalette() for name in find_palettes(kind=Palette) if name != "css"}
for name in find_palettes(kind=StackPalette):
    dict_name = name
    if name in palettes:
        dict_name += " (stack palette)"
    palettes[dict_name] = StackPalette.load(name)
palettes = {k: palettes[k] for k in sorted(palettes)}
max_pal_size = max(len(pal) for pal in palettes.values())
carnival = StackPalette.load("carnival")

fig = make_subplots(2, 2)
for i in range(max_pal_size):
    fig.add_trace(go.Scatter(
        x=np.arange(50),
        y=np.random.random(50) + i * 2,
        line_width=1,
        marker_size=10,
        line_color=carnival[i % len(carnival)],
        marker_color=carnival[i % len(carnival)],
        showlegend=False,
        visible=i < len(carnival),
    ), row=1, col=1)
# We re-iterate to change the order in which the traces are added
for i in range(max_pal_size):
    fig.add_trace(go.Scatter(
        x=np.arange(20),
        y=np.random.random(20) * (1 - i/max_pal_size) + 2 + i/max_pal_size,
        stackgroup=0,
        line_color=carnival[i % len(carnival)],
        marker_color=carnival[i % len(carnival)],
        showlegend=False,
        visible=i < len(carnival),
    ), row=1, col=2)
for i in range(max_pal_size):
    markers = np.random.randint(3, 5)
    fig.add_trace(go.Scatter(
        x=np.arange(markers) + np.random.random(markers) + i,
        y=(np.random.random(markers) - 0.5) + np.random.random() * 4,
        line_width=3,
        marker_size=10,
        marker_line_width=2,
        line_color=carnival[i % len(carnival)],
        marker_color=carnival[i % len(carnival)],
        showlegend=False,
        visible=i < len(carnival),
    ), row=2, col=1)
fig.add_trace(go.Contour(
    z=[[None, None, None, 12, 13, 14, 15, 16],
       [None, 1, None, 11, None, None, None, 17],
       [None, 2, 6, 7, None, None, None, 18],
       [None, 3, None, 8, None, None, None, 19],
       [5, 4, 10, 9, None, None, None, 20],
       [None, None, None, 27, None, None, None, 21],
       [None, None, None, 26, 25, 24, 23, 22]],
    connectgaps=True,
    colorscale=Grad(carnival).to_plotly_colorscale(),
    showscale=False
), row=2, col=2)
fig.update_layout(width=700, height=700)

buttons = []
for pal_name, pal in palettes.items():
    buttons.append(go.layout.updatemenu.Button(
        label=pal_name,
        method="restyle",
        args=[{"marker.color": list(pal.resize(max_pal_size, repeat=True)),
               "line.color": list(pal.resize(max_pal_size, repeat=True)),
               "colorscale": [Grad(pal).to_plotly_colorscale()],
               "visible": [True] * len(pal) + [False] * (max_pal_size - len(pal))}],
    ))
fig.update_layout(updatemenus=[
    go.layout.Updatemenu(
        buttons=buttons,
        type='dropdown',
        direction='down',
        x=0.25, y=1.1,
        showactive=True,
        active=list(palettes).index("carnival")
    ),
    go.layout.Updatemenu(
        buttons=[
            go.layout.updatemenu.Button(
                args=[{"theme": "plotly_dark"}],
                label="Dark mode",
                method="relayout"
            )
        ],
        type="buttons",
        x=0.5, y=1.1,
        showactive=True,
    )
])
fig.show("browser")

# Line + scatter
