"""The Agensi skill archive contains only the allowlisted skill text files."""

import importlib.util
import os
import re
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/trading212-portfolio-analysis"


def load_packager():
    spec = importlib.util.spec_from_file_location(
        "package_agensi_skill", ROOT / "scripts/package-agensi-skill.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_archive_is_allowlisted_and_reproducible(tmp_path):
    packager = load_packager()
    first = packager.build(tmp_path / "a.zip")
    second = packager.build(tmp_path / "b.zip")
    assert first == second
    with ZipFile(tmp_path / "a.zip") as archive:
        assert archive.namelist() == [
            "trading212-portfolio-analysis/SKILL.md",
            "trading212-portfolio-analysis/references/analysis-guide.md",
            "trading212-portfolio-analysis/LICENSE",
        ]


@pytest.mark.skipif(os.name == "nt", reason="symlinks need privileges on Windows")
def test_archive_rejects_symlinked_files(tmp_path, monkeypatch):
    packager = load_packager()
    source = tmp_path / "skills" / packager.NAME
    (source / "references").mkdir(parents=True)
    for relative in packager.FILES:
        (source / relative).write_text("text\n")
    (source / "LICENSE").unlink()
    (source / "LICENSE").symlink_to(source / "SKILL.md")
    monkeypatch.setattr(packager, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Symlinks"):
        packager.build(tmp_path / "out.zip")


def test_skill_frontmatter_and_tool_names_match_server():
    from trading212_mcp.server import create_server
    from trading212_mcp.settings import Settings

    text = (SKILL / "SKILL.md").read_text() + (
        SKILL / "references/analysis-guide.md"
    ).read_text()
    assert re.match(r"---\nname: trading212-portfolio-analysis\ndescription: ", text)
    server = create_server(Settings(api_key="synthetic-key"))
    tools = {tool.name for tool in server._tool_manager.list_tools()}
    referenced = set(re.findall(r"`((?:fetch|search)_[a-z_]+)`", text))
    assert referenced and referenced <= tools
