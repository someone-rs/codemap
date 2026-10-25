"""Generate one self-contained interactive HTML report (inline CSS + JS)."""

import html
import json
import math
import os

from .languages import color_for

_CSS = """
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0d1117;color:#e6edf3}
header{padding:28px 32px 8px}h1{margin:0 0 6px;font-size:28px}.sub{color:#8b949e;margin:0 0 18px}
.cards{display:flex;gap:12px;flex-wrap:wrap;padding:0 32px}.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px 18px;min-width:130px}
.card b{display:block;font-size:22px}.card span{color:#8b949e;font-size:13px}
section{padding:18px 32px}h2{font-size:20px;margin:6px 0 14px}
.bar-row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:14px}.bar-row .ln{width:110px;color:#c9d1d9}
.bar-row .bar{flex:1;height:14px;background:#21262d;border-radius:7px;overflow:hidden}.bar-row .fill{height:100%}
.bar-row .v{width:150px;text-align:right;color:#8b949e;font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;color:#8b949e;padding:8px;border-bottom:1px solid #30363d}
td{padding:7px 8px;border-bottom:1px solid #21262d;font-variant-numeric:tabular-nums}tr:hover td{background:#161b22}
a{color:#58a6ff;text-decoration:none}
#crumbs{margin:0 0 10px;color:#8b949e;font-size:14px}#crumbs a{cursor:pointer}#crumbs a:hover{text-decoration:underline}
#treemap{position:relative;width:100%;height:560px;background:#010409;border:1px solid #30363d;border-radius:10px;overflow:hidden}
.tm{position:absolute;overflow:hidden;border:1px solid rgba(0,0,0,.35);border-radius:3px;cursor:pointer}
.tm.dir{background:#161b22;cursor:pointer}.tm.dir>.lbl{font-size:12px;color:#8b949e;padding:3px 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tm.file{color:#fff}.tm.file>.lbl{font-size:12px;padding:4px 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 2px rgba(0,0,0,.6)}
#tip{position:fixed;display:none;pointer-events:none;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 10px;font-size:13px;z-index:99;max-width:320px;box-shadow:0 8px 24px rgba(0,0,0,.5)}
#tip b{display:block;margin-bottom:2px}#tip span{color:#8b949e}
.donut-wrap{display:flex;gap:24px;align-items:center;flex-wrap:wrap}.legend{font-size:14px}.legend div{margin:4px 0}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}
footer{padding:10px 32px 28px;color:#8b949e;font-size:13px}
"""

