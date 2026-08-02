#!/usr/bin/env python3
"""
build.py — Creature Codex book generator
=========================================
Reads a creature codex folder containing a config.toml and sources/*.toml files,
then regenerates all Patchouli JSON files for the series.

Usage:
    python3 build.py creature_codex

Each book (t0-t5) contains 3 categories:
  - Monture (mounts): only in books t1-t5
  - Animali (animals): all books
  - Pesci (fishes): all books

Generated output:
    creature_codex_t0/  →  animals + fishes (tier 0)
    creature_codex_t1/  →  mounts + animals + fishes (tiers 0-1)
    ... up to creature_codex_t5/
"""

import json
import os
import sys
import tomllib
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def slug(name: str) -> str:
    """Convert a name to a filesystem-safe slug."""
    return (
        name.lower()
        .replace(" ", "_")
        .replace("'", "")
        .replace("\u2019", "")
        .replace("\u2018", "")
        .replace("\u00e0", "a").replace("\u00e8", "e").replace("\u00e9", "e")
        .replace("\u00ec", "i").replace("\u00f2", "o").replace("\u00f9", "u")
    )


def description_to_patchouli(raw: str) -> str:
    """
    Convert a plain multiline description into a Patchouli text string.
    Blank lines between paragraphs become $(br2).
    """
    lines = [line.strip() for line in raw.strip().splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if line == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    return "$(br2)".join(paragraphs)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
        f.write("\n")



def load_config(series_dir: Path) -> dict:
    config_path = series_dir / "config.toml"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Validate required top-level keys
    for key in ("output_prefix", "num_tiers", "namespace", "category", "tier", "book"):
        if key not in config:
            print(f"ERROR: config.toml is missing key '{key}'", file=sys.stderr)
            sys.exit(1)

    config["num_tiers"] = int(config["num_tiers"])

    # Build lookup dicts
    config["_category_map"] = {c["id"]: c for c in config["category"]}
    config["_tier_map"] = {t["num"]: t for t in config["tier"]}
    config["_book_map"] = {b["num"]: b for b in config["book"]}

    return config


def load_sources(series_dir: Path, config: dict) -> list[dict]:
    """
    Load source files from the nested directory structure:
        sources/<type>/<tier>/<creature>.toml

    Type and tier are inferred from the folder hierarchy.
    """
    sources_dir = series_dir / "sources"
    if not sources_dir.is_dir():
        print(f"ERROR: {sources_dir} directory not found", file=sys.stderr)
        sys.exit(1)

    num_tiers = config["num_tiers"]
    valid_types = set(config["_category_map"].keys())

    entries = []
    errors = []

    # Scan each type subfolder (mounts, animals, fishes)
    for type_dir in sorted(sources_dir.iterdir()):
        if not type_dir.is_dir():
            continue

        creature_type = type_dir.name
        if creature_type not in valid_types:
            print(f"  WARNING: skipping unknown type folder '{creature_type}'", file=sys.stderr)
            continue

        # Scan each tier subfolder within the type
        for tier_dir in sorted(type_dir.iterdir()):
            if not tier_dir.is_dir():
                continue

            # Parse tier number from folder name
            try:
                tier = int(tier_dir.name)
            except ValueError:
                print(f"  WARNING: skipping non-numeric tier folder '{tier_dir.name}' in {creature_type}/", file=sys.stderr)
                continue

            if tier not in range(0, num_tiers):
                errors.append(f"  ERROR: tier {tier} in {creature_type}/ is out of range (must be 0-{num_tiers - 1})")
                continue

            # Validate: tier 0 should not have mounts
            if tier == 0 and creature_type == "mounts":
                errors.append(f"  ERROR: mounts cannot be in tier 0")
                continue

            # Load each .toml file in this tier folder
            for toml_file in sorted(tier_dir.glob("*.toml")):
                with open(toml_file, "rb") as f:
                    data = tomllib.load(f)

                required = {"name", "sortnum", "icon", "image", "description"}
                missing = required - data.keys()
                if missing:
                    errors.append(f"  ERROR: {toml_file.name} is missing fields: {missing}")
                    continue

                data["tier"] = tier
                data["type"] = creature_type
                data["_file"] = toml_file.name
                data["_path"] = toml_file.relative_to(series_dir)
                entries.append(data)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    return entries


def build_book_json(book_meta: dict) -> dict:
    return {
        "name":          book_meta["name"],
        "landing_text":  book_meta["landing_text"],
        "subtitle":      book_meta["subtitle"],
        "pamphlet":      False,
        "show_progress": False,
        "creative_tab":  "minecraft:transportation",
    }


def build_category_json(cat_meta: dict) -> dict:
    return {
        "name":        cat_meta["name"],
        "description": cat_meta["description"],
        "icon":        cat_meta["icon"],
        "sortnum":     cat_meta.get("sortnum", 0),
    }


def build_entry_json(entry: dict, category_id: str, namespace: str) -> dict:
    description = description_to_patchouli(entry["description"])
    return {
        "name":     entry["name"],
        "sortnum":  entry["sortnum"],
        "icon":     entry["icon"],
        "category": f"{namespace}:{category_id}",
        "pages": [
            {
                "type":    "patchouli:poster_top",
                "drawing": entry["image"],
                "text":    "",
            },
            {
                "type": "text",
                "text": description,
            },
        ],
    }


TEMPLATE_CONTENT = {
    "drawing.json": {
        "components": [
            {"type": "patchouli:text",  "x": 0,  "y": -4,  "text": "#text"},
            {"type": "patchouli:image", "image": "#drawing",
             "x": -6, "y": -10, "u": 0, "v": 0,
             "texture_width": 124, "texture_height": 162,
             "width": 124, "height": 162, "scale": 1},
        ]
    },
    "poster.json": {
        "components": [
            {"type": "patchouli:text",  "x": 0, "y": -4, "text": "#text"},
            {"type": "patchouli:image", "image": "#drawing",
             "x": 6, "y": 20, "u": 0, "v": 0,
             "texture_width": 128, "texture_height": 128,
             "width": 128, "height": 128, "scale": 0.8},
        ]
    },
    "poster2.json": {
        "components": [
            {"type": "patchouli:text",  "x": 0,   "y": -4,  "text": "#text"},
            {"type": "patchouli:image", "image": "#drawing",
             "x": 6, "y": 21, "u": 0, "v": 0,
             "texture_width": 128, "texture_height": 128,
             "width": 128, "height": 128, "scale": 0.8},
            {"type": "patchouli:text",  "x": 0,   "y": 126, "text": "#text2"},
        ]
    },
    "poster_bottom.json": {
        "components": [
            {"type": "patchouli:text",  "x": 0, "y": -4, "text": "#text"},
            {"type": "patchouli:image", "image": "#drawing",
             "x": 6, "y": 40, "u": 0, "v": 0,
             "texture_width": 128, "texture_height": 128,
             "width": 128, "height": 128, "scale": 0.8},
        ]
    },
    "poster_top.json": {
        "components": [
            {"type": "patchouli:text",  "x": 0, "y": 97, "text": "#text"},
            {"type": "patchouli:image", "image": "#drawing",
             "x": 6, "y": -6, "u": 0, "v": 0,
             "texture_width": 128, "texture_height": 128,
             "width": 128, "height": 128, "scale": 0.8},
        ]
    },
    "itemshow.json": {
        "components": [
            {"type": "patchouli:image", "image": "#drawing",
             "x": 6, "y": -6, "u": 0, "v": 0,
             "texture_width": 128, "texture_height": 128,
             "width": 128, "height": 128, "scale": 0.8},
            {"type": "patchouli:item", "item": "#item1", "x": 25, "y": 132},
            {"type": "patchouli:item", "item": "#item2", "x": 50, "y": 132},
            {"type": "patchouli:item", "item": "#item3", "x": 75, "y": 132},
            {"type": "patchouli:text", "x": 0, "y": 98, "text": "#text"},
        ]
    },
}


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 build.py <series_folder>", file=sys.stderr)
        print("Example: python3 build.py creature_codex", file=sys.stderr)
        sys.exit(1)

    series_name = sys.argv[1]
    series_dir = SCRIPT_DIR / series_name
    if not series_dir.is_dir():
        print(f"ERROR: series folder '{series_dir}' not found", file=sys.stderr)
        sys.exit(1)

    config = load_config(series_dir)
    output_prefix = config["output_prefix"]
    num_tiers = config["num_tiers"]
    namespace = config["namespace"]
    category_map = config["_category_map"]
    tier_map = config["_tier_map"]
    book_map = config["_book_map"]

    print(f"Loading sources from {series_dir}/sources/...")
    entries = load_sources(series_dir, config)
    print(f"  Found {len(entries)} entries.")

    for book_num in range(0, num_tiers):
        book_dir = SCRIPT_DIR / f"{output_prefix}_t{book_num}"
        en_us    = book_dir / "en_us"
        print(f"\nBuilding {output_prefix}_t{book_num}/")

        # book.json
        write_json(book_dir / "book.json", build_book_json(book_map[book_num]))

        # Templates
        for tpl_name, tpl_data in TEMPLATE_CONTENT.items():
            write_json(en_us / "templates" / tpl_name, tpl_data)

        # For each category type, create category + entries
        sortnum_counter = 0
        for cat_meta in category_map.values():
            cat_id = cat_meta["id"]

            # Skip mounts category for book t0
            if book_num == 0 and cat_id == "mounts":
                continue

            # Write category file
            write_json(
                en_us / "categories" / f"{cat_id}.json",
                build_category_json(cat_meta),
            )

            # Get entries for this category: tier <= book_num AND type matches
            cat_entries = [
                e for e in entries
                if e["tier"] <= book_num and e["type"] == cat_id
            ]

            # Write entry files
            for entry in cat_entries:
                file_slug = slug(entry["name"])
                entry_path = en_us / "entries" / cat_id / f"{file_slug}.json"
                write_json(entry_path, build_entry_json(entry, cat_id, namespace))
                print(f"  [{cat_id.upper():>8}] {entry['name']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
