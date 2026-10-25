# 🗺️ codemap

**See your codebase.** One command turns any repository into a single, self-contained, interactive HTML report — a treemap of your files, a language breakdown, and your git hotspots.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Deps](https://img.shields.io/badge/deps-zero-brightgreen)

## What you get

Open the report in any browser — no server, no build step, no external assets. Everything is inline:

- **🗂️ Interactive treemap** — files sized by bytes, colored by language. Hover for details, **click a directory to zoom in**, breadcrumb to go back.
- **🌐 Language breakdown** — donut chart + bars: which languages your repo is really made of.
- **📦 Biggest files** — top 20 by size, with LOC and last-change date.
- **🔥 Most-changed files** — top 20 by git commit count. Your hotspots: the files that change most (and usually break most).
- **📊 Summary header** — total files, lines of code, size, top language.

👉 **Try a real report right now:** open [`demo/codemap-demo.html`](demo/codemap-demo.html) — it's codemap's report of its own codebase.

## Install

```bash
pip install codemap
```

Or run without installing:

```bash
git clone https://github.com/someone-rs/codemap
cd codemap
python -m codemap --help
```

## Quickstart

```bash
# Map the current directory
codemap

# Map another repo, custom output
codemap ~/projects/my-app -o my-app-map.html

# Skip docs and minified files, limit depth
codemap . --exclude 'docs/*' --exclude '*.min.js' --max-depth 3
```

Then open `codemap.html` in your browser. Example output:

```
codemap: 342 files, 28417 LOC, 1.84 MB -> codemap.html
```

## Usage

```
codemap [path] [-o report.html] [--max-depth N] [--exclude GLOB] [--include-hidden]
```

| Option | What it does |
| --- | --- |
| `path` | Repo or directory to analyze (default: `.`) |
| `-o, --output` | Output HTML file (default: `codemap.html`) |
| `--max-depth N` | Limit directory depth (`0` = root files only) |
| `--exclude GLOB` | Skip paths matching a glob (repeatable) |
| `--include-hidden` | Include dotfiles/dot-directories (skipped by default) |

Always skipped: `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`, `target`, and other junk directories.

## How it works

1. **Scan** — walks the tree, classifies each file's language by extension, counts non-blank lines of code, skips binaries.
2. **Git hotspots** — a single `git log` pass counts commits per file and finds last-modified dates. Plain directories work too (the hotspot section just notes it).
3. **Render** — everything is embedded into one HTML file: inline CSS, vanilla JS treemap (slice-and-dice layout), pure-SVG donut. Zero runtime dependencies, and the report works offline forever.

## Development

```bash
pip install pytest
pytest
```

## License

MIT — see [LICENSE](LICENSE).
