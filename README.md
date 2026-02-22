# UK Walks Tracker

Track and visualize your walking adventures across the UK with an interactive map.

This Python tool transforms your GPX files into a beautiful interactive map, allowing you to log and organize walks by region.

## Features

- Automatically detects new GPX files and updates `data/walks.yaml`.  
- Generates interactive **Folium maps** showing walked sections with folder-based color coding.  
- Supports journaling for each walk in Markdown (`docs/journals/`).  
- Assigns custom colors to each walk folder for easy identification.  
- Sidebar TOC shows all walks.

## How to Use This

1. Fork this repo.

2. Place your GPX files in the `gpx` folder following the naming convention:

    `[start]-to-[destination].gpx`

    Example: `south-queensferry-to-boness.gpx`

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the build pipeline:

    ```bash
    python scripts/build.py
    ```

    This single command will:
    - Scan GPX folder and update `data/walks.yaml`
    - Assign colors to walk folders in `data/folder_colors.yaml`
    - Create/update journal markdown files in `docs/journals/`
    - Generate the interactive map in `docs/map/index.html`
    - Build Sphinx documentation in `docs/_build/html/`

    > ⚠️ If you delete a GPX file, manually remove it from `walks.yaml`.

5. View the output locally:

    ```bash
    open docs/_build/html/index.html  # macOS
    # or navigate in your file browser to docs/_build/html/index.html
    ```

## Output

- Interactive map: `docs/map/index.html`  
- Journals: `docs/journals/`  
- Distance data: `data/distance.json`  

See [UK Walks Tracker](https://twotogether.github.io/uk-walks-tracker/).