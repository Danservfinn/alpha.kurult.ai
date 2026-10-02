#!/usr/bin/env python3
"""Static site builder for alpha.kurult.ai.

Python 3 standard library only. Reads articles/YYYY-MM-DD-slug.md and writes
a fully static, script-free site into dist/.

Last line of output is BUILD_OK or BUILD_FAIL.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import sys
import traceback
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "articles"
DIST = ROOT / "dist"
MARK_SRC = ROOT / "mark.svg"

SITE_HOST = "alpha.kurult.ai"
SITE_URL = f"https://{SITE_HOST}"
SITE_NAME = "alpha.kurult.ai"
SITE_KICKER = "Arghun, Crypto Analyst"
SITE_TAGLINE = "Daily research notes. Research only. Not a trading desk."

DISCLAIMER = (
    "Research only. Not financial advice. Nothing on this site is an offer "
    "to buy, sell, or hold any asset. No wallet. No comments."
)

FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://\S+$", re.I)


class BuildError(Exception):
    """Raised for any content or configuration problem that must fail the build."""


# --------------------------------------------------------------------------- #
# Frontmatter
# --------------------------------------------------------------------------- #


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_frontmatter(text: str, name: str) -> tuple[str, str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        raise BuildError(f"{name}: missing frontmatter opening '---'")
    end = text.find("\n---\n", 4)
    if end == -1:
        if text.endswith("\n---"):
            return text[4:-4], ""
        raise BuildError(f"{name}: missing frontmatter closing '---'")
    return text[4:end], text[end + 5 :]


def parse_source_list(lines: list[str], i: int, name: str) -> tuple[list[dict], int]:
    items: list[dict] = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if not line[0] in " \t-":
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append({})
            stripped = stripped[2:].strip()
        if not items:
            raise BuildError(f"{name}: malformed sources list near {line!r}")
        m = re.match(r"^(label|url):\s*(.*)$", stripped)
        if not m:
            raise BuildError(f"{name}: unexpected sources line {line!r}")
        items[-1][m.group(1)] = unquote(m.group(2).strip())
        i += 1
    return items, i


def parse_frontmatter(block: str, name: str) -> dict:
    meta: dict = {}
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            raise BuildError(f"{name}: bad frontmatter line {line!r}")
        key, value = m.group(1), m.group(2).strip()
        if key == "sources":
            if value:
                raise BuildError(f"{name}: sources must be a list")
            meta[key], i = parse_source_list(lines, i + 1, name)
            continue
        meta[key] = unquote(value)
        i += 1
    return meta


def validate_meta(meta: dict, file_date: str, name: str) -> None:
    for key in ("title", "date", "summary"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise BuildError(f"{name}: frontmatter '{key}' is required")
    if not DATE_RE.match(meta["date"]):
        raise BuildError(f"{name}: date must be YYYY-MM-DD")
    try:
        dt.date.fromisoformat(meta["date"])
    except ValueError as exc:
        raise BuildError(f"{name}: invalid date {meta['date']!r}") from exc
    if meta["date"] != file_date:
        raise BuildError(
            f"{name}: frontmatter date {meta['date']} does not match filename date {file_date}"
        )
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        raise BuildError(f"{name}: sources must be a non-empty list")
    for idx, src in enumerate(sources, 1):
        label = src.get("label", "").strip()
        url = src.get("url", "").strip()
        if not label:
            raise BuildError(f"{name}: source {idx} is missing a label")
        if not URL_RE.match(url):
            raise BuildError(f"{name}: source {idx} has an invalid url {url!r}")


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
UL_RE = re.compile(r"^[-*+]\s+(.*)$")
OL_RE = re.compile(r"^\d+[.)]\s+(.*)$")
FENCE_RE = re.compile(r"^```\s*([\w+-]*)\s*$")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
STRONG_RE = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1")
EM_RE = re.compile(r"(?<![\w*])(\*|_)(?=\S)(.+?)(?<=\S)\1(?![\w*])")
SAFE_HREF_RE = re.compile(r"^(https?:|mailto:|/|#|\.)", re.I)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_inline_text(text: str) -> str:
    """Escape then apply links and emphasis. Links are protected from emphasis."""
    text = esc(text)
    links: list[str] = []

    def link_sub(m: re.Match) -> str:
        label, href = m.group(1), m.group(2)
        if not SAFE_HREF_RE.match(html.unescape(href)):
            return label
        links.append(f'<a href="{href}">{label}</a>')
        return f"\x00{len(links) - 1}\x00"

    text = LINK_RE.sub(link_sub, text)
    text = STRONG_RE.sub(r"<strong>\2</strong>", text)
    text = EM_RE.sub(r"<em>\2</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], text)


def render_inline(text: str) -> str:
    parts = CODE_SPAN_RE.split(text)
    out = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            out.append(f"<code>{esc(part)}</code>")
        else:
            out.append(render_inline_text(part))
    return "".join(out)


def is_block_start(line: str) -> bool:
    return bool(
        not line.strip()
        or FENCE_RE.match(line)
        or HEADING_RE.match(line)
        or UL_RE.match(line)
        or OL_RE.match(line)
    )


def render_fence(lines: list[str], i: int, out: list[str], name: str) -> int:
    lang = FENCE_RE.match(lines[i]).group(1)
    i += 1
    body: list[str] = []
    while i < len(lines) and not lines[i].startswith("```"):
        body.append(lines[i])
        i += 1
    if i >= len(lines):
        raise BuildError(f"{name}: unclosed fenced code block")
    cls = f' class="language-{esc(lang)}"' if lang else ""
    out.append(f"<pre><code{cls}>{esc(chr(10).join(body))}</code></pre>")
    return i + 1


def render_heading(m: re.Match, out: list[str]) -> None:
    # Article title owns <h1>; shift markdown headings down one level.
    level = min(len(m.group(1)) + 1, 6)
    out.append(f"<h{level}>{render_inline(m.group(2))}</h{level}>")


def render_list(lines: list[str], i: int, out: list[str], marker: re.Pattern, tag: str) -> int:
    items: list[str] = []
    while i < len(lines):
        line = lines[i]
        m = marker.match(line)
        if m:
            items.append(m.group(1).strip())
        elif line[:1] in (" ", "\t") and line.strip() and items:
            items[-1] += " " + line.strip()
        else:
            break
        i += 1
    out.append(f"<{tag}>" + "".join(f"<li>{render_inline(t)}</li>" for t in items) + f"</{tag}>")
    return i


def render_paragraph(lines: list[str], i: int, out: list[str]) -> int:
    buf: list[str] = []
    while i < len(lines) and not is_block_start(lines[i]):
        buf.append(lines[i].strip())
        i += 1
    out.append(f"<p>{render_inline(' '.join(buf))}</p>")
    return i


def render_markdown(text: str, name: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif FENCE_RE.match(line):
            i = render_fence(lines, i, out, name)
        elif HEADING_RE.match(line):
            render_heading(HEADING_RE.match(line), out)
            i += 1
        elif UL_RE.match(line):
            i = render_list(lines, i, out, UL_RE, "ul")
        elif OL_RE.match(line):
            i = render_list(lines, i, out, OL_RE, "ol")
        else:
            i = render_paragraph(lines, i, out)
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Articles
# --------------------------------------------------------------------------- #


class Article:
    def __init__(self, path: Path):
        m = FILENAME_RE.match(path.name)
        if not m:
            raise BuildError(
                f"{path.name}: filename must match YYYY-MM-DD-slug.md "
                "(lowercase letters, digits, single hyphens)"
            )
        self.file_date, self.slug = m.group(1), m.group(2)
        self.dir_name = path.stem
        front, body = split_frontmatter(path.read_text(encoding="utf-8"), path.name)
        self.meta = parse_frontmatter(front, path.name)
        validate_meta(self.meta, self.file_date, path.name)
        self.date = dt.date.fromisoformat(self.meta["date"])
        self.title = self.meta["title"].strip()
        self.summary = self.meta["summary"].strip()
        self.sources = self.meta["sources"]
        self.body_html = render_markdown(body, path.name)
        if not self.body_html.strip():
            raise BuildError(f"{path.name}: article body is empty")

    @property
    def path(self) -> str:
        return f"/articles/{self.dir_name}/"

    @property
    def url(self) -> str:
        return SITE_URL + self.path

    @property
    def date_display(self) -> str:
        return f"{self.date.day:02d} {self.date.strftime('%b %Y')}"


def load_articles() -> list[Article]:
    if not ARTICLES_DIR.is_dir():
        raise BuildError(f"missing articles directory: {ARTICLES_DIR}")
    paths = sorted(p for p in ARTICLES_DIR.iterdir() if p.is_file() and not p.name.startswith("."))
    articles = [Article(p) for p in paths]
    articles.sort(key=lambda a: (a.date, a.slug), reverse=True)
    return articles


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #


def time_tag(article: Article) -> str:
    return f'<time datetime="{article.date.isoformat()}">{article.date_display}</time>'


def page(title: str, description: str, path: str, body: str, body_class: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{esc(SITE_URL + path)}">
<link rel="icon" href="/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="/styles.css">
</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="masthead sheet">
  <a class="wordmark" href="/" aria-label="{esc(SITE_NAME)} home">
    <img class="mark" src="/mark.svg" alt="" width="22" height="22">
    <span class="wordmark-text">{esc(SITE_NAME)}</span>
  </a>
  <span class="kicker">{esc(SITE_KICKER)}</span>
</header>
<div class="ticker" role="note" aria-label="Desk status">
  <div class="ticker-row sheet">
    <span class="tick tick-cmd" aria-hidden="true">&gt;_</span>
    <span class="tick">Alpha desk open</span>
    <span class="tick tick-up">&#9650; Daily notes</span>
    <span class="tick tick-down">&#9660; No trade</span>
    <span class="tick">No wallet</span>
    <span class="tick">No analytics</span>
  </div>
</div>
<aside class="notice" role="note" aria-label="Disclaimer">
  <div class="sheet"><span class="notice-mark" aria-hidden="true">!</span>{esc(DISCLAIMER)}</div>
</aside>
<main id="main" class="sheet">
{body}
</main>
<footer class="colophon sheet">
  <span>{esc(SITE_NAME)}</span>
  <span class="colophon-sep" aria-hidden="true">|</span>
  <span>No wallet. No comments. No analytics. No scripts.</span>
</footer>
</body>
</html>
"""


