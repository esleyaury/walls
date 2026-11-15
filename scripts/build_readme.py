#!/usr/bin/env python3
import json
import random
from collections import defaultdict
from pathlib import Path

CATEGORY_TITLES = {
    "photography": "Photography",
    "illustration": "Illustration & Anime",
    "minimal": "Minimal & Geometric",
    "retro-pixel": "Retro & Pixel Art",
    "abstract-3d": "Abstract & 3D",
}


def render_grid(items: list[dict], cols: int = 3) -> str:
    rows = []
    for i in range(0, len(items), cols):
        chunk = items[i : i + cols]
        cells = "".join(
            f'<td align="center"><a href="{w["path"]}"><img src="{w["path"]}" width="280"/></a></td>'
            for w in chunk
        )
        rows.append(f"  <tr>{cells}</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main():
    root = Path(__file__).resolve().parent.parent
    random.seed(42)
    data = json.loads((root / "wallpapers.json").read_text())

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for item in data:
        by_cat[item["category"]].append(item)

    lines = [
        "# walls",
        "",
        f"Curated wallpaper collection (**{len(data)}** images) organized by visual style, with perceptual color search (CIELAB) via CLI.",
        "",
        "## Quick CLI Search",
        "",
        "```fish",
        "# Search by theme preset (nord, gruvbox, catppuccin, dracula, solarized)",
        "python scripts/pick.py -t nord -n 20 --abs | xargs gwenview",
        "",
        "# Search by hex color inside a specific style folder",
        "python scripts/pick.py -c '#2d3b2e' --cat photography -n 15",
        "",
        "# Materialize a temporary symlink folder to browse visually",
        "python scripts/pick.py -t gruvbox -n 40 --dir /tmp/walls-gruvbox",
        "```",
        "",
        "## Categories",
        "",
    ]

    for cat, title in CATEGORY_TITLES.items():
        items = by_cat.get(cat, [])
        if not items:
            continue
        sample = random.sample(items, min(6, len(items)))
        lines.extend([
            f"### [{title}]({cat}/) ({len(items)})",
            "",
            render_grid(sample, cols=3),
            "",
        ])

    lines.extend([
        "## Credits",
        "",
        "Curated and reorganized from [`dharmx/walls`](https://github.com/dharmx/walls). All artworks belong to their respective creators.",
        "",
    ])

    (root / "README.md").write_text("\n".join(lines))
    print("README.md gerado com sucesso.")


if __name__ == "__main__":
    main()
