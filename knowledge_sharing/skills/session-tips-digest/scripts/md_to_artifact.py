#!/usr/bin/env python3
"""Convert a tips Markdown file into an Artifact page (HTML body content).

The page follows the Artifact page contract: no doctype/html/head/body tags,
a <title> first, color tokens on :root with dark-mode overrides, and a layout
that works at phone width.

Usage:
  md_to_artifact.py INPUT.md --out OUT.html [--title T] [--eyebrow E] [--meta TEXT]...
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

CSS = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Zen+Old+Mincho:wght@700;900&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: reading column with a sticky table of contents on the left at desktop; one column on phones. */
:root{--bg:#f6f7f4;--surface:#ffffff;--fg:#1d2420;--muted:#5b665f;--line:#d9ded8;--accent:#1f6f5f;--accent-soft:#e3efea;--code-bg:#eef1ed;--font-body:"Zen Kaku Gothic New","Hiragino Sans","Noto Sans JP",sans-serif;--font-display:"Zen Old Mincho","Hiragino Mincho ProN","Noto Serif JP",serif;--font-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141917;--surface:#1b211e;--fg:#e6ebe7;--muted:#9aa69f;--line:#2c352f;--accent:#6fc2ad;--accent-soft:#1f3a33;--code-bg:#222925;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141917;--surface:#1b211e;--fg:#e6ebe7;--muted:#9aa69f;--line:#2c352f;--accent:#6fc2ad;--accent-soft:#1f3a33;--code-bg:#222925;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--font-body);font-size:16px;line-height:1.85;margin:0;padding-block:0 4rem;padding-inline:16px}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1100px;margin:0 auto}
header.hero{padding-block:3rem 2rem;border-bottom:1px solid var(--line)}
.eyebrow{font-family:var(--font-mono);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:0 0 .75rem}
h1{font-family:var(--font-display);font-weight:900;font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.3;margin:0 0 1rem;text-wrap:balance}
.lead p{margin:0 0 .75rem;color:var(--muted);max-width:40em}
.meta{display:flex;flex-wrap:wrap;gap:.5rem 1.25rem;font-family:var(--font-mono);font-size:.8rem;color:var(--muted);margin-top:1.25rem}
.layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:3rem;align-items:start;padding-top:2rem}
.toc{position:sticky;top:calc(env(safe-area-inset-top,0px) + 1rem);max-height:calc(100vh - 2rem);overflow:auto;font-size:.85rem;padding-right:.5rem}
.toc-label{font-family:var(--font-mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 .5rem}
.toc ol{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
.toc a{display:block;color:var(--fg);text-decoration:none;padding:.25rem .75rem;border-left:2px solid transparent;margin-left:-1px;line-height:1.5}
.toc a:hover{background:var(--accent-soft)}
.toc li.l2 a{font-weight:700;margin-top:.5rem}
.toc li.l3 a{color:var(--muted);font-size:.8rem}
.toc a.active{border-left-color:var(--accent);color:var(--accent)}
main{min-width:0;max-width:44em}
section{padding-block:1.5rem 1rem;border-bottom:1px solid var(--line)}
section:last-of-type{border-bottom:0}
h2{font-family:var(--font-display);font-weight:700;font-size:1.55rem;line-height:1.35;margin:.5rem 0 1rem;text-wrap:balance;scroll-margin-top:1rem}
h3{font-size:1.08rem;font-weight:700;line-height:1.5;margin:2.25rem 0 .6rem;padding-left:.75rem;border-left:3px solid var(--accent);text-wrap:balance;scroll-margin-top:1rem}
p{margin:0 0 .9rem}
ul,ol{margin:0 0 1rem;padding-left:1.4em}
li{margin:.25rem 0}
li::marker{color:var(--accent)}
blockquote{margin:0 0 1rem;padding:.5rem 1rem;border-left:3px solid var(--line);color:var(--muted)}
code{font-family:var(--font-mono);font-size:.86em;background:var(--code-bg);padding:.1em .4em;border-radius:4px;word-break:break-all}
pre.code{background:var(--code-bg);border:1px solid var(--line);border-radius:6px;padding:.9rem 1rem;overflow-x:auto;margin:.75rem 0 1.1rem;line-height:1.6}
pre.code code{background:none;padding:0;font-size:.82rem;word-break:normal;white-space:pre}
.tablewrap{overflow-x:auto;margin:.75rem 0 1.1rem}
table{border-collapse:collapse;width:100%;font-size:.92rem;min-width:420px}
th,td{text-align:left;vertical-align:top;padding:.55rem .7rem;border-bottom:1px solid var(--line)}
th{font-weight:700;color:var(--muted);font-size:.8rem;letter-spacing:.04em;border-bottom:2px solid var(--line)}
td code{white-space:nowrap}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);font-size:.85rem;color:var(--muted);font-family:var(--font-mono)}
@media (max-width:860px){.layout{grid-template-columns:1fr;gap:1.5rem}.toc{position:static;max-height:none;border:1px solid var(--line);border-radius:6px;padding:1rem;background:var(--surface)}.toc li.l3{display:none}}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
</style>
"""

