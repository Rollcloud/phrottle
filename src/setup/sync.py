"""Implement `mpremote fs cp -r src/rp2/ :/` in Python until mpremote release-1.24.0 (https://github.com/micropython/micropython/milestone/7) is available."""

import subprocess
import sys
from pathlib import Path

import mpremote
import yaml

SOURCE = Path("src/rp2/")
DEST = Path(":")
DEFAULT_SEARCH = "*"

SETTINGS = Path("src/setup/sync.yaml")

settings = {}
if SETTINGS.exists():
    with SETTINGS.open("r") as f:
        settings = yaml.safe_load(f)


search = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SEARCH

if mpremote.__version__ >= "1.24.0":
    print(
        "mpremote release-1.24.0 or later is available. Use `mpremote fs cp -r src/rp2/ :/` instead."
    )
    exit(1)


def mpremote_fs_cp(source: Path, dest: Path) -> bool:
    """
    Copy source to dest using mpremote fs cp.

    Returns True if the source is a file for copying.
    """
    if source.is_dir():
        # Create the parent directory of the source file
        if source.parent != SOURCE:
            # Check if the directory exists
            result = subprocess.run(
                f"mpremote fs ls {dest.parent}",
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                # Directory does not exist, create it
                print(f"Creating directory {dest.parent}")
                subprocess.run(f"mpremote fs mkdir {dest.parent}", shell=True)
    else:
        # print(f"Copying {source_file} to {dest_file}")
        subprocess.run(f"mpremote fs cp {source} {dest}", check=True, shell=True)
        if "files" not in settings:
            settings["files"] = {}
        settings["files"][source.as_posix()] = int(source.stat().st_mtime)

        return True
    return False


copy_counter = 0
# Recursively iterate over all files in the source directory
for source_file in SOURCE.rglob(search):
    # Calculate the relative path of the source file
    relative_path = source_file.relative_to(SOURCE)
    # Calculate the destination path of the source file
    dest_file = DEST / relative_path

    # if file is newer, copy it
    source_modified = int(source_file.stat().st_mtime)
    dest_modified = settings.get("files", {}).get(source_file.as_posix(), 0)
    if source_modified > dest_modified:
        copied = mpremote_fs_cp(source_file, dest_file)
        if copied:
            copy_counter += 1
    else:
        # skipping file
        pass

with SETTINGS.open("w") as f:
    yaml.dump(settings, f)

print(f"Copied {copy_counter} files.")
print("Done.")
