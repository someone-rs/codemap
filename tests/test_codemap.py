import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from codemap.languages import color_for, detect_language  # noqa: E402
from codemap.report import generate  # noqa: E402
from codemap.scanner import FileInfo, count_loc, scan  # noqa: E402
from codemap.gitinfo import apply_hotspots, hotspots, is_git_repo  # noqa: E402


# --- language detection ----------------------------------------------------

def test_detect_language_by_extension():
    assert detect_language("app.py") == "Python"
    assert detect_language("main.go") == "Go"
    assert detect_language("lib.rs") == "Rust"
    assert detect_language("index.ts") == "TypeScript"
    assert detect_language("style.css") == "CSS"
    assert detect_language("query.sql") == "SQL"
    assert detect_language("run.sh") == "Shell"
    assert detect_language("data.json") == "JSON"
    assert detect_language("cfg.yaml") == "YAML"
    assert detect_language("page.html") == "HTML"


def test_detect_language_special_filenames():
    assert detect_language("Dockerfile") == "Dockerfile"
    assert detect_language("Makefile") == "Makefile"
    assert detect_language("dockerfile") == "Dockerfile"


def test_detect_language_unknown():
    assert detect_language("weird.xyz123") == "Other"
    assert detect_language("noextension") == "Other"


def test_color_for_known_and_unknown():
    assert color_for("Python").startswith("#")
    assert color_for("DefinitelyNotALanguage") == "#cccccc"


# --- LOC counting ----------------------------------------------------------

def test_count_loc_ignores_blank_lines(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("import os\n\n\ndef x():\n    pass\n\n")
    assert count_loc(str(f)) == 3


def test_count_loc_empty_file(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    assert count_loc(str(f)) == 0


# --- walking / ignore rules -------------------------------------------------

def _write(root, rel, content="x = 1\n"):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(content)
    return p


def test_scan_skips_junk_dirs(tmp_path):
    root = str(tmp_path)
    _write(root, "src/app.py")
    _write(root, "node_modules/pkg/index.js")
    _write(root, ".git/config")
    _write(root, "__pycache__/app.pyc", content="binary")
    _write(root, ".venv/lib/code.py")
    paths = [f.path for f in scan(root)]
    assert paths == ["src/app.py"]


def test_scan_skips_hidden_by_default_and_includes_with_flag(tmp_path):
    root = str(tmp_path)
    _write(root, ".hidden.py")
    _write(root, "visible.py")
    assert [f.path for f in scan(root)] == ["visible.py"]
    assert sorted(f.path for f in scan(root, include_hidden=True)) == [
        ".hidden.py",
        "visible.py",
    ]


def test_scan_exclude_patterns(tmp_path):
    root = str(tmp_path)
    _write(root, "a.min.js")
    _write(root, "b.js")
    _write(root, "docs/readme.md")
    paths = [f.path for f in scan(root, exclude=["*.min.js", "docs/*"])]
    assert paths == ["b.js"]


def test_scan_max_depth(tmp_path):
    root = str(tmp_path)
    _write(root, "top.py")
    _write(root, "sub/mid.py")
    _write(root, "sub/deep/low.py")
    assert [f.path for f in scan(root, max_depth=0)] == ["top.py"]
    assert sorted(f.path for f in scan(root, max_depth=1)) == [
        "sub/mid.py",
        "top.py",
    ]


def test_scan_binary_files_get_zero_loc(tmp_path):
    root = str(tmp_path)
    p = os.path.join(root, "blob.bin")
    with open(p, "wb") as fh:
        fh.write(b"\x00\x01\x02binary")
    files = scan(root)
    assert len(files) == 1
    assert files[0].loc == 0
    assert files[0].size == 9


def test_scan_sorts_and_records_size(tmp_path):
    root = str(tmp_path)
    _write(root, "b.py", content="a = 1\nb = 2\n")
    _write(root, "a.py", content="a = 1\n")
    files = scan(root)
    assert [f.path for f in files] == ["a.py", "b.py"]
    assert files[1].loc == 2


# --- git hotspots -----------------------------------------------------------

def _git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True,
                   capture_output=True, text=True)


@pytest.fixture
def git_repo(tmp_path):
    root = str(tmp_path)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "Test")
    _write(root, "hot.py", content="v1\n")
    _write(root, "cold.py", content="v1\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "first")
    _write(root, "hot.py", content="v2\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "second")
    _write(root, "hot.py", content="v3\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "third")
    return root


def test_is_git_repo(git_repo, tmp_path):
    assert is_git_repo(git_repo) is True
    assert is_git_repo(str(tmp_path / "nothere")) is False


def test_hotspots_counts_and_dates(git_repo):
    data = hotspots(git_repo)
    assert data["hot.py"][0] == 3
    assert data["cold.py"][0] == 1
    # Newest commit first: last date is a real YYYY-MM-DD string.
    assert len(data["hot.py"][1]) == 10
    assert data["hot.py"][1][4] == "-"


def test_apply_hotspots_fills_fileinfo(git_repo):
    files = scan(git_repo)
    apply_hotspots(files, git_repo)
    by_path = {f.path: f for f in files}
    assert by_path["hot.py"].commits == 3
    assert by_path["cold.py"].commits == 1


def test_hotspots_plain_directory_returns_empty(tmp_path):
    assert hotspots(str(tmp_path)) == {}


# --- HTML report ------------------------------------------------------------

def _sample_files():
    return [
        FileInfo(path="src/app.py", size=1200, loc=40, language="Python",
                 commits=5, last_modified="2026-10-20"),
        FileInfo(path="src/util.py", size=300, loc=12, language="Python"),
        FileInfo(path="web/index.html", size=800, loc=30, language="HTML"),
        FileInfo(path="web/app.js", size=2000, loc=60, language="JavaScript",
                 commits=2, last_modified="2026-10-19"),
    ]


def test_generate_creates_self_contained_report(tmp_path):
    out = str(tmp_path / "report.html")
    generate(_sample_files(), "demo-repo", out)
    page = open(out, encoding="utf-8").read()
    # Sections present.
    assert "Treemap" in page
    assert "Languages" in page
    assert "Biggest files" in page
    assert "Most-changed files" in page
    # Data embedded.
    assert "src/app.py" in page
    assert "Python" in page
    # Summary numbers.
    assert "4" in page  # files (also appears elsewhere; check header cards)
    assert "142" in page  # total LOC: 40+12+30+60
    # Self-contained: no external assets.
    assert "<link" not in page
    assert "<script src" not in page
    assert "http://cdn" not in page and "https://cdn" not in page


def test_generate_without_git_shows_notice(tmp_path):
    files = [FileInfo(path="a.py", size=100, loc=5, language="Python")]
    out = str(tmp_path / "report.html")
    generate(files, "plain-dir", out)
    page = open(out, encoding="utf-8").read()
    assert "Not a git repository" in page


def test_generate_escapes_html_in_paths(tmp_path):
    files = [FileInfo(path="x/<b>.py", size=10, loc=1, language="Python")]
    out = str(tmp_path / "report.html")
    generate(files, "repo", out)
    page = open(out, encoding="utf-8").read()
    assert "x/&lt;b&gt;.py" in page
    # Raw "<b>" must not appear anywhere: tables are html-escaped and the
    # embedded JSON escapes "<" as \u003c.
    assert "x/<b>.py" not in page
