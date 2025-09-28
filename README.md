# ebook_repair

Repair EPUB files by rebuilding them into clean ZIP archives. Ensures the `mimetype` entry is first and stored uncompressed, as required by the EPUB spec.

## Features
- Rebuilds EPUBs from files or already-extracted directories
- Preserves deterministic entry ordering

## Usage
```
python3 repair_epubs.py INPUT_DIR OUTPUT_DIR [--overwrite]
```

- INPUT_DIR: directory containing `.epub` files
- OUTPUT_DIR: directory where repaired `.epub` files will be written
- --overwrite: replace existing files in the output directory

## Notes
- The tool writes temporary archives in the output directory for atomic moves and better performance.
- The `mimetype` file, when present, is stored uncompressed and written first.
