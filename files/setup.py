#!/usr/bin/env python3
"""
setup.py - One-time setup script for SGB II MaEnde deployment tool.

Drop ALL files into one folder together with this script, then run:
    python setup.py

What it does:
    1. Creates all required subfolders (mstr, workflows, utils, tests)
    2. Moves every file into its correct subfolder automatically
    3. Reports what was moved, what was already in place, and what is missing
"""

import os
import sys
import shutil
from pathlib import Path


# ── File -> destination folder mapping ───────────────────────────────────────
# Key:   filename (just the name, no path)
# Value: subfolder it belongs in ("." = project root, stays where it is)

FILE_MAP = {
    # Root files — stay in the project root
    "main.py":               ".",
    "config.py":             ".",
    "credentials.env":       ".",
    "requirements.txt":      ".",
    "README.md":             ".",
    "run.bat":               ".",
    "run.sh":                ".",

    # mstr package
    "connection.py":         "mstr",
    "project.py":            "mstr",
    "dbconnection.py":       "mstr",
    "security.py":           "mstr",
    "duplicate.py":          "mstr",
    "schema.py":             "mstr",

    # workflows package
    "ohne_backup.py":        "workflows",
    "mit_backup.py":         "workflows",

    # utils package
    "logger.py":             "utils",

    # tests
    "test_config.py":        "tests",
    "test_workflows.py":     "tests",
}

# __init__.py files that must exist in each package folder
INIT_FILES = [
    "mstr/__init__.py",
    "workflows/__init__.py",
    "utils/__init__.py",
    "tests/__init__.py",
]

SUBFOLDERS = ["mstr", "workflows", "utils", "tests"]


def main():
    root = Path(__file__).parent.resolve()

    print()
    print("=" * 60)
    print("  SGB II MaEnde - Setup & File Organiser")
    print(f"  Folder: {root}")
    print("=" * 60)

    # ── Step 1: Create subfolders ─────────────────────────────────────
    print("\n[Step 1] Creating subfolders...")
    for folder in SUBFOLDERS:
        folder_path = root / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True)
            print(f"  [CREATED] {folder}/")
        else:
            print(f"  [OK]      {folder}/  (already exists)")

    # ── Step 2: Create missing __init__.py files ──────────────────────
    print("\n[Step 2] Creating package __init__.py files...")
    for init_path in INIT_FILES:
        full_path = root / init_path
        if not full_path.exists():
            full_path.write_text("", encoding="utf-8")
            print(f"  [CREATED] {init_path}")
        else:
            print(f"  [OK]      {init_path}  (already exists)")

    # ── Step 3: Move files into correct subfolders ────────────────────
    print("\n[Step 3] Organising files...")
    moved    = []
    skipped  = []
    missing  = []

    for filename, destination in FILE_MAP.items():
        dest_folder = root if destination == "." else root / destination
        dest_path   = dest_folder / filename
        src_path    = root / filename   # file dropped flat in root

        if dest_path.exists():
            # Already in the right place
            skipped.append(filename)
            print(f"  [OK]      {destination}/{filename}  (already in place)")

        elif src_path.exists() and destination != ".":
            # File is in root but needs to go into a subfolder — move it
            shutil.move(str(src_path), str(dest_path))
            moved.append(f"{filename}  ->  {destination}/")
            print(f"  [MOVED]   {filename}  ->  {destination}/")

        elif src_path.exists() and destination == ".":
            # File is already in root where it belongs
            skipped.append(filename)
            print(f"  [OK]      {filename}  (already in place)")

        else:
            # File not found anywhere
            missing.append(filename)
            print(f"  [MISSING] {filename}  (not found — download and place in {root})")

    # ── Step 4: Summary ───────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Moved:   {len(moved)}")
    print(f"  OK:      {len(skipped)}")
    print(f"  Missing: {len(missing)}")

    if missing:
        print()
        print("  The following files were not found.")
        print(f"  Download them and place them in: {root}")
        print()
        for f in missing:
            print(f"    - {f}")
        print()
        print("  Then run setup.py again.")
    else:
        print()
        print("  [SUCCESS] All files are in place!")
        print()
        print("  Next steps:")
        print("  1. Edit credentials.env with your server settings")
        print("  2. Install dependencies:")
        print("       pip install -r requirements.txt")
        print("  3. Preview without connecting:")
        print("       python main.py ohne-backup --dry-run")
        print("  4. Run for real:")
        print("       python main.py ohne-backup")
        print("       python main.py mit-backup --backup-month 202512")

    print("=" * 60)
    print()


if __name__ == "__main__":
    main()