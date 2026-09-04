"""Standalone wheel/container verification, requiring only runtime dependencies."""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker")
    args = parser.parse_args()
    with TemporaryDirectory() as directory:
        if args.docker:
            command = "docker"
            parameters = [
                "run",
                "--rm",
                "-i",
                "--network=none",
                "-e",
                "TRADING212_API_KEY=synthetic-smoke",
                args.docker,
            ]
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network=none",
                    "--entrypoint",
                    "python",
                    args.docker,
                    "-c",
                    'import os,pathlib; assert os.getuid()==10001; assert not list(pathlib.Path("/app").rglob(".env*")); assert not pathlib.Path("/app/.cache").exists(); assert not pathlib.Path("/home/app/.env.docker-test").exists()',
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            command = sys.executable
            parameters = ["-m", "trading212_mcp"]
            import trading212_mcp

            # Editable installs would defeat this check.
            assert "site-packages" in str(Path(trading212_mcp.__file__).resolve())

        async def run():
            async with Client(
                StdioServerParameters(
                    command=command,
                    args=parameters,
                    cwd=directory,
                    env={
                        "TRADING212_API_KEY": "synthetic-smoke",
                        "TRADING212_CACHE_DIR": str(Path(directory) / "cache"),
                    },
                )
            ) as client:
                assert len((await client.list_tools()).tools) == 28
                assert len((await client.list_resources()).resources) == 11
                assert (
                    len((await client.list_resource_templates()).resource_templates)
                    == 5
                )
                assert len((await client.list_prompts()).prompts) == 1

        asyncio.run(run())
    print("Package smoke check passed")


if __name__ == "__main__":
    main()
