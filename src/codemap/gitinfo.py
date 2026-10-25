"""Git hotspot data: per-file commit counts and last-modified dates.

A single ``git log`` invocation produces everything, so this stays fast even
on large repositories. All failures degrade to empty data — codemap works
fine on plain directories too.
"""

import os
import subprocess


def is_git_repo(root):
    if os.path.isdir(os.path.join(root, ".git")):
        return True
    try:
        out = subprocess.run(
            ["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return out.returncode == 0 and out.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def hotspots(root):
    """Return {rel_path: (commit_count, last_date)} for files in git history.

    last_date is a ``YYYY-MM-DD`` string. Files never committed are absent.
    """
    try:
        out = subprocess.run(
            ["git", "-C", root, "log", "--pretty=format:COMMIT %ad", "--date=short",
             "--name-only", "--no-renames"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if out.returncode != 0:
        return {}

    result = {}
    current_date = ""
    for line in out.stdout.splitlines():
        if line.startswith("COMMIT "):
            current_date = line[len("COMMIT "):].strip()
        elif line.strip():
            path = line.strip()
            count, last = result.get(path, (0, ""))
            # git log lists newest commits first, so the first date seen is
            # the most recent one.
            result[path] = (count + 1, last or current_date)
    return result


def apply_hotspots(files, root):
    """Fill in commits/last_modified on FileInfo objects, in place."""
    if not files or not is_git_repo(root):
        return files
    data = hotspots(root)
    for f in files:
        if f.path in data:
            f.commits, f.last_modified = data[f.path]
    return files
