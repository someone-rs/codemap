"""codemap — see your codebase: one self-contained HTML report per repo."""

import argparse
import os
import sys

from .gitinfo import apply_hotspots
from .report import generate, repo_display_name
from .scanner import scan

__version__ = "0.1.0"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="codemap",
        description="Analyze a codebase and generate a single self-contained "
        "interactive HTML report (treemap, language breakdown, hotspots).",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="repository or directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "-o", "--output", default="codemap.html",
        help="output HTML file (default: codemap.html)",
    )
    parser.add_argument(
        "--max-depth", type=int, default=None, metavar="N",
        help="limit directory depth relative to the root (0 = root files only)",
    )
    parser.add_argument(
        "--exclude", action="append", default=[], metavar="GLOB",
        help="glob pattern to exclude (repeatable, matched against relative path)",
    )
    parser.add_argument(
        "--include-hidden", action="store_true",
        help="include hidden files and directories (skipped by default)",
    )
    parser.add_argument("--version", action="version", version="codemap " + __version__)
    args = parser.parse_args(argv)

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print("codemap: not a directory: %s" % args.path, file=sys.stderr)
        return 2

    files = scan(
        root,
        exclude=args.exclude,
        include_hidden=args.include_hidden,
        max_depth=args.max_depth,
    )
    apply_hotspots(files, root)
    out = generate(files, repo_display_name(root), args.output)
    total_loc = sum(f.loc for f in files)
    total_bytes = sum(f.size for f in files)
    print(
        "codemap: %d files, %d LOC, %s -> %s"
        % (len(files), total_loc, _fmt(total_bytes), out)
    )
    return 0


def _fmt(n):
    if n < 1024:
        return "%d B" % n
    if n < 1024 * 1024:
        return "%.1f KB" % (n / 1024)
    return "%.2f MB" % (n / 1024 / 1024)


if __name__ == "__main__":
    sys.exit(main())
