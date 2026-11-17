"""The Claude Code plugin manifests stay consistent with the package."""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = json.loads((ROOT / ".claude-plugin/plugin.json").read_text("utf-8"))
MARKETPLACE = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text("utf-8"))
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"]
SERVER = PLUGIN["mcpServers"]["trading212"]


def test_versions_and_names_match():
    assert PLUGIN["version"] == PROJECT["version"]
    [entry] = MARKETPLACE["plugins"]
    assert entry["name"] == PLUGIN["name"]
    assert entry["source"] == "./"


def test_server_launches_packaged_stdio_entry_point():
    args = SERVER["args"]
    assert SERVER["command"] == "uv"
    assert args[args.index("--directory") + 1] == "${CLAUDE_PLUGIN_ROOT}"
    assert args[-1] in PROJECT["scripts"]
    assert "--frozen" in args
    assert SERVER["env"]["TRANSPORT"] == "stdio"
    # Plugin roots are replaced on update; persistent state goes in the data dir.
    assert SERVER["env"]["TRADING212_CACHE_DIR"].startswith("${CLAUDE_PLUGIN_DATA}/")


def test_credentials_come_only_from_sensitive_user_config():
    options = PLUGIN["userConfig"]
    referenced = set(re.findall(r"\$\{user_config\.(\w+)\}", json.dumps(SERVER)))
    assert referenced == set(options)
    for key in ("api_key", "api_secret"):
        assert options[key]["sensitive"] is True
    assert options["environment"]["default"] == "demo"
    assert set(options["environment"]["options"]) == {"demo", "live"}


def test_bundled_skill_is_in_default_location():
    assert (ROOT / "skills/trading212-portfolio-analysis/SKILL.md").is_file()
    assert "skills" not in PLUGIN
