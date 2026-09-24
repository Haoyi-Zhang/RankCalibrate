#!/usr/bin/env python3
"""Byte-compare deterministic scientific outputs from two verifier runs.

Resource/timing records are deliberately excluded because they are host observations,
not scientific invariants.  Every other regular file is treated as claim-relevant.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def _ignored(relative: Path) -> bool:
    return (
        relative.name == "reproduction.json"
        or (relative.name.startswith("resources") and relative.suffix == ".json")
    )


def deterministic_files(root: Path) -> dict[Path, bytes]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"result directory does not exist: {root}")
    files: dict[Path, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            relative = path.relative_to(root)
            if not _ignored(relative):
                files[relative] = path.read_bytes()
    if not files:
        raise ValueError(f"no deterministic result files found in {root}")
    return files


def compare_results(expected: Path, actual: Path) -> list[Path]:
    expected_files = deterministic_files(expected)
    actual_files = deterministic_files(actual)
    expected_names = set(expected_files)
    actual_names = set(actual_files)
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    changed = sorted(
        name
        for name in expected_names & actual_names
        if expected_files[name] != actual_files[name]
    )
    if missing or extra or changed:
        parts: list[str] = []
        if missing:
            parts.append("missing: " + ", ".join(map(str, missing)))
        if extra:
            parts.append("extra: " + ", ".join(map(str, extra)))
        if changed:
            parts.append("changed: " + ", ".join(map(str, changed)))
        raise ValueError("deterministic result mismatch (" + "; ".join(parts) + ")")
    return sorted(expected_names)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    matched = compare_results(args.expected, args.actual)
    print(f"deterministic result comparison passed: {len(matched)} files")


if __name__ == "__main__":
    main()
