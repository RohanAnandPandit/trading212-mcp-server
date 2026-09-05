#!/usr/bin/env python3
"""Check or refresh the checked-in Trading 212 OpenAPI snapshot."""

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

import yaml

SOURCE_URL = "https://docs.trading212.com/_bundle/api.yaml"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SNAPSHOT = REPOSITORY_ROOT / "docs" / "api.json"


def fetch_schema() -> Any:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "trading212-mcp-server-schema-sync"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return yaml.safe_load(response.read())


def changed_paths(before: Any, after: Any, path: str = "$") -> list[str]:
    if type(before) is not type(after):
        return [path]
    if isinstance(before, dict):
        paths: list[str] = []
        for key in sorted(before.keys() | after.keys()):
            child = f"{path}.{key}"
            if key not in before or key not in after:
                paths.append(child)
            else:
                paths.extend(changed_paths(before[key], after[key], child))
        return paths
    if isinstance(before, list):
        return [] if before == after else [path]
    return [] if before == after else [path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare docs/api.json with Trading 212's live OpenAPI schema."
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="fail when drift exists")
    action.add_argument("--update", action="store_true", help="refresh the snapshot")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    live = fetch_schema()
    snapshot = json.loads(args.snapshot.read_text())
    differences = changed_paths(snapshot, live)

    if not differences:
        print(f"Schema is current: {SOURCE_URL}")
        return 0

    print(f"Detected {len(differences)} changed schema paths:")
    for path in differences[:50]:
        print(f"- {path}")
    if len(differences) > 50:
        print(f"- ... and {len(differences) - 50} more")

    if args.update:
        args.snapshot.write_text(json.dumps(live, indent=2) + "\n")
        print(f"Updated {args.snapshot.relative_to(REPOSITORY_ROOT)}")
        return 0

    print("Run again with --update after reviewing the reported drift.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