_JS = """
const DATA = __DATA_JSON__;
const tip = document.getElementById('tip');
const box = document.getElementById('treemap');
const crumbs = document.getElementById('crumbs');
let path = [];
function nodeAt(p){let n=DATA.tree;for(const s of p){n=n.children.find(c=>c.name===s);}return n;}
function fmt(n){if(n<1024)return n+' B';if(n<1048576)return (n/1024).toFixed(1)+' KB';return (n/1048576).toFixed(2)+' MB';}
function render(){
  const root=nodeAt(path);
  box.innerHTML='';
  crumbs.innerHTML='';
  const home=document.createElement('a');
  home.textContent=DATA.name;
  home.onclick=()=>go([]);
  crumbs.appendChild(home);
  path.forEach((s,i)=>{
    crumbs.appendChild(document.createTextNode(' / '));
    const a=document.createElement('a');
    a.textContent=s;
    const target=path.slice(0,i+1);
    a.onclick=()=>go(target);
    crumbs.appendChild(a);
  });
  layout(root, box, box.clientWidth, box.clientHeight);
}
function go(p){path=p;render();}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function layout(node, el, w, h){
  const kids=[...(node.children||[])].sort((a,b)=>b.size-a.size);
  if(!kids.length){
    const d=document.createElement('div');d.className='tm file';
    d.style.cssText='left:0;top:0;width:100%;height:100%;background:'+node.color;
    d.innerHTML='<div class="lbl">'+esc(node.name)+'</div>';
    tipify(d,node);el.appendChild(d);return;
  }
  let x=0,y=0,rw=w,rh=h;
  const horizontal = rw>=rh;
  const total=kids.reduce((s,c)=>s+c.size,0)||1;
  let headerH=0;
  if(node!==DATA.tree || path.length){
    const hd=document.createElement('div');hd.className='lbl';hd.textContent=node.name;
    hd.style.cssText='font-size:12px;color:#8b949e;padding:3px 6px;';
    el.appendChild(hd);headerH=20;rh-=headerH;y+=headerH;
  }
  for(const k of kids){
    const frac=k.size/total;
    const cw=horizontal?rw*frac:rw, ch=horizontal?rh:rh*frac;
    if(cw<2||ch<2) continue;
    const d=document.createElement('div');
    const isDir=!!k.children;
    d.className='tm '+(isDir?'dir':'file');
    d.style.cssText='left:'+x+'px;top:'+y+'px;width:'+cw+'px;height:'+ch+'px;'+(isDir?'':'background:'+k.color);
    if(isDir){
      d.onclick=e=>{e.stopPropagation();path=[...path,k.name];render();};
      d.innerHTML='<div class="lbl">'+esc(k.name)+'</div>';
      const inner=document.createElement('div');
      inner.style.cssText='position:absolute;left:0;right:0;top:20px;bottom:0;';
      d.appendChild(inner);
      layout(k,inner,Math.max(cw-2,1),Math.max(ch-22,1));
    } else {
      if(cw>60&&ch>28) d.innerHTML='<div class="lbl">'+esc(k.name)+'<br><span style="opacity:.8">'+fmt(k.size)+'</span></div>';
      else if(cw>28&&ch>18) d.innerHTML='<div class="lbl">'+esc(k.name)+'</div>';
      tipify(d,k);
    }
    el.appendChild(d);
    if(horizontal) x+=cw; else y+=ch;
  }
}
function tipify(el,node){
  el.onmousemove=e=>{
    tip.style.display='block';
    tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+14)+'px';
    tip.innerHTML='<b>'+esc(node.path)+'</b><span>'+node.language+' &middot; '+fmt(node.size)+' &middot; '+node.loc+' LOC'+(node.commits?' &middot; '+node.commits+' commits':'')+'</span>';
  };
  el.onmouseleave=()=>{tip.style.display='none';};
}
window.addEventListener('resize',render);
render();
"""


def fmt_size(n):
    if n < 1024:
        return "%d B" % n
    if n < 1024 * 1024:
        return "%.1f KB" % (n / 1024)
    return "%.2f MB" % (n / 1024 / 1024)


def _build_tree(files):
    """Nested dict tree from flat file list. Dirs get aggregated size."""
    root = {"name": "", "size": 0, "children": {}}
    for f in files:
        parts = f.path.split("/")
        node = root
        node["size"] += f.size
        for part in parts[:-1]:
            node = node["children"].setdefault(
                part, {"name": part, "size": 0, "children": {}})
            node["size"] += f.size
        node["children"][parts[-1]] = {
            "name": parts[-1],
            "path": f.path,
            "size": f.size,
            "loc": f.loc,
            "language": f.language,
            "commits": f.commits,
            "color": color_for(f.language),
        }
    return root


def _tree_to_json(node):
    out = {"name": node["name"], "size": node["size"]}
    if "path" in node:
        out.update(
            path=node["path"],
            loc=node["loc"],
            language=node["language"],
            commits=node["commits"],
            color=node["color"],
        )
    else:
        out["children"] = [
            _tree_to_json(c)
            for c in sorted(node["children"].values(), key=lambda c: -c["size"])
        ]
    return out


def _donut(languages, total_bytes):
    """SVG donut of language share by bytes (pure SVG, no JS)."""
    r = 80
    circ = 2 * math.pi * r
    segments = []
    offset = 0.0
    for lang, b in languages:
        frac = b / total_bytes if total_bytes else 0
        dash = frac * circ
        segments.append(
            '<circle cx="100" cy="100" r="80" fill="none" stroke="%s" '
            'stroke-width="28" stroke-dasharray="%.2f %.2f" '
            'stroke-dashoffset="%.2f" transform="rotate(-90 100 100)"/>'
            % (color_for(lang), dash, circ - dash, -offset)
        )
        offset += dash
    return (
        '<svg width="200" height="200" viewBox="0 0 200 200">'
        + "".join(segments)
        + "</svg>"
    )


