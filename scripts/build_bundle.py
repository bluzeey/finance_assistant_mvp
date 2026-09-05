#!/usr/bin/env python3
"""Create a deterministic, secret-safe ZIP snapshot of the repository."""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2026, 9, 4, 9, 0, 0)
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "node_modules", "exports", "runs"}
EXCLUDED_FILES = {".env", ".DS_Store"}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path.name in EXCLUDED_FILES:
        return False
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False
    return path.is_file()


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted((p for p in ROOT.rglob("*") if should_include(p)), key=lambda p: p.as_posix()):
            relative = PurePosixPath(ROOT.name) / PurePosixPath(source.relative_to(ROOT).as_posix())
            info = ZipInfo(relative.as_posix(), FIXED_ZIP_TIME)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if source.stat().st_mode & 0o111 else 0o644) << 16
            archive.writestr(info, source.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT.parent / f"{ROOT.name}.zip",
        help="Destination ZIP path.",
    )
    args = parser.parse_args()
    print(build(args.output.resolve()))


if __name__ == "__main__":
    main()
