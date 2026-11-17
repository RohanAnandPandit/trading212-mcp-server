#!/usr/bin/env python3
"""Build the Agensi submission archive from an explicit, text-only allowlist."""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
NAME = "trading212-portfolio-analysis"
FILES = ("SKILL.md", "references/analysis-guide.md", "LICENSE")


def build(output: Path) -> str:
    source = ROOT / "skills" / NAME
    payloads = {}
    for relative in FILES:
        path = source / relative
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError(f"Symlinks are not allowed: {relative}")
        payload = path.read_bytes()
        payload.decode("utf-8")
        if b"\x00" in payload:
            raise ValueError(f"Expected text file: {relative}")
        payloads[f"{NAME}/{relative}"] = payload

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, payload)

    with ZipFile(output) as archive:
        if archive.testzip() is not None or archive.namelist() != list(payloads):
            raise ValueError("Archive verification failed")
        for name, payload in payloads.items():
            if archive.read(name) != payload:
                raise ValueError(f"Archive content mismatch: {name}")
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / f"{NAME}.zip")
    args = parser.parse_args()
    digest = build(args.output)
    print(f"Archive: {args.output.resolve()}")
    print(f"SHA256: {digest}")
    print(f"Verified {len(FILES)} text files; no repository or account data included.")


if __name__ == "__main__":
    main()
