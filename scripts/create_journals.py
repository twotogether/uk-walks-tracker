"""
Modular script for creating and managing walk journal markdown files.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GPX_DIR = BASE_DIR / "gpx"
JOURNALS_DIR = BASE_DIR / "docs" / "journals"

JOURNAL_TEMPLATE = """{title}

## Walk Metadata

| Attribute | Value |
| --------- | ----- |
| **Difficulty** | |
| **Distance** | |
| **Duration** | |
| **Elevation Gain** | |
| **Terrain** | |
| **Accessibility** | |
| **Can be done by public transport** | |

## Getting There

**Start:**
- **Train**:
- **Bus**:
- **Parking**:

**End:**
- **Train**:
- **Bus**:
- **Parking**:

## Route

| Section Walked  | Distance | Date |
| --------------- | -------- | ---- |

## Description

Add walk description here.

## Notes

- Add notes, photos, and links here.
"""


def create_journal_file(gpx_file: Path, gpx_dir: Path, journals_dir: Path) -> bool:
    """
    Create a journal markdown file for a GPX file if it doesn't exist.

    Returns True if a new file was created, False if it already existed.
    """
    rel_path = gpx_file.relative_to(gpx_dir)
    folder = rel_path.parent
    gpx_name = gpx_file.stem

    journal_folder = journals_dir / folder
    journal_folder.mkdir(parents=True, exist_ok=True)
    journal_file = journal_folder / f"{gpx_name}.md"

    if not journal_file.exists():
        title = f"# {gpx_name.replace('-', ' ').title()}\n"
        content = title + JOURNAL_TEMPLATE
        journal_file.write_text(content, encoding="utf-8")
        return True

    return False


def update_journals_index(journals_dir: Path) -> list:
    """
    Update journals/index.json with all existing markdown files.

    Returns a list of all journal files.
    """
    md_files = sorted([
        f.relative_to(journals_dir).as_posix()
        for f in journals_dir.rglob("*.md")
    ])

    with open(journals_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(md_files, f, indent=2)

    return md_files


def create_journals(gpx_dir=None, journals_dir=None):
    """
    Create missing journal markdown files for GPX files.

    Scans gpx/ folder and creates corresponding journals in docs/journals/
    with matching folder structure.
    """
    if gpx_dir is None:
        gpx_dir = GPX_DIR
    if journals_dir is None:
        journals_dir = JOURNALS_DIR

    journals_dir.mkdir(parents=True, exist_ok=True)

    new_files = []

    if gpx_dir.exists():
        for gpx_file in sorted(gpx_dir.rglob("*.gpx")):
            if create_journal_file(gpx_file, gpx_dir, journals_dir):
                rel_path_str = gpx_file.relative_to(gpx_dir).as_posix()
                new_files.append(rel_path_str)

    md_files = update_journals_index(journals_dir)

    print(f"📁 journals/index.json updated with {len(md_files)} entries.")
    if new_files:
        print(f"📝 Created {len(new_files)} new journal(s):")
        for f in new_files:
            print(f"   - {f}")
    else:
        print("✓ All GPX files have corresponding journals.")
    print()


if __name__ == "__main__":
    create_journals()
