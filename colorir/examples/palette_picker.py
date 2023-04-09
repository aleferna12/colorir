import csv
import numpy as np
import plotly.graph_objs as go
from pathlib import Path
from plotly.io import templates as plotly_templates
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
carnival_colorscale = Grad(carnival).to_plotly_colorscale()

fig = make_subplots(
    4, 2,
    specs=[[{"type": "scatter"}, {"type": "violin"}],
           [{"type": "scatter"}, {"type": "contour"}],
           [{"type": "histogram"}, {"type": "surface"}],
           [{"type": "choropleth", "colspan": 2}, None]]
)

# We will refer to this list to determine how to restyle the trace when changing palettes
restyle = []
for i in range(max_pal_size):
    y = [i]
    for j in range(49):
        y.append(y[-1] + 2 * (np.random.random() - 0.5))
    fig.add_trace(go.Scatter(
        x=np.arange(50),
        y=y,
        line_width=1,
        marker_size=10,
        line_color=carnival[i % len(carnival)],
        marker_color=carnival[i % len(carnival)],
        showlegend=False,
        visible=i < len(carnival)
    ), row=1, col=1)
    restyle.append("dynamic_categ")

    fig.add_trace(go.Violin(
        x=np.random.standard_normal(20) - i / 2,
        y0=max_pal_size - i,
        orientation='h',
        side="positive",
        width=3,
        line_color=carnival[(max_pal_size - i) % len(carnival)],
        showlegend=False,
        visible=i < len(carnival),
        hoverinfo="skip"
    ), row=1, col=2)
    restyle.append("dynamic_categ")

locations = []
pop = []
lifeexp = []
gdppercapita = []
with open(Path(__file__).parent / "gapminder.csv") as file:
    for row in csv.DictReader(file.read().split("\n")[:-1]):
        locations.append(row["iso"])
        pop.append(int(row["pop"]))
        lifeexp.append(float(row["lifeExp"]))
        gdppercapita.append(float(row["gdpPercap"]))
fig.add_trace(go.Scatter(
    x=gdppercapita,
    y=lifeexp,
    mode="markers",
    marker=go.scatter.Marker(
        size=pop,
        sizemode="area",
        sizeref=max(pop) / 3600,
        color=np.random.choice(np.array(carnival), size=len(pop))
    ),
    showlegend=False
), row=2, col=1)
restyle.append("static_categ")
fig.update_xaxes(type="log", row=2, col=1)

fig.add_trace(go.Contour(
    z=[[None, None, None, 12, 13, 14, 15, 16],
       [None, 1, None, 11, None, None, None, 17],
       [None, 2, 6, 7, None, None, None, 18],
       [None, 3, None, 8, None, None, None, 19],
       [5, 4, 10, 9, None, None, None, 20],
       [None, None, None, 27, None, None, None, 21],
       [None, None, None, 26, 25, 24, 23, 22]],
    connectgaps=True,
    colorscale=carnival_colorscale,
    showscale=False,
), row=2, col=2)
restyle.append("colorscale")

fig.add_trace(go.Histogram2d(
    x=np.concatenate([np.random.beta(4, 2, 100000), np.random.beta(2, 4, 100000)]),
    y=np.concatenate([np.random.beta(4, 2, 100000), np.random.beta(2, 4, 100000)]),
    nbinsx=50,
    nbinsy=50,
    colorscale=carnival_colorscale,
    showscale=False
), row=3, col=1)
restyle.append("colorscale")
fig.update_xaxes(constrain="domain", row=3, col=1)
fig.update_yaxes(scaleanchor="x5", scaleratio=1, row=3, col=1)


with open(Path(__file__).parent / "surface_data.csv") as file:
    surface_data = list(csv.reader(file.read().split("\n")[:-1]))
