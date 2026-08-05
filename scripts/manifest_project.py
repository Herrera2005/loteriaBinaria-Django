#!/usr/bin/env python3
"""Genera o verifica el manifiesto SHA-256 del paquete entregable."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "MANIFEST_SHA256.txt"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "staticfiles",
    "Respaldos",
}
EXCLUDED_NAMES = {
    ".env",
    "MANIFEST_SHA256.txt",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".bak",
    ".log",
    ".sqlite3",
    ".db",
}


def deliverable_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if relative.name in EXCLUDED_NAMES:
            continue
        if relative.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def digest(relative: Path) -> str:
    hasher = hashlib.sha256()
    with (ROOT / relative).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def expected_entries() -> dict[str, str]:
    return {relative.as_posix(): digest(relative) for relative in deliverable_files()}


def parse_manifest() -> dict[str, str]:
    if not MANIFEST.exists():
        raise RuntimeError("MANIFEST_SHA256.txt no existe.")
    entries = {}
    for number, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            checksum, relative = line.split("  ", 1)
        except ValueError as exc:
            raise RuntimeError(f"Línea inválida del manifiesto: {number}") from exc
        entries[relative] = checksum
    return entries


def write_manifest() -> None:
    entries = expected_entries()
    content = "".join(
        f"{checksum}  {relative}\n"
        for relative, checksum in entries.items()
    )
    MANIFEST.write_text(content, encoding="utf-8")
    print(f"Manifiesto generado: {len(entries)} archivos.")


def verify_manifest() -> int:
    expected = expected_entries()
    actual = parse_manifest()
    missing = sorted(set(actual) - set(expected))
    omitted = sorted(set(expected) - set(actual))
    changed = sorted(
        relative
        for relative in set(expected) & set(actual)
        if expected[relative] != actual[relative]
    )
    if missing or omitted or changed:
        print("MANIFIESTO SHA-256: FALLÓ")
        for relative in missing:
            print(f"- Declarado pero ausente: {relative}")
        for relative in omitted:
            print(f"- Archivo no inventariado: {relative}")
        for relative in changed:
            print(f"- Hash incorrecto: {relative}")
        return 1
    print(f"MANIFIESTO SHA-256: OK ({len(expected)} archivos)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_manifest()
        return 0
    return verify_manifest()


if __name__ == "__main__":
    sys.exit(main())
