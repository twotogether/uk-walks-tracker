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
    """Save walks.yaml file with atomic write to prevent corruption."""
    import tempfile
    import shutil
    from datetime import datetime

    try:
        # Create backup before overwriting
        if WALKS_YAML.exists():
            backup_path = WALKS_YAML.with_stem(f"{WALKS_YAML.stem}.backup")
            shutil.copy2(WALKS_YAML, backup_path)
            print(f"[OK] Created backup: {backup_path.name}")

        # Write to temporary file first (atomic write on Windows/Unix)
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            dir=WALKS_YAML.parent,
            delete=False,
            encoding="utf-8"
        ) as tmp_file:
            yaml.dump(data, tmp_file, sort_keys=False, allow_unicode=True)
            tmp_path = Path(tmp_file.name)

        # Atomic rename (move temp file to actual location)
        shutil.move(str(tmp_path), str(WALKS_YAML))
    except Exception as e:
        print(f"[ERROR] Failed to save walks.yaml: {e}")
        raise


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
            # Verify GPX file is readable before adding
            try:
                with open(gpx_file, "r", encoding="utf-8") as f:
                    gpxpy.parse(f)
            except Exception as e:
                print(f"[WARN] Skipping invalid/unreadable GPX file {gpx_file}: {e}")
                continue

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
        # Validate that no existing entries were lost
        final_gpx_set = {Path(w["gpx"]).as_posix() for w in data["walks"]}
        if len(final_gpx_set) < len(existing_gpx):
            lost_gpx = existing_gpx - final_gpx_set
            print(f"[ERROR] WARNING: {len(lost_gpx)} walk entries were lost during update!")
            for gpx in lost_gpx:
                print(f"  - {gpx}")
            raise RuntimeError("walks.yaml update would lose existing entries. Aborting.")

        save_walks_yaml(data)
        print("[OK] walks.yaml updated with new GPX files\n")
    else:
        print("[INFO] No new GPX files found\n")

    return data


def _build_spatial_grid(all_walks_coords):
    """
    Build a spatial grid mapping (round(lat,3), round(lon,3)) -> set of walk IDs.

    A grid cell contains multiple walk IDs when those walks pass through
    the same ~100m area, indicating a geographic overlap.

    Args:
        all_walks_coords: dict of {walk_id: {"coords": [[lat, lon], ...], ...}}

    Returns:
        dict: {(float, float): set of str}
    """
    grid = {}
    for walk_id, walk_data in all_walks_coords.items():
        for lat, lon in walk_data["coords"]:
            cell = (round(lat, 3), round(lon, 3))
            if cell not in grid:
                grid[cell] = set()
            grid[cell].add(walk_id)
    return grid


def _split_segments(coords, walk_id, grid):
    """
    Split coords into runs of consecutive points with the same overlap state.

    At each point, the overlap state is the frozenset of other walk IDs that
    also pass through the same ~100m grid cell.

    Transition points are shared between adjacent segments to prevent
    visual gaps in the rendered polyline.

    Args:
        coords:   list of [lat, lon] pairs for this walk
        walk_id:  str identifier for this walk (used to exclude self from overlap set)
        grid:     dict from _build_spatial_grid

    Returns:
        list of dicts: [
            {"overlapping_with": frozenset of str, "coords": [[lat, lon], ...]},
            ...
        ]
    """
    if not coords:
        return []

    segments = []
    current_overlap = None
    current_coords = []

    for pt in coords:
        cell = (round(pt[0], 3), round(pt[1], 3))
        others = frozenset(grid.get(cell, set()) - {walk_id})

        if others != current_overlap:
            if current_coords:
                current_coords.append(pt)
                segments.append({
                    "overlapping_with": current_overlap,
                    "coords": current_coords,
                })
            current_overlap = others
            current_coords = [pt]
        else:
            current_coords.append(pt)

    if current_coords:
        segments.append({
            "overlapping_with": current_overlap,
            "coords": current_coords,
        })

    return segments


def generate_map(data=None, folder_colors=None):
    """Generate interactive Folium map from walks data with overlapping path detection."""
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

    # ============================================================================
    # PASS 1: Parse all walks into memory
    # ============================================================================
    all_walks_coords = {}

    for walk in data.get("walks", []):
        walk_id = walk["gpx"]
        name = walk["name"]
        gpx_path = BASE_DIR / walk_id

        if not gpx_path.exists():
            print(f"[WARN] Missing GPX file: {gpx_path}")
            continue

        coords = []
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

        gpx_rel_path = Path(walk_id).relative_to("gpx")
        folder_name = gpx_rel_path.parts[0]
        color = folder_colors.get(folder_name, "#808080")

        journal_html = walk["journal"].replace(".md", ".html")
        journal_url = f"{SITE_ROOT}/{journal_html}"
        popup_html = f"<b>{name}</b><br><a href='{journal_url}' target='_blank'>View Journal</a>"

        all_walks_coords[walk_id] = {
            "name": name,
            "color": color,
            "coords": coords,
            "popup_html": popup_html,
        }

    # ============================================================================
    # Build spatial grid (detect overlapping walks)
    # ============================================================================
    grid = _build_spatial_grid(all_walks_coords)

    # ============================================================================
    # PASS 2: Split each walk into segments and render
    # ============================================================================
    for walk_id, walk_data in all_walks_coords.items():
        name = walk_data["name"]
        color = walk_data["color"]
        popup_html = walk_data["popup_html"]
        coords = walk_data["coords"]

        segments = _split_segments(coords, walk_id, grid)

        first_segment = True
        overlapping_segment_count = 0

        for seg in segments:
            seg_coords = seg["coords"]
            overlapping_with = seg["overlapping_with"]

            popup = popup_html if first_segment else None
            first_segment = False

            if not overlapping_with:
                # Non-overlapping segment: solid line
                folium.PolyLine(
                    seg_coords,
                    color=color,
                    weight=4,
                    popup=popup,
                ).add_to(m)
            else:
                # Overlapping segment: alternating dashes
                all_overlapping = overlapping_with | {walk_id}
                sorted_ids = sorted(all_overlapping)
                my_index = sorted_ids.index(walk_id)
                dash_offset = str(my_index * 15)

                folium.PolyLine(
                    seg_coords,
                    color=color,
                    weight=4,
                    dash_array="15 15",
                    dash_offset=dash_offset,
                    popup=popup,
                ).add_to(m)

                overlapping_segment_count += 1

        overlap_note = (
            f", {overlapping_segment_count} overlapping segment(s)"
            if overlapping_segment_count
            else ""
        )
        print(f"[OK] Added to map: {name} (color: {color}{overlap_note})")

    map_out = MAP_DIR / "index.html"
    m.save(str(map_out))
    print(f"\n[OK] Map saved to {map_out}\n")


if __name__ == "__main__":
    folder_colors = assign_colors_to_folders()
    data = update_walks_yaml()
    generate_map(data, folder_colors)