SCRIPT = """<script>
(function(){
  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
  if(!('IntersectionObserver' in window))return;
  var obs=new IntersectionObserver(function(es){
    es.forEach(function(e){if(e.isIntersecting){links.forEach(function(l){l.classList.remove('active')});var a=map[e.target.id];if(a)a.classList.add('active');}});
  },{rootMargin:'-10% 0px -80% 0px'});
  [].slice.call(document.querySelectorAll('main section, main h3')).forEach(function(t){obs.observe(t)});
})();
</script>
"""

BLOCK_START = re.compile(r"^(#{1,3} |```|\||- |\d+\. |> )")


def inline(text: str) -> str:
    """Render inline Markdown. Code spans are taken out first so their content stays literal."""
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append("<code>" + html.escape(m.group(1).strip(), quote=False) + "</code>")
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"``(.+?)``", stash, text)
    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        lambda m: '<a href="{}" target="_blank" rel="noopener">{}</a>'.format(
            m.group(2).replace('"', "&quot;"), m.group(1)
        ),
        text,
    )
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)


def _table(rows: list[list[str]]) -> str:
    head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    out = '<div class="tablewrap"><table><thead><tr>'
    out += "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
    for r in body:
        out += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    return out + "</tbody></table></div>"


def render(
    md: str,
    title: str | None = None,
    eyebrow: str = "Claude Code / Field Notes",
    meta: list[str] | None = None,
    fallback_title: str = "Claude Code Tips",
) -> str:
    lines = md.split("\n")
    out: list[str] = []
    lead: list[str] = []
    toc: list[tuple[int, str, str]] = []
    h1: str | None = None
    in_section = False
    count = 0
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("```"):
            buf = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f'<pre class="code"><code>{html.escape(chr(10).join(buf), quote=False)}</code></pre>')
            continue
        if line.startswith("# "):
            h1 = h1 or line[2:].strip()
            i += 1
            continue
        if line.startswith("## ") or line.startswith("### "):
            level = 2 if line.startswith("## ") else 3
            text = line[level + 1:].strip()
            count += 1
            anchor = f"s{count}"
            toc.append((level, anchor, text))
            if level == 2:
                if in_section:
                    out.append("</section>")
                out.append(f'<section id="{anchor}"><h2>{inline(text)}</h2>')
                in_section = True
            else:
                out.append(f'<h3 id="{anchor}">{inline(text)}</h3>')
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append(_table(rows))
            continue
        if re.match(r"^\d+\. ", line):
            items = []
            while i < n and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if line.startswith("- "):
            items = []
            while i < n and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if line.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:].strip())
                i += 1
            out.append("<blockquote><p>" + "".join(inline(x) for x in buf) + "</p></blockquote>")
            continue
        if not line.strip() or line.strip() == "---":
            i += 1
            continue
        buf = []
        while i < n and lines[i].strip() and not BLOCK_START.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        paragraph = "<p>" + "".join(inline(x) for x in buf) + "</p>"
        (out if in_section else lead).append(paragraph)
    if in_section:
        out.append("</section>")

    page_title = title or h1 or fallback_title
    toc_html = '<nav class="toc" aria-label="目次"><p class="toc-label">目次</p><ol>'
    toc_html += "".join(f'<li class="l{lv}"><a href="#{a}">{inline(t)}</a></li>' for lv, a, t in toc)
    toc_html += "</ol></nav>"
    meta_html = "".join(f"<span>{html.escape(m, quote=False)}</span>" for m in (meta or []))
    return (
        f"<title>{html.escape(page_title, quote=False)}</title>\n"
        + CSS
        + '<div class="wrap">\n<header class="hero">\n'
        + f'<p class="eyebrow">{html.escape(eyebrow, quote=False)}</p>\n'
        + f"<h1>{inline(page_title)}</h1>\n"
        + f'<div class="lead">{"".join(lead)}</div>\n'
        + (f'<div class="meta">{meta_html}</div>\n' if meta_html else "")
        + "</header>\n"
        + f'<div class="layout">\n{toc_html}\n<main>\n{"".join(out)}\n</main>\n</div>\n'
        + "<footer>事例は案件名・固有値を伏せ、パターンとして書き直してある。</footer>\n</div>\n"
        + SCRIPT
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert tips Markdown into an Artifact page.")
    parser.add_argument("input")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title")
    parser.add_argument("--eyebrow", default="Claude Code / Field Notes")
    parser.add_argument("--meta", action="append", default=[])
    args = parser.parse_args(argv)
    src = Path(args.input)
    try:
        md = src.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    page = render(md, title=args.title, eyebrow=args.eyebrow, meta=args.meta, fallback_title=src.stem)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(page)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
