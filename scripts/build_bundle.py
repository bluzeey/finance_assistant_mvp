#!/usr/bin/env python3
"""Create a deterministic, secret-safe ZIP snapshot named finance_ai_bot."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "finance_ai_bot"
FIXED_ZIP_TIME = (2026, 9, 5, 0, 0, 0)
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "node_modules", "exports", "runs", ".mysql"}
EXCLUDED_FILES = {".env", ".DS_Store"}
SENSITIVE_PATTERNS = ("OPENAI_API_KEY=" + "sk-", "GITHUB_TOKEN=" + "gh", "MYSQL_PASSWORD=" + "root")


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path.name in EXCLUDED_FILES:
        return False
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False
    return path.is_file()


def scan_secret_like_text(path: Path, payload: bytes) -> None:
    if path.suffix.lower() in {".docx", ".zip", ".png", ".jpg", ".jpeg", ".webp"}:
        return
    text = payload.decode("utf-8", errors="ignore")
    for pattern in SENSITIVE_PATTERNS:
        if pattern in text:
            raise RuntimeError(f"secret-like value found in {path.relative_to(ROOT)}: {pattern}")


def validate() -> None:
    commands = [
        [sys.executable, "scripts/generate_dataset.py", "--check"],
        [sys.executable, "scripts/validate_dataset.py"],
        [sys.executable, "scripts/validate_repository.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)


def build(output: Path) -> tuple[Path, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    sources = sorted((p for p in ROOT.rglob("*") if should_include(p)), key=lambda p: p.as_posix())
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sources:
            payload = source.read_bytes()
            scan_secret_like_text(source, payload)
            relative = PurePosixPath(ARCHIVE_ROOT) / PurePosixPath(source.relative_to(ROOT).as_posix())
            info = ZipInfo(relative.as_posix(), FIXED_ZIP_TIME)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if source.stat().st_mode & 0o111 else 0o644) << 16
            archive.writestr(info, payload, compress_type=ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return output, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "finance_ai_bot.zip")
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    if not args.skip_validation:
        validate()
    path, digest = build(args.output.resolve())
    print(path)
    print(f"sha256:{digest}")


if __name__ == "__main__":
    main()
