"""Directory walking, file classification and LOC counting."""

import fnmatch
import os
from dataclasses import dataclass

from .languages import detect_language

# Directories never descended into (unless explicitly re-included via --exclude
# overrides, which only add patterns; these defaults are always skipped).
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    "coverage",
    ".eggs",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".gradle",
    ".terraform",
    "vendor",
    "bower_components",
}

SKIP_FILES = {
    ".DS_Store",
    "Thumbs.db",
}

# Files bigger than this are counted for size but not read for LOC.
MAX_READ_SIZE = 1024 * 1024  # 1 MiB

# A file is treated as binary if a NUL byte appears in the first chunk.
_BINARY_PROBE = 8192


@dataclass
class FileInfo:
    path: str  # path relative to the scanned root, slash-separated
    size: int
    loc: int
    language: str
    commits: int = 0
    last_modified: str = ""  # ISO date, "" when unknown


def is_binary(path):
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(_BINARY_PROBE)
    except OSError:
        return True


def count_loc(path):
    """Count non-blank lines of a text file. 0 for binary/unreadable files."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for line in fh if line.strip())
    except OSError:
        return 0


def _matches_any(name, patterns):
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def scan(root, exclude=(), include_hidden=False, max_depth=None):
    """Walk *root* and return a list of FileInfo, sorted by path.

    *exclude* is a list of glob patterns matched against the relative path
    (e.g. ``*.min.js`` or ``docs/*``). *max_depth* limits directory depth
    relative to the root (0 = only files directly in root).
    """
    root = os.path.abspath(root)
    exclude = list(exclude)
    results = []

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1

        # Prune directories in-place so os.walk does not descend into them.
        keep_dirs = []
        for d in dirnames:
            if d in SKIP_DIRS:
                continue
            if not include_hidden and d.startswith("."):
                continue
            sub = d if rel_dir == "." else rel_dir + os.sep + d
            if max_depth is not None and depth + 1 > max_depth:
                continue
            if _matches_any(sub.replace(os.sep, "/"), exclude):
                continue
            keep_dirs.append(d)
        dirnames[:] = keep_dirs

        if max_depth is not None and depth > max_depth:
            continue

        for name in filenames:
            if name in SKIP_FILES:
                continue
            if not include_hidden and name.startswith("."):
                continue
            rel = name if rel_dir == "." else rel_dir + os.sep + name
            rel_slash = rel.replace(os.sep, "/")
            if _matches_any(rel_slash, exclude):
                continue
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size > MAX_READ_SIZE or is_binary(full):
                loc = 0
            else:
                loc = count_loc(full)
            results.append(
                FileInfo(
                    path=rel_slash,
                    size=size,
                    loc=loc,
                    language=detect_language(name),
                )
            )

    results.sort(key=lambda f: f.path)
    return results