surface_data = np.array(surface_data, dtype=float)
fig.add_trace(go.Surface(
    z=surface_data,
    contours=dict(z=dict(show=True, usecolormap=True)),
    colorscale=carnival_colorscale,
    showscale=False
), row=3, col=2)
fig.update_layout(scene=dict(
    xaxis=dict(showticklabels=False, title=""),
    yaxis=dict(showticklabels=False, title=""),
    zaxis=dict(showticklabels=False, title="")
))
restyle.append("colorscale")

fig.add_trace(go.Choropleth(
    locations=locations,
    z=gdppercapita,
    colorscale=carnival_colorscale,
    colorbar=go.choropleth.ColorBar(x=1.1, y=1, yanchor="top", tickvals=[], len=0.4)
), row=4, col=1)
restyle.append("colorscale")

# This is just a dummy trace to display the discrete palette as a colorbar
fig.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    marker_colorscale=Grad(carnival, discrete=True).to_plotly_colorscale(),
    marker_showscale=True,
    marker_colorbar=go.scatter.marker.ColorBar(y=1, yanchor="top", tickvals=[], len=0.4),
    showlegend=False
))
restyle.append("discrete_colorscale")

fig.update_xaxes(showticklabels=False)
fig.update_yaxes(showticklabels=False)
fig.update_layout(mapbox_zoom=8,
                  width=700,
                  height=1300)

buttons = []
for pal_name, pal in palettes.items():
    restyle_dict = {
        "marker.color": [None] * len(fig.data),
        "marker.colorscale": [None] * len(fig.data),
        "marker.colorbar": [None] * len(fig.data),
        "line.color": [None] * len(fig.data),
        "colorscale": [None] * len(fig.data),
        "visible": [True] * len(fig.data)
    }
    for i, trace in enumerate(fig.data):
        if restyle[i] == "dynamic_categ":
            color_index = int(i / 2)
            if color_index >= len(pal):
                restyle_dict["visible"][i] = False
            else:
                restyle_dict["marker.color"][i] = pal[color_index]
                restyle_dict["line.color"][i] = pal[color_index]
        elif restyle[i] == "static_categ":
            restyle_dict["marker.color"][i] = np.random.choice(np.array(pal), size=len(pop))
        elif restyle[i] == "colorscale":
            restyle_dict["colorscale"][i] = Grad(pal).to_plotly_colorscale()
        elif restyle[i] == "discrete_colorscale":
            restyle_dict["marker.colorscale"][i] = Grad(pal, discrete=True).to_plotly_colorscale()
            restyle_dict["marker.colorbar"][i] = go.scatter.marker.ColorBar(y=1, yanchor="top", tickvals=[], len=0.4)
    buttons.append(go.layout.updatemenu.Button(
        label=pal_name,
        method="restyle",
        args=[restyle_dict]
    ))

fig.update_layout(
    updatemenus=[
        go.layout.Updatemenu(
            buttons=buttons,
            type='dropdown',
            direction='down',
            x=0.4, y=1.1,
            showactive=True,
            active=list(palettes).index("carnival")
        ),
        go.layout.Updatemenu(
            buttons=[
                go.layout.updatemenu.Button(
                    # We have to index with the key because of some lazy access magic plotly implements
                    args=[{"template": plotly_templates[template]}],
                    label=template,
                    method="relayout"
                ) for template in sorted(plotly_templates)
            ],
            type='dropdown',
            direction='down',
            x=0.8, y=1.1,
            showactive=True,
            active=sorted(plotly_templates).index("plotly")
        ),
    ],
    annotations=[
        go.layout.Annotation(
            text="Palette:",
            font=dict(size=12),
            x=0,
            y=1.1,
            xref="paper",
            yref="paper",
            showarrow=False
        ),
        go.layout.Annotation(
            text="Template:",
            font=dict(size=12),
            x=0.55,
            y=1.1,
            xanchor="right",
            xref="paper",
            yref="paper",
            showarrow=False
        ),
    ]
)
fig.show("browser")
