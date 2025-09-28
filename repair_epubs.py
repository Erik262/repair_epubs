#!/usr/bin/env python3
"""Repair Epub files by rebuilding them as fresh ZIP archives."""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
import zipfile


def _build_epub_from_tree(content_root: Path, destination: Path) -> None:
    """Create an EPUB archive from files under *content_root*."""

    fd, temp_zip_name = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    temp_zip_path = Path(temp_zip_name)
    mimetype_path = content_root / "mimetype"

    try:
        with zipfile.ZipFile(temp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as rebuilt:
            if mimetype_path.is_file():
                rebuilt.write(
                    str(mimetype_path),
                    arcname="mimetype",
                    compress_type=zipfile.ZIP_STORED,
                )

            for item in sorted(content_root.rglob("*")):
                if not item.is_file() or item == mimetype_path:
                    continue
                rebuilt.write(
                    str(item),
                    arcname=str(item.relative_to(content_root)),
                )
    except Exception:
        temp_zip_path.unlink(missing_ok=True)
        raise

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(temp_zip_path), destination)


@contextlib.contextmanager
def _epub_content(source: Path):
    """Yield a directory containing the EPUB content for *source*."""

    if source.is_dir():
        yield source
        return

    with tempfile.TemporaryDirectory() as extract_dir:
        extract_path = Path(extract_dir)
        with zipfile.ZipFile(source, "r") as existing_zip:
            existing_zip.extractall(extract_path)
        yield extract_path


def rebuild_epub(source: Path, destination: Path) -> bool:
    """Rebuild a single EPUB archive from a file or directory."""

    if not source.exists():
        print(f"[warn] {source.name}: source missing", file=sys.stderr)
        return False

    try:
        with _epub_content(source) as content_root:
            _build_epub_from_tree(content_root, destination)
        return True
    except zipfile.BadZipFile:
        print(f"[warn] {source.name}: not a valid zip archive", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[warn] {source.name}: failed to rebuild ({exc})", file=sys.stderr)
        return False


def iterate_epubs(input_dir: Path):
    for path in sorted(input_dir.glob("*.epub")):
        if path.is_file() or path.is_dir():
            yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild EPUB files into clean ZIP archives.")
    parser.add_argument("input", type=Path, help="Directory containing source .epub files")
    parser.add_argument("output", type=Path, help="Directory for repaired .epub files")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing files in the output directory",
    )

    args = parser.parse_args(argv)

    source_dir: Path = args.input
    output_dir: Path = args.output

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Input directory '{source_dir}' does not exist or is not a directory", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    repaired = 0
    skipped = 0

    for epub in iterate_epubs(source_dir):
        total += 1
        target = output_dir / epub.name
        if target.exists() and not args.overwrite:
            print(f"[skip] {epub.name}: destination exists (use --overwrite to replace)")
            skipped += 1
            continue

        success = rebuild_epub(epub, target)
        if success:
            print(f"[ok]   {epub.name}")
            repaired += 1
        else:
            print(f"[fail] {epub.name}")

    if total == 0:
        print("No .epub files found.")
    else:
        print(
            f"Finished: processed {total} file(s), rebuilt {repaired}, skipped {skipped}, "
            f"failed {total - repaired - skipped}."
        )

    return 0 if repaired or total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
