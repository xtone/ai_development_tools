import importlib.util
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
CONVERT = SCRIPTS / "md_to_artifact.py"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


conv = _load("md_to_artifact")

SAMPLE = """# Claude Code 運用 Tips

対象読者はエンジニア。
1章は通読する。

## 1. 落とし穴

### `Closes #N` をバッククォートで囲むと閉じない

PR 本文に `` `Closes #9` `` と書いたら閉じなかった。
体裁を整えたいなら `**Closes #N**` にする。

| コマンド | 何をするか |
|---|---|
| `/fix-pr <N>` | CI を直す |

```bash
echo "<b>" && gh stack link 10 11
```

- **強調**と [リンク](https://code.claude.com/docs/en/goal)
- <script>alert(1)</script>

1. 一つ目
2. 二つ目
"""


def test_code_spans_keep_symbols_and_never_nest():
    html = conv.render(SAMPLE)
    assert "<code><code>" not in html
    assert "<code><strong>" not in html
    assert "<code>`Closes #9`</code>" in html
    assert "<code>**Closes #N**</code>" in html
    assert "<code>`Closes #N`</code>" not in html
    assert "<code>Closes #N</code>" in html


def test_page_contract_title_and_theme_tokens():
    html = conv.render(SAMPLE)
    assert html.lstrip().startswith("<title>Claude Code 運用 Tips</title>")
    assert "<!doctype" not in html.lower()
    assert "<html" not in html.lower()
    assert "<body" not in html.lower()
    root = html.index(":root{")
    assert "--bg:" in html[root : html.index("}", root)]
    assert root < html.index("@media (prefers-color-scheme: dark)")
    assert ':root[data-theme="dark"]' in html


def test_blocks_are_converted_and_escaped():
    html = conv.render(SAMPLE)
    assert "<table>" in html and "<th>コマンド</th>" in html
    assert "<td><code>/fix-pr &lt;N&gt;</code></td>" in html
    assert '<pre class="code"><code>echo "&lt;b&gt;" &amp;&amp; gh stack link 10 11</code></pre>' in html
    assert '<a href="https://code.claude.com/docs/en/goal" target="_blank" rel="noopener">リンク</a>' in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<ol><li>一つ目</li><li>二つ目</li></ol>" in html


def test_lead_paragraph_joins_lines_without_br():
    html = conv.render(SAMPLE)
    assert "<p>対象読者はエンジニア。1章は通読する。</p>" in html
    assert "<br>" not in html


def test_toc_lists_sections():
    html = conv.render(SAMPLE)
    toc = html[html.index('<nav class="toc"') : html.index("</nav>")]
    assert re.search(r'<li class="l2"><a href="#s1">1\. 落とし穴</a></li>', toc)
    assert '<li class="l3"><a href="#s2"><code>Closes #N</code> をバッククォートで囲むと閉じない</a></li>' in toc


def test_title_falls_back_when_no_h1():
    html = conv.render("## だけ\n\n本文\n", fallback_title="tips")
    assert html.lstrip().startswith("<title>tips</title>")
    html = conv.render("## だけ\n", title="指定タイトル")
    assert html.lstrip().startswith("<title>指定タイトル</title>")


def test_cli_writes_file(tmp_path):
    src = tmp_path / "claude-code-tips.md"
    src.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "dist" / "index.html"
    r = subprocess.run(
        [sys.executable, "-I", str(CONVERT), str(src), "--out", str(out), "--meta", "対象: エンジニア"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    html = out.read_text(encoding="utf-8")
    assert "<span>対象: エンジニア</span>" in html
    r = subprocess.run(
        [sys.executable, "-I", str(CONVERT), str(tmp_path / "missing.md"), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2


def test_link_urls_cannot_break_out_of_the_attribute():
    html = conv.render('## s\n\n[x](https://a.example/"onmouseover="alert(1))\n')
    assert '"onmouseover="' not in html
    assert 'href="https://a.example/&quot;onmouseover=&quot;alert(1"' in html


def test_injection_attempts_in_every_block_stay_inert():
    payload = '<img src=x onerror=alert(1)>'
    md = "\n".join(
        [
            f"# T {payload}",
            f"lead {payload}",
            f"## H2 {payload}",
            f"### H3 `{payload}` {payload}",
            f"| {payload} | `{payload}` |",
            "|---|---|",
            f"| a {payload} | b |",
            f"- item {payload}",
            f"1. num {payload}",
            f"> quote {payload}",
            f"[{payload}](https://a.example/{payload})",
            f"[x](javascript:alert(1)) **{payload}**",
            "```",
            payload,
            "```",
            "x\x000\x00y",
        ]
    )
    html = conv.render(md, eyebrow=payload, meta=[payload])
    body = html[html.index("</style>") :]
    assert "<img" not in body
    assert 'href="javascript:' not in body
    html = conv.render("## s\n", title=payload)
    assert "<img" not in html