def generate(files, repo_name, output_path):
    """Write the report for *files* (list of FileInfo) to *output_path*."""
    total_files = len(files)
    total_loc = sum(f.loc for f in files)
    total_bytes = sum(f.size for f in files)

    lang_bytes = {}
    lang_files = {}
    for f in files:
        lang_bytes[f.language] = lang_bytes.get(f.language, 0) + f.size
        lang_files[f.language] = lang_files.get(f.language, 0) + 1
    languages = sorted(lang_bytes.items(), key=lambda kv: -kv[1])
    top_language = languages[0][0] if languages else "—"

    tree_json = json.dumps(
        {"name": repo_name, "tree": _tree_to_json(_build_tree(files))}
    ).replace("<", "\\u003c")

    bars = []
    for lang, b in languages[:12]:
        pct = 100.0 * b / total_bytes if total_bytes else 0
        bars.append(
            '<div class="bar-row"><span class="ln">%s</span>'
            '<span class="bar"><span class="fill" style="width:%.1f%%;background:%s"></span></span>'
            '<span class="v">%.1f%% &middot; %s &middot; %d files</span></div>'
            % (html.escape(lang), pct, color_for(lang), pct, fmt_size(b),
               lang_files[lang])
        )

    def row_file(f):
        return (
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>"
            % (html.escape(f.path), html.escape(f.language), fmt_size(f.size),
               f.loc, f.last_modified or "—")
        )

    biggest = "".join(row_file(f) for f in sorted(files, key=lambda f: -f.size)[:20])
    hot = "".join(
        row_file(f) for f in sorted(files, key=lambda f: -f.commits)[:20]
        if f.commits
    )
    hot_section = (
        "<section><h2>🔥 Most-changed files (git history)</h2><table>"
        "<tr><th>File</th><th>Language</th><th>Size</th><th>LOC</th><th>Last change</th></tr>"
        + hot
        + "</table></section>"
        if hot
        else "<section><h2>🔥 Most-changed files</h2><p style='color:#8b949e'>"
        "Not a git repository, or no file history found — run codemap inside "
        "a git checkout to see hotspots.</p></section>"
    )

    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>codemap — {repo}</title><style>{css}</style></head>
<body>
<header><h1>🗺️ codemap — {repo}</h1>
<p class="sub">Interactive map of your codebase. Click a directory tile to zoom in.</p></header>
<div class="cards">
<div class="card"><b>{files:,}</b><span>files</span></div>
<div class="card"><b>{loc:,}</b><span>lines of code</span></div>
<div class="card"><b>{size}</b><span>total size</span></div>
<div class="card"><b>{top}</b><span>top language</span></div>
</div>
<section><h2>🗂️ Treemap (by file size)</h2>
<div id="crumbs"></div><div id="treemap"></div><div id="tip"></div></section>
<section><h2>🌐 Languages</h2><div class="donut-wrap">{donut}
<div class="legend">{legend}</div></div>{bars}</section>
<section><h2>📦 Biggest files</h2><table>
<tr><th>File</th><th>Language</th><th>Size</th><th>LOC</th><th>Last change</th></tr>
{biggest}</table></section>
{hot_section}
<footer>Generated by <a href="https://github.com/someone-rs/codemap">codemap</a> — single-file report, no external assets.</footer>
<script>{js}</script>
</body></html>
""".format(
        repo=html.escape(repo_name),
        css=_CSS,
        files=total_files,
        loc=total_loc,
        size=fmt_size(total_bytes),
        top=html.escape(top_language),
        donut=_donut(languages, total_bytes),
        legend="".join(
            '<div><span class="dot" style="background:%s"></span>%s — %s</div>'
            % (color_for(lang), html.escape(lang), fmt_size(b))
            for lang, b in languages[:12]
        ),
        bars="".join(bars),
        biggest=biggest,
        hot_section=hot_section,
        js=_JS.replace("__DATA_JSON__", tree_json),
    )

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return output_path


def repo_display_name(root):
    return os.path.basename(os.path.abspath(root)) or "repo"
