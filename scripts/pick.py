#!/usr/bin/env python3
import argparse
import json
import math
import os
import shutil
from pathlib import Path

THEMES = {
    "nord": ["#2e3440", "#3b4252", "#88c0d0", "#81a1c1", "#5e81ac"],
    "gruvbox": ["#282828", "#cc241d", "#98971a", "#d79921", "#458588", "#d65d0e"],
    "catppuccin": ["#1e1e2e", "#89b4fa", "#cba6f7", "#f38ba8", "#a6e3a1"],
    "dracula": ["#282a36", "#bd93f9", "#ff79c6", "#8be9fd", "#50fa7b"],
    "solarized": ["#002b36", "#073642", "#268bd2", "#2aa198", "#b58900"],
}


def hex_to_lab(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92

    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.00000
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    f = lambda t: t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16 / 116)
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(c1: tuple[float, float, float], c2: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def score_wallpaper(palette: list[dict], targets_lab: list[tuple[float, float, float]]) -> float:
    valid = [c for c in palette if c.get("share", 0) > 0.02]
    if not valid:
        return float("inf")
    total_score = 0.0
    for target in targets_lab:
        best = min(
            delta_e(target, hex_to_lab(entry["hex"])) / (entry["share"] ** 0.5)
            for entry in valid
        )
        total_score += best
    return total_score / len(targets_lab)


def main():
    root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description="Busca wallpapers por cor ou tema.")
    parser.add_argument("-c", "--color", nargs="+", help="Cor(es) em Hex (ex: #88c0d0 #2e3440)")
    parser.add_argument("-t", "--theme", choices=THEMES.keys(), help="Paleta predefinida")
    parser.add_argument("--cat", help="Filtrar por categoria (photography, illustration, minimal, retro-pixel, abstract-3d)")
    parser.add_argument("-n", "--limit", type=int, default=20, help="Quantidade de resultados")
    parser.add_argument("--dir", help="Cria pasta temporária com symlinks dos resultados")
    parser.add_argument("--abs", action="store_true", help="Imprime caminhos absolutos")
    parser.add_argument("--db", default=str(root / "wallpapers.json"), help="Caminho do JSON")
    args = parser.parse_args()

    hex_targets = args.color or (THEMES[args.theme] if args.theme else None)
    if not hex_targets:
        parser.error("Informe --color ou --theme.")

    targets_lab = [hex_to_lab(c) for c in hex_targets]
    data = json.loads(Path(args.db).read_text())

    if args.cat:
        data = [item for item in data if item.get("category") == args.cat]

    ranked = sorted(
        data,
        key=lambda item: score_wallpaper(item.get("palette", []), targets_lab),
    )[: args.limit]

    if args.dir:
        out_dir = Path(args.dir)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        for idx, item in enumerate(ranked, 1):
            src = (root / item["path"]).resolve()
            os.symlink(src, out_dir / f"{idx:03d}_{src.name}")
        print(out_dir)
    else:
        for item in ranked:
            print((root / item["path"]).resolve() if args.abs else item["path"])


if __name__ == "__main__":
    main()