def render_index_entry(article: Article, i: int) -> str:
    return f"""  <li class="entry" style="--i:{i}">
    <span class="entry-date">{time_tag(article)}</span>
    <h2 class="entry-title"><a href="{esc(article.path)}">{esc(article.title)}</a></h2>
    <p class="entry-summary">{esc(article.summary)}</p>
  </li>"""


def render_index(articles: list[Article]) -> str:
    n = len(articles)
    count = f"{n} {'entry' if n == 1 else 'entries'}"
    if articles:
        entries = "\n".join(render_index_entry(a, i) for i, a in enumerate(articles))
        ledger_core = f'<ol class="ledger" reversed>\n{entries}\n  </ol>'
    else:
        ledger_core = '<p class="empty">No entries filed.</p>'
    body = f"""<section class="panel">
  <div class="panel-head"><span>Alpha desk</span><span>{esc(count)}</span></div>
  <div class="panel-body">
    <h1 class="command-title">{esc(SITE_NAME)}</h1>
    <p class="command-lede">{esc(SITE_TAGLINE)}</p>
  </div>
</section>
<section class="panel" aria-label="Article ledger">
  <div class="panel-head"><span>Ledger</span><span>{esc(count)}</span></div>
{ledger_core}
</section>"""
    return page(SITE_NAME, SITE_TAGLINE, "/", body, "page-index")


