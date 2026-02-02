import yaml
import folium
import gpxpy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WALKS_YAML = BASE_DIR / "data" / "walks.yaml"
GPX_FOLDER = BASE_DIR / "gpx"
MAP_DIR = BASE_DIR / "docs" / "_static" / "map"
FOLDER_COLORS_FILE = BASE_DIR / "data" / "folder_colors.yaml"
SITE_ROOT = "https://twotogether.github.io/uk-walks-tracker"

MAP_DIR.mkdir(parents=True, exist_ok=True)

# Predefined color palette for new folders
COLOR_PALETTE = [
    "#98FB98",      # Pale green
    "#6495ED",      # Cornflower blue
    "#FFD700",      # Gold
    "#FF6B6B",      # Red
    "#800000",      # Maroon
    "#DDA0DD",      # Plum
    "#F29239",      # Orange
    "#FFB6C1",      # Light pink
    "#90EE90",      # Light green
    "#20B2AA",      # Light sea green
]

def load_folder_colors():
    """Load folder-to-color mapping from file, creating it if it doesn't exist."""
    if FOLDER_COLORS_FILE.exists():
        with open(FOLDER_COLORS_FILE, "r", encoding="utf-8") as f:
            colors = yaml.safe_load(f) or {}
            return colors
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
            # Find next available color
            color_index = len(folder_colors) % len(COLOR_PALETTE)
            assigned_color = COLOR_PALETTE[color_index]
            folder_colors[folder_name] = assigned_color
            print(f"🎨 Assigned color {assigned_color} to folder: {folder_name}")
            colors_updated = True

    # Save if any new folders were added
    if colors_updated:
        save_folder_colors(folder_colors)
        print(f"\n✅ folder_colors.yaml updated\n")

    return folder_colors

# Assign colors to GPX folders
folder_colors = assign_colors_to_folders()

# Load existing walks.yaml
with open(WALKS_YAML, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

if "walks" not in data:
    data["walks"] = []

# Set of existing gpx entries, normalised
existing_gpx = {Path(w["gpx"]).as_posix() for w in data["walks"]}

new_walks_added = False

def make_human_name(stem: str) -> str:
    """Convert filename into readable title."""
    name = stem.replace("-", " ")
    name = name.replace("  ", " ")
    # Capitalize first letter of each word but keep apostrophes correct
    return " ".join(word.capitalize() for word in name.split())

# Scan all GPX recursively
for gpx_file in GPX_FOLDER.rglob("*.gpx"):
    relative_gpx = gpx_file.relative_to(BASE_DIR).as_posix()  # POSIX
    if relative_gpx not in existing_gpx:

        # Name comes from gpx filename
        name = make_human_name(gpx_file.stem)

        # Build journal path mirroring gpx/ structure
        # e.g. gpx/fife-coast-path/aberdour-to-kirkcaldy.gpx -> journals/fife-coast-path/aberdour-to-kirkcaldy.md
        gpx_rel = gpx_file.relative_to(GPX_FOLDER)
        journal_rel = Path("journals") / gpx_rel.with_suffix(".md")

        new_walk = {
            "name": name,
            "gpx": relative_gpx,
            "journal": journal_rel.as_posix()
        }

        data["walks"].append(new_walk)
        print(f"➕ Added new walk: {relative_gpx}")
        new_walks_added = True

# Save walks.yaml only if modified
if new_walks_added:
    with open(WALKS_YAML, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    print("\n✅ walks.yaml updated with new GPX files")
else:
    print("\nℹ️ No new GPX files found")

# Initialize map
m = folium.Map(location=[54.5, -3.0], zoom_start=6, tiles="OpenStreetMap")

# Load GPX files and overlay paths on map
for walk in data.get("walks", []):
    name = walk["name"]
    coords = []

    gpx_path = BASE_DIR / walk["gpx"]

    if not gpx_path.exists():
        print(f"⚠️ Missing GPX file: {gpx_path}")
        continue

    # Parse GPX
    with open(gpx_path, "r", encoding="utf-8") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

        # Handle tracks (existing functionality)
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    coords.append([point.latitude, point.longitude])

        # Handle routes (new functionality)
        for route in gpx.routes:
            for point in route.points:
                coords.append([point.latitude, point.longitude])

    if not coords:
        continue

    # Build journal URL (Sphinx builds .html versions)
    journal_html = walk["journal"].replace(".md", ".html")
    journal_url = f"{SITE_ROOT}/{journal_html}"

    popup_html = f"<b>{name}</b><br><a href='{journal_url}' target='_blank'>View Journal</a>"

    # Get color based on GPX subfolder
    gpx_rel_path = Path(walk["gpx"]).relative_to("gpx")
    folder_name = gpx_rel_path.parts[0]
    color = folder_colors.get(folder_name, "#808080")  # Default to gray if folder not in mapping

    folium.PolyLine(coords, color=color, weight=4, popup=popup_html).add_to(m)

    print(f"✅ Added to map: {name} (color: {color})")

# Save map
map_out = MAP_DIR / "index.html"
m.save(map_out)
print(f"\n✅ Map saved to {map_out}")
