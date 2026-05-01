#!/usr/bin/env python3
"""
Consolidated build orchestration script for UK Walks Tracker.

Runs the complete build pipeline:
1. Update walks.yaml from GPX files
2. Assign colors to walk folders
3. Generate journal markdown files
4. Generate interactive map
5. Build Sphinx documentation
"""

import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

# Import modular functions
sys.path.insert(0, str(BASE_DIR / "scripts"))
from update_uk_walks import assign_colors_to_folders, update_walks_yaml, generate_map
from create_journals import create_journals


def build_sphinx():
    """Build Sphinx documentation using sphinx-build."""
    import shutil

    print("\n" + "=" * 60)
    print("📚 Building Sphinx documentation...")
    print("=" * 60 + "\n")

    # Clean doctrees cache to avoid stale cache issues
    doctrees_dir = DOCS_DIR / "_build" / "doctrees"
    if doctrees_dir.exists():
        shutil.rmtree(doctrees_dir)

    # Use python -m sphinx for cross-platform compatibility
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", ".", "_build/html"],
        cwd=str(DOCS_DIR),
        capture_output=False
    )

    if result.returncode != 0:
        print("\n❌ Sphinx build failed!")
        return False

    print("\n✅ Sphinx documentation built successfully!\n")
    return True


def main(skip_sphinx=False):
    """Run the complete build pipeline."""
    print("\n" + "=" * 60)
    print("🚀 UK Walks Tracker Build Pipeline")
    print("=" * 60 + "\n")

    try:
        # Step 1: Assign colors
        print("=" * 60)
        print("1️⃣ Assigning colors to walk folders...")
        print("=" * 60 + "\n")
        folder_colors = assign_colors_to_folders()

        # Step 2: Update walks.yaml
        print("=" * 60)
        print("2️⃣ Updating walks.yaml from GPX files...")
        print("=" * 60 + "\n")
        data = update_walks_yaml()

        # Step 3: Create journals
        print("=" * 60)
        print("3️⃣ Creating journal markdown files...")
        print("=" * 60 + "\n")
        create_journals()

        # Step 4: Generate map
        print("=" * 60)
        print("4️⃣ Generating interactive map...")
        print("=" * 60 + "\n")
        generate_map(data, folder_colors)

        # Step 5: Build Sphinx documentation (optional)
        if skip_sphinx:
            print("\n" + "=" * 60)
            print("⏭️ Skipping Sphinx build (--update-only mode)")
            print("=" * 60 + "\n")
        else:
            if not build_sphinx():
                sys.exit(1)

        print("=" * 60)
        if skip_sphinx:
            print("✨ Update complete!")
        else:
            print("✨ Build complete! View at: docs/_build/html/index.html")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Build failed with error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UK Walks Tracker build system")
    parser.add_argument("--clean", action="store_true", help="Remove old build artifacts")
    parser.add_argument("--preview", action="store_true", help="Build and open in browser")
    parser.add_argument("--update-only", action="store_true", help="Update walks.yaml and map only (skip Sphinx)")
    args = parser.parse_args()

    if args.clean:
        import shutil
        build_dir = DOCS_DIR / "_build"
        if build_dir.exists():
            print("\n" + "=" * 60)
            print("🧹 Cleaning build artifacts...")
            print("=" * 60 + "\n")
            shutil.rmtree(build_dir)
            print("[OK] Build artifacts removed\n")

    try:
        main(skip_sphinx=args.update_only)

        if args.preview and not args.update_only:
            import webbrowser
            html_file = (DOCS_DIR / "_build" / "html" / "index.html").as_posix()
            webbrowser.open(f"file:///{html_file}")
            print(f"[OK] Opening {html_file} in browser\n")
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}\n")
        sys.exit(1)