def render_sources(article: Article) -> str:
    items = "\n".join(
        f'    <li><a href="{esc(s["url"].strip())}" rel="noopener">{esc(s["label"].strip())}</a>'
        f'<span class="source-url">{esc(s["url"].strip())}</span></li>'
        for s in article.sources
    )
    return f"""<section class="sources panel" aria-labelledby="sources-heading">
  <div class="panel-head"><span id="sources-heading">Sources</span><span>{len(article.sources)} ref</span></div>
  <ol class="source-table">
{items}
  </ol>
</section>"""


def render_article(article: Article) -> str:
    body = f"""<article class="article panel">
  <div class="panel-head"><span><a href="/">&laquo; Ledger</a></span><span>{time_tag(article)}</span></div>
  <header class="article-head">
    <h1 class="article-title">{esc(article.title)}</h1>
    <p class="article-lede">{esc(article.summary)}</p>
  </header>
  <div class="prose">
{article.body_html}
  </div>
</article>
{render_sources(article)}"""
    return page(f"{article.title} | {SITE_NAME}", article.summary, article.path, body, "page-article")


def render_404() -> str:
    body = """<section class="panel panel-error">
  <div class="panel-head"><span>Error 404</span><span>Not found</span></div>
  <div class="panel-body">
    <h1 class="command-title">Nothing filed here.</h1>
    <p class="command-lede">The page you asked for is not on this desk. <a href="/">Return to the ledger.</a></p>
  </div>
</section>"""
    return page(f"Not found | {SITE_NAME}", "Page not found.", "/404.html", body, "page-404")


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #

