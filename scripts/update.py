#!/usr/bin/env python3
import hashlib
import json
import re
import shutil
from pathlib import Path
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
CATEGORIES = ["photography", "illustration", "minimal", "retro-pixel", "abstract-3d"]

KEYWORD_RULES = [
    ("retro-pixel", {"pixel", "8-bit", "16-bit", "retro", "synthwave", "vaporwave", "crt", "arcade"}),
    ("minimal", {"minimal", "gradient", "geometric", "logo", "symbol", "lines", "shapes"}),
    ("abstract-3d", {"abstract", "3d", "render", "fractal", "pattern", "texture", "waves", "surreal", "glitch"}),
    ("illustration", {"anime", "drawing", "painting", "illustration", "sketch", "cartoon", "character", "girl", "boy", "samurai", "dragon", "manga"}),
    ("photography", {"photo", "street", "forest", "ocean", "city", "sky", "clouds", "sunset", "snow", "lake", "beach", "building", "road", "mountain", "river"}),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_by_name(stem: str) -> str:
    tokens = set(re.findall(r"[a-z0-9-]+", stem.lower()))
    for target, keywords in KEYWORD_RULES:
        if tokens & keywords:
            return target
    return "review"


def extract_palette(path: Path, n_colors: int = 8) -> list[dict]:
    with Image.open(path) as img:
        thumb = img.convert("RGB")
        thumb.thumbnail((128, 128))
        quantized = thumb.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
        palette_raw = quantized.getpalette() or []
        counts = sorted(quantized.getcolors() or [], reverse=True)
        total = sum(c for c, _ in counts) or 1

        colors = []
        for count, idx in counts:
            r, g, b = palette_raw[idx * 3 : idx * 3 + 3]
            colors.append({
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "share": round(count / total, 3),
            })
        return colors


def process_inbox(root: Path, known_hashes: set[str]) -> tuple[int, int, int]:
    inbox_dir = root / "inbox"
    if not inbox_dir.exists():
        return 0, 0, 0

    routed, to_review, dupes = 0, 0, 0
    for path in sorted(inbox_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue

        file_hash = sha256_file(path)
        if file_hash in known_hashes:
            path.unlink()
            dupes += 1
            continue

        target_cat = classify_by_name(path.stem)
        dest_dir = root / target_cat
        dest_dir.mkdir(parents=True, exist_ok=True)

        candidate = dest_dir / path.name
        if candidate.exists():
            candidate = dest_dir / f"{path.stem}-{file_hash[:6]}{path.suffix.lower()}"

        shutil.move(str(path), str(candidate))
        known_hashes.add(file_hash)

        if target_cat == "review":
            to_review += 1
        else:
            routed += 1

    return routed, to_review, dupes


def main():
    root = Path(__file__).resolve().parent.parent
    db_path = root / "wallpapers.json"

    existing = {}
    if db_path.exists():
        for item in json.loads(db_path.read_text()):
            existing[item["hash"]] = item

    routed, to_review, dupes = process_inbox(root, set(existing.keys()))

    updated_manifest = []
    added, moved = 0, 0

    for cat in CATEGORIES:
        cat_dir = root / cat
        if not cat_dir.exists():
            continue

        for path in sorted(cat_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
                continue

            rel_path = path.relative_to(root).as_posix()
            file_hash = sha256_file(path)

            if file_hash in existing:
                entry = existing[file_hash]
                if entry["path"] != rel_path:
                    moved += 1
                entry["path"] = rel_path
                entry["category"] = cat
                updated_manifest.append(entry)
            else:
                added += 1
                updated_manifest.append({
                    "path": rel_path,
                    "hash": file_hash,
                    "category": cat,
                    "tags": [],
                    "source": "own",
                    "palette": extract_palette(path),
                })

    db_path.write_text(json.dumps(updated_manifest, indent=2, ensure_ascii=False))

    if routed or to_review or dupes:
        print(f"Inbox -> Categorizados: {routed} | Para review: {to_review} | Duplicatas removidas: {dupes}")
    print(f"Índice -> Total: {len(updated_manifest)} | Movidos: {moved} | Novos: {added}")

    review_dir = root / "review"
    if review_dir.exists():
        left = [p for p in review_dir.iterdir() if p.is_file()]
        if left:
            print(f"Aviso: {len(left)} arquivos aguardando triagem em review/")


if __name__ == "__main__":
    main()
