"""
Modular script for updating walks data and managing GPX files.
Provides functions for:
- Loading and saving walks.yaml
- Assigning colors to walk folders
- Generating interactive maps
"""

import yaml
import folium
import gpxpy
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
WALKS_YAML = BASE_DIR / "data" / "walks.yaml"
GPX_FOLDER = BASE_DIR / "gpx"
MAP_DIR = BASE_DIR / "docs" / "_build" / "html" / "map"
FOLDER_COLORS_FILE = BASE_DIR / "data" / "folder_colors.yaml"
SITE_ROOT = "https://twotogether.github.io/uk-walks-tracker"

COLOR_PALETTE = [
    "#2E8B57",      # Sea green
    "#1E3A8A",      # Dark blue
    "#B8860B",      # Dark goldenrod
    "#DC143C",      # Crimson
    "#8B0000",      # Dark red
    "#8B008B",      # Dark magenta
    "#D35400",      # Dark orange
    "#C71585",      # Medium violet red
    "#3CB371",      # Medium sea green
    "#008B8B",      # Dark cyan
]


def load_folder_colors():
    """Load folder-to-color mapping from file."""
    if FOLDER_COLORS_FILE.exists():
        with open(FOLDER_COLORS_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_folder_colors(colors):
    """Save folder-to-color mapping to file."""
    with open(FOLDER_COLORS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(colors, f, sort_keys=False, allow_unicode=True)


def assign_colors_to_folders():
    """Scan GPX folder and assign colors to any new subfolders."""
    folder_colors = load_folder_colors()
    colors_updated = False

    # Get all subfolders in gpx/
    gpx_subfolders = set()
    for gpx_file in GPX_FOLDER.rglob("*.gpx"):
        gpx_rel = gpx_file.relative_to(GPX_FOLDER)
        folder_name = gpx_rel.parts[0]
        gpx_subfolders.add(folder_name)

    # Assign colors to new folders
    for folder_name in sorted(gpx_subfolders):
        if folder_name not in folder_colors:
            color_index = len(folder_colors) % len(COLOR_PALETTE)
            assigned_color = COLOR_PALETTE[color_index]
            folder_colors[folder_name] = assigned_color
            print(f"[COLOR] Assigned color {assigned_color} to folder: {folder_name}")
            colors_updated = True

    if colors_updated:
        save_folder_colors(folder_colors)
        print(f"[OK] folder_colors.yaml updated\n")

    return folder_colors


def make_human_name(stem: str) -> str:
    """Convert filename into readable title."""
    name = stem.replace("-", " ").replace("  ", " ")
    return " ".join(word.capitalize() for word in name.split())


def load_walks_yaml():
    """Load walks.yaml file."""
    with open(WALKS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"walks": []}


def save_walks_yaml(data):
    """Save walks.yaml file."""
    with open(WALKS_YAML, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)


def update_walks_yaml():
    """Scan GPX folder and update walks.yaml with new entries."""
    data = load_walks_yaml()
    if "walks" not in data:
        data["walks"] = []

    existing_gpx = {Path(w["gpx"]).as_posix() for w in data["walks"]}
    new_walks_added = False

    for gpx_file in GPX_FOLDER.rglob("*.gpx"):
        relative_gpx = gpx_file.relative_to(BASE_DIR).as_posix()
        if relative_gpx not in existing_gpx:
            name = make_human_name(gpx_file.stem)
            gpx_rel = gpx_file.relative_to(GPX_FOLDER)
            journal_rel = Path("journals") / gpx_rel.with_suffix(".md")

            new_walk = {
                "name": name,
                "gpx": relative_gpx,
                "journal": journal_rel.as_posix()
            }

            data["walks"].append(new_walk)
            print(f"[+] Added new walk: {relative_gpx}")
            new_walks_added = True

    if new_walks_added:
        save_walks_yaml(data)
        print("[OK] walks.yaml updated with new GPX files\n")
    else:
        print("[INFO] No new GPX files found\n")

    return data


def generate_map(data=None, folder_colors=None):
    """Generate interactive Folium map from walks data."""
    MAP_DIR.mkdir(parents=True, exist_ok=True)

    if data is None:
        data = load_walks_yaml()
    if folder_colors is None:
        folder_colors = load_folder_colors()

    m = folium.Map(location=[54.5, -3.0], zoom_start=6, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="CartoDB Light"
    ).add_to(m)

    for walk in data.get("walks", []):
        name = walk["name"]
        coords = []
        gpx_path = BASE_DIR / walk["gpx"]

        if not gpx_path.exists():
            print(f"[WARN] Missing GPX file: {gpx_path}")
            continue

        with open(gpx_path, "r", encoding="utf-8") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        coords.append([point.latitude, point.longitude])
            for route in gpx.routes:
                for point in route.points:
                    coords.append([point.latitude, point.longitude])

        if not coords:
            continue

        journal_html = walk["journal"].replace(".md", ".html")
        journal_url = f"{SITE_ROOT}/{journal_html}"
        popup_html = f"<b>{name}</b><br><a href='{journal_url}' target='_blank'>View Journal</a>"

        gpx_rel_path = Path(walk["gpx"]).relative_to("gpx")
        folder_name = gpx_rel_path.parts[0]
        color = folder_colors.get(folder_name, "#808080")

        folium.PolyLine(coords, color=color, weight=4, popup=popup_html).add_to(m)
        print(f"[OK] Added to map: {name} (color: {color})")

    map_out = MAP_DIR / "index.html"
    m.save(str(map_out))
    print(f"\n[OK] Map saved to {map_out}\n")


if __name__ == "__main__":
    folder_colors = assign_colors_to_folders()
    data = update_walks_yaml()
    generate_map(data, folder_colors)
