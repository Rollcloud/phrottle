"""Implement `mpremote fs cp -r src/rp2/ :/` in Python until mpremote release-1.24.0 (https://github.com/micropython/micropython/milestone/7) is available."""

import subprocess
from pathlib import Path

import mpremote

SOURCE = Path("src/rp2/")
DEST = Path(":")


if mpremote.__version__ >= "1.24.0":
    print(
        "mpremote release-1.24.0 or later is available. Use `mpremote fs cp -r src/rp2/ :/` instead."
    )
    exit(1)


def mpremote_fs_cp(source: Path, dest: Path):
    """Copy source to dest using mpremote fs cp."""
    if source.is_dir():
        if source.parent != SOURCE:
            # Create the parent directory of the source file
            print(f"Creating directory {dest.parent}")
            subprocess.run(f"mpremote fs mkdir {dest.parent}", shell=True)
    else:
        # print(f"Copying {source_file} to {dest_file}")
        subprocess.run(f"mpremote fs cp {source} {dest}", check=True, shell=True)


# Recursively iterate over all files in the source directory
for source_file in SOURCE.rglob("*"):
    # Calculate the relative path of the source file
    relative_path = source_file.relative_to(SOURCE)
    # Calculate the destination path of the source file
    dest_file = DEST / relative_path

    mpremote_fs_cp(source_file, dest_file)

print("Done.")