STYLES = """/* alpha.kurult.ai terminal desk */
:root {
  --bg: #000000;
  --panel: #0a0906;
  --panel-head: rgba(255, 176, 0, .10);
  --amber: #ffb000;
  --amber-mid: #e6a100;
  --amber-dim: #c98400;
  --amber-faint: #a86b12;
  --text: #f2ecdc;
  --text-dim: #c9c0a8;
  --up: #00e676;
  --down: #ff6b6b;
  --edge: rgba(255, 176, 0, .36);
  --edge-soft: rgba(255, 176, 0, .16);
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --measure: 72ch;
  --gutter: clamp(1rem, 3vw, 2rem);
}

*, *::before, *::after { box-sizing: border-box; }

html {
  background: var(--bg);
  color: var(--text);
  font-family: var(--mono);
  font-size: 100%;
  -webkit-text-size-adjust: 100%;
  text-rendering: optimizeLegibility;
}

body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-size: .9375rem;
  line-height: 1.65;
  position: relative;
  isolation: isolate;
}

/* faint CRT scanlines */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  background: repeating-linear-gradient(
    0deg,
    rgba(255, 176, 0, .025) 0,
    rgba(255, 176, 0, .025) 1px,
    transparent 1px,
    transparent 3px
  );
}

::selection { background: var(--amber); color: #000; }

a { color: var(--amber); text-decoration-color: var(--amber-dim); text-underline-offset: .18em; }
a:hover { background: var(--amber); color: #000; text-decoration: none; }
a:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }

.sheet { width: 100%; max-width: 76rem; margin-inline: auto; padding-inline: var(--gutter); }

.skip {
  position: absolute;
  left: var(--gutter);
  top: -3rem;
  background: var(--amber);
  color: #000;
  padding: .5rem .75rem;
  font-size: .8rem;
  text-decoration: none;
  z-index: 10;
}
.skip:focus { top: .5rem; }

/* Masthead ---------------------------------------------------------------- */
.masthead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 1rem .9rem;
}
.wordmark {
  display: inline-flex;
  align-items: center;
  gap: .6rem;
  text-decoration: none;
  font-weight: 700;
  letter-spacing: .04em;
  color: var(--amber);
  font-size: 1rem;
}
.mark { width: 22px; height: 22px; display: block; }
.kicker {
  font-size: .72rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--amber-dim);
}

/* Ticker bar -------------------------------------------------------------- */
.ticker { border-block: 1px solid var(--edge); background: #000; }
.ticker-row {
  display: flex;
  flex-wrap: wrap;
  gap: .25rem 1.1rem;
  padding-block: .5rem;
  font-size: .72rem;
  letter-spacing: .10em;
  text-transform: uppercase;
}
.tick { color: var(--amber-dim); white-space: nowrap; }
.tick-cmd { color: var(--amber); font-weight: 700; }
.tick-up { color: var(--up); }
.tick-down { color: var(--down); }

/* Disclaimer strip -------------------------------------------------------- */
.notice {
  border-bottom: 1px solid var(--edge-soft);
  background: rgba(255, 176, 0, .05);
  font-size: .74rem;
  line-height: 1.6;
  color: var(--amber-mid);
}
.notice .sheet { padding-block: .55rem; display: flex; gap: .6rem; align-items: baseline; }
.notice-mark { color: var(--down); font-weight: 700; flex: none; }

main { flex: 1; padding-block: 1.75rem 3rem; display: grid; gap: 1.25rem; }

/* Panels ------------------------------------------------------------------ */
.panel { border: 1px solid var(--edge); background: var(--panel); }
.panel-head {
  display: flex;
  justify-content: space-between;
  gap: .5rem 1rem;
  flex-wrap: wrap;
  padding: .45rem .9rem;
  background: var(--panel-head);
  border-bottom: 1px solid var(--edge-soft);
  font-size: .70rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--amber);
}
.panel-head a { color: var(--amber); text-decoration: none; }
.panel-head a:hover { background: var(--amber); color: #000; }
.panel-head time { color: var(--amber-dim); letter-spacing: .06em; text-transform: none; }
.panel-body { padding: 1.1rem 1.15rem 1.25rem; }
.panel-error { border-color: rgba(255, 107, 107, .45); }
.panel-error .panel-head {
  color: var(--down);
  background: rgba(255, 107, 107, .10);
  border-bottom-color: rgba(255, 107, 107, .30);
}

.command-title {
  color: var(--amber);
  font-weight: 700;
  font-size: clamp(1.5rem, 4vw, 2.4rem);
  line-height: 1.1;
  letter-spacing: .01em;
  margin: 0 0 .6rem;
}
.command-lede { color: var(--text-dim); margin: 0; max-width: 58ch; }

/* Ledger ------------------------------------------------------------------ */
.ledger { list-style: none; margin: 0; padding: 0; }
.entry {
  display: grid;
  grid-template-columns: 1fr;
  gap: .15rem 1.25rem;
  padding: .7rem .9rem;
  border-bottom: 1px solid var(--edge-soft);
  animation: rise .3s ease both;
  animation-delay: calc(var(--i, 0) * 60ms);
}
.entry:last-child { border-bottom: 0; }
.entry:hover { background: rgba(255, 176, 0, .08); }
.entry-date {
  font-size: .74rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--amber-dim);
}
.entry-title { margin: 0; font-size: 1.02rem; line-height: 1.3; font-weight: 700; }
.entry-title a { color: var(--text); text-decoration: none; }
.entry-title a:hover { background: none; color: var(--amber); text-decoration: underline; }
.entry-title a:focus-visible { outline-offset: 0; }
.entry-summary { margin: 0; color: var(--text-dim); font-size: .84rem; line-height: 1.55; }
.empty {
  margin: 0;
  padding: 1rem .9rem;
  font-size: .8rem;
  letter-spacing: .10em;
  text-transform: uppercase;
  color: var(--amber-dim);
}

/* Article ----------------------------------------------------------------- */
.article-head { padding: 1.1rem 1.15rem 0; }
.article-title {
  color: var(--amber);
  font-weight: 700;
  font-size: clamp(1.3rem, 3.5vw, 2rem);
  line-height: 1.15;
  margin: 0 0 .55rem;
  text-wrap: balance;
}
.article-lede {
  color: var(--amber-mid);
  margin: 0;
  padding-bottom: 1.1rem;
  border-bottom: 1px solid var(--edge-soft);
  font-size: .95rem;
}

.prose { padding: 1.15rem 1.15rem 1.4rem; }
.prose > * { margin-block: 0 1.1em; }
.prose p, .prose li { color: var(--text); max-width: var(--measure); }
.prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {
  color: var(--amber);
  font-weight: 700;
  line-height: 1.25;
  margin-top: 1.8em;
  text-wrap: balance;
}
.prose h2 {
  font-size: 1rem;
  letter-spacing: .10em;
  text-transform: uppercase;
  border-left: 3px solid var(--amber);
  padding-left: .6rem;
}
.prose h3 { font-size: .95rem; letter-spacing: .06em; text-transform: uppercase; color: var(--amber-mid); }
.prose h4, .prose h5, .prose h6 {
  font-size: .78rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--amber-dim);
}
.prose ul, .prose ol { padding-left: 1.4em; margin-block: 0 1.1em; }
.prose li { margin-block: .3em; }
.prose li::marker { color: var(--amber-dim); }
.prose strong { color: var(--amber); font-weight: 700; }
.prose em { font-style: italic; }
.prose code {
  font-family: var(--mono);
  font-size: .88em;
  color: var(--amber);
  background: rgba(255, 176, 0, .12);
  padding: .08em .3em;
}
.prose pre {
  font-size: .8rem;
  line-height: 1.6;
  background: #000;
  border: 1px solid var(--edge-soft);
  border-left: 3px solid var(--amber);
  padding: .9rem 1rem;
  overflow-x: auto;
  color: var(--text-dim);
}
.prose pre code { background: none; padding: 0; font-size: inherit; color: inherit; }

/* Sources ----------------------------------------------------------------- */
.source-table { list-style: none; margin: 0; padding: 0; counter-reset: src; }
.source-table li {
  counter-increment: src;
  display: grid;
  grid-template-columns: 2.6rem minmax(0, 1fr);
  gap: 0 .5rem;
  padding: .55rem .9rem;
  border-bottom: 1px solid var(--edge-soft);
}
.source-table li:last-child { border-bottom: 0; }
.source-table li::before {
  content: counter(src, decimal-leading-zero);
  color: var(--amber-dim);
  font-size: .74rem;
  padding-top: .2em;
}
.source-table a { color: var(--text); text-decoration: none; }
.source-url {
  grid-column: 2;
  display: block;
  font-size: .7rem;
  color: var(--amber-dim);
  word-break: break-all;
  margin-top: .1rem;
}

/* Colophon ---------------------------------------------------------------- */
.colophon {
  border-top: 1px solid var(--edge-soft);
  margin-top: 1rem;
  padding-block: 1rem 1.8rem;
  font-size: .7rem;
  letter-spacing: .10em;
  text-transform: uppercase;
  color: var(--amber-faint);
  display: flex;
  flex-wrap: wrap;
  gap: .5rem .8rem;
}
.colophon-sep { color: var(--amber-dim); }

/* Motion ------------------------------------------------------------------ */
@keyframes rise {
  from { opacity: 0; transform: translateY(.35rem); }
  to { opacity: 1; transform: none; }
}
.panel { animation: rise .3s ease both; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* Wide -------------------------------------------------------------------- */
@media (min-width: 48rem) {
  .entry { grid-template-columns: 7.5rem minmax(0, 1fr); }
  .entry-summary { grid-column: 2; }
}
@media (min-width: 72rem) {
  .entry { grid-template-columns: 7.5rem 17rem minmax(0, 1fr); }
  .entry-summary { grid-column: 3; }
}

/* Narrow ------------------------------------------------------------------ */
@media (max-width: 48rem) {
  .masthead { flex-direction: column; align-items: flex-start; gap: .45rem; }
  .prose, .article-head { padding-inline: .9rem; }
  .panel-head { padding: .4rem .7rem; }
  .entry { padding: .65rem .7rem; }
  .source-table li { padding-inline: .7rem; grid-template-columns: 2.2rem minmax(0, 1fr); }
}

@media print {
  body { background: #fff; color: #000; }
  body::before, .ticker { display: none; }
  .panel { border-color: #000; background: #fff; }
  .panel-head, .notice, .colophon { color: #000; border-color: #000; background: none; }
  a { color: #000; background: none; }
}
"""

