from colorir import *


def color_div(color, cname):
    title = f"{cname} - {color.hex()}" if cname else f"{color.hex()}"
    return (f'<div data-hexcode="{color.hex()}" title="{title}" '
            f'onclick="navigator.clipboard.writeText(this.dataset.hexcode)" '
            f'class="swatch" style="background-color: {color.hex()};"></div>')


def main():
    pals = {name: Palette.load(name) for name in find_palettes(kind=Palette)}
    for name in find_palettes(kind=StackPalette):
        if name in pals:
            name += "_sp"
        pals[name] = StackPalette.load(name)

    for name, pal in pals.items():
        html = '<div class="palette">'
        if isinstance(pal, Palette):
            cnames = pal.color_names
        else:
            cnames = (False for _ in range(len(pal)))
        for color, cname in zip(pal, cnames):
            html += color_div(color, cname)

        html += "</div>"

        with open(f"_static/html/palettes/{name}.html", "w") as file:
            file.write(html)

    named = '<div class="palette">'
    pal = Palette.load()
    sort_key = hue_sort_key(8)
    for cname in sorted(pal.color_names, key=lambda cn: sort_key(pal[cn])):
        named += color_div(pal[cname], cname)
    named += "</div>"
    with open(f"_static/html/named_colors.html", "w") as file:
        file.write(named)

    all_str = '<div class="palette">'
    allc = set(StackPalette.load() & pal.to_stackpalette())
    for color in sorted(allc, key=sort_key):
        all_str += color_div(color, False)
    all_str += "</div>"
    with open(f"_static/html/all_colors.html", "w") as file:
        file.write(all_str)


if __name__ == "__main__":
    main()