# --------------------------------------------------------------------------- #
# Text artefacts
# --------------------------------------------------------------------------- #


def render_robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"


def render_llms(articles: list[Article]) -> str:
    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_TAGLINE}",
        "",
        DISCLAIMER,
        "",
        "Static site. No scripts, no remote assets, no wallet, no comments, no analytics.",
        "",
        "## Articles",
        "",
    ]
    if articles:
        lines += [f"- [{a.title}]({a.url}): {a.summary}" for a in articles]
    else:
        lines.append("- (none yet)")
    return "\n".join(lines) + "\n"


def render_sitemap(articles: list[Article]) -> str:
    def url(loc: str, lastmod: str) -> str:
        return f"  <url>\n    <loc>{esc(loc)}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>"

    newest = articles[0].date.isoformat() if articles else dt.date.today().isoformat()
    entries = [url(SITE_URL + "/", newest)]
    entries += [url(a.url, a.date.isoformat()) for a in articles]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def reset_dist() -> None:
    if DIST.exists():
        if DIST.resolve().parent != ROOT:
            raise BuildError(f"refusing to remove unexpected dist path: {DIST}")
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)


def build() -> None:
    if not MARK_SRC.is_file():
        raise BuildError(f"missing {MARK_SRC.name} at repository root")
    articles = load_articles()
    print(f"  {len(articles)} article(s) loaded")

    reset_dist()
    write(DIST / "index.html", render_index(articles))
    for article in articles:
        write(DIST / "articles" / article.dir_name / "index.html", render_article(article))
    write(DIST / "404.html", render_404())
    write(DIST / "styles.css", STYLES)
    write(DIST / "robots.txt", render_robots())
    write(DIST / "llms.txt", render_llms(articles))
    write(DIST / "sitemap.xml", render_sitemap(articles))
    shutil.copyfile(MARK_SRC, DIST / "mark.svg")
    print("  copied mark.svg")


def main() -> int:
    try:
        build()
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("BUILD_FAIL")
        return 1
    except Exception:  # noqa: BLE001 - surface anything unexpected, then fail loudly
        traceback.print_exc()
        print("BUILD_FAIL")
        return 1
    print("BUILD_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
