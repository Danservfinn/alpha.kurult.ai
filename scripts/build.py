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
        unlisted_raw = str(self.meta.get("unlisted", "")).strip().lower()
        self.unlisted = unlisted_raw in ("true", "1", "yes")
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
<meta name="theme-color" content="#14120e">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{esc(SITE_URL + path)}">
<link rel="icon" href="/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="/styles.css">
</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="masthead sheet">
  <a class="wordmark" href="/" aria-label="{esc(SITE_NAME)} home">
    <img class="mark" src="/mark.svg" alt="" width="28" height="28">
    <span class="wordmark-text">{esc(SITE_NAME)}</span>
  </a>
  <span class="kicker">{esc(SITE_KICKER)}</span>
</header>
<aside class="notice" role="note" aria-label="Disclaimer">
  <div class="sheet"><span class="notice-mark" aria-hidden="true">&sect;</span>{esc(DISCLAIMER)}</div>
</aside>
<main id="main" class="sheet">
{body}
</main>
<footer class="colophon sheet">
  <span>{esc(SITE_NAME)}</span>
  <span class="colophon-sep" aria-hidden="true">&middot;</span>
  <span>No wallet. No comments. No analytics. No scripts.</span>
</footer>
</body>
</html>
"""


def render_index_entry(article: Article, i: int) -> str:
    return f"""  <li class="entry" style="--i:{i}">
    <div class="entry-date">{time_tag(article)}</div>
    <div class="entry-body">
      <h2 class="entry-title"><a href="{esc(article.path)}">{esc(article.title)}</a></h2>
      <p class="entry-summary">{esc(article.summary)}</p>
    </div>
  </li>"""


def render_index(articles: list[Article]) -> str:
    n = len(articles)
    count = f"{n} {'entry' if n == 1 else 'entries'}"
    if articles:
        entries = "\n".join(render_index_entry(a, i) for i, a in enumerate(articles))
        ledger = f'<ol class="ledger" reversed>\n{entries}\n</ol>'
    else:
        ledger = '<p class="empty">No entries filed yet.</p>'
    body = f"""<section class="hero">
  <p class="eyebrow">Ledger &middot; {esc(count)}</p>
  <h1 class="hero-title">{esc(SITE_NAME)}</h1>
  <p class="hero-lede">{esc(SITE_TAGLINE)}</p>
</section>
{ledger}"""
    return page(SITE_NAME, SITE_TAGLINE, "/", body, "page-index")


def render_sources(article: Article) -> str:
    items = "\n".join(
        f'    <li><a href="{esc(s["url"].strip())}" rel="noopener">{esc(s["label"].strip())}</a>'
        f'<span class="source-url">{esc(s["url"].strip())}</span></li>'
        for s in article.sources
    )
    return f"""<section class="sources" aria-labelledby="sources-heading">
  <h2 id="sources-heading" class="eyebrow">Sources</h2>
  <ol>
{items}
  </ol>
</section>"""


def render_article(article: Article) -> str:
    body = f"""<article class="article">
  <header class="article-head">
    <p class="eyebrow"><a href="/">&larr; Ledger</a> &middot; {time_tag(article)}</p>
    <h1 class="article-title">{esc(article.title)}</h1>
    <p class="article-lede">{esc(article.summary)}</p>
  </header>
  <div class="prose">
{article.body_html}
  </div>
{render_sources(article)}
</article>"""
    return page(f"{article.title} | {SITE_NAME}", article.summary, article.path, body, "page-article")


def render_404() -> str:
    body = """<section class="hero hero-404">
  <p class="eyebrow">Error 404</p>
  <h1 class="hero-title">Nothing filed here.</h1>
  <p class="hero-lede">The page you asked for is not on this desk. <a href="/">Return to the ledger.</a></p>
</section>"""
    return page(f"Not found | {SITE_NAME}", "Page not found.", "/404.html", body, "page-404")


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #

NOISE_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E"
    "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' "
    "stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"
)

STYLES = f"""/* alpha.kurult.ai night desk */
:root {{
  --ink: #14120e;
  --ink-raised: #1b1813;
  --paper: #f3ead7;
  --paper-dim: rgba(243, 234, 215, .70);
  --paper-faint: rgba(243, 234, 215, .42);
  --brass: #b08d57;
  --brass-dim: rgba(176, 141, 87, .55);
  --rule: rgba(176, 141, 87, .32);
  --serif: "Iowan Old Style", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --measure: 66ch;
  --gutter: clamp(1.25rem, 4vw, 3rem);
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html {{
  background: var(--ink);
  color: var(--paper);
  font-family: var(--serif);
  font-size: clamp(1.0625rem, 0.95rem + 0.4vw, 1.1875rem);
  line-height: 1.55;
  -webkit-text-size-adjust: 100%;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern", "liga", "onum";
}}

body {{
  margin: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(ellipse 70% 45% at 12% -8%, rgba(176, 141, 87, .22), transparent 70%),
    radial-gradient(ellipse 50% 40% at 100% 110%, rgba(176, 141, 87, .06), transparent 70%),
    var(--ink);
  position: relative;
  isolation: isolate;
}}

body::before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  opacity: .055;
  background-image: url("{NOISE_SVG}");
  mix-blend-mode: screen;
}}

::selection {{ background: var(--brass); color: var(--ink); }}

a {{ color: inherit; text-decoration-color: var(--brass-dim); text-underline-offset: .18em; }}
a:hover {{ text-decoration-color: var(--brass); }}
a:focus-visible {{ outline: 2px solid var(--brass); outline-offset: 3px; }}

.sheet {{
  width: 100%;
  max-width: 72rem;
  margin-inline: auto;
  padding-inline: var(--gutter);
}}

.skip {{
  position: absolute;
  left: var(--gutter);
  top: -3rem;
  background: var(--brass);
  color: var(--ink);
  padding: .5rem .75rem;
  font-family: var(--mono);
  font-size: .8rem;
  text-decoration: none;
}}
.skip:focus {{ top: .5rem; z-index: 10; }}

/* Masthead ---------------------------------------------------------------- */
.masthead {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 1.5rem 1.1rem;
}}
.wordmark {{
  display: inline-flex;
  align-items: center;
  gap: .7rem;
  text-decoration: none;
  letter-spacing: .02em;
  font-size: 1.05rem;
}}
.mark {{ width: 28px; height: 28px; display: block; }}
.wordmark-text {{ font-variant-numeric: oldstyle-nums; }}
.kicker {{
  font-family: var(--mono);
  font-size: .72rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--brass);
}}

/* Disclaimer strip -------------------------------------------------------- */
.notice {{
  border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  background: linear-gradient(90deg, rgba(176, 141, 87, .07), transparent 60%);
  font-family: var(--mono);
  font-size: .76rem;
  line-height: 1.5;
  color: var(--paper-dim);
}}
.notice .sheet {{ padding-block: .7rem; display: flex; gap: .8rem; align-items: baseline; }}
.notice-mark {{ color: var(--brass); flex: none; }}

/* Shared type ------------------------------------------------------------- */
.eyebrow {{
  font-family: var(--mono);
  font-size: .74rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--brass);
  margin: 0 0 1rem;
}}
.eyebrow a {{ text-decoration: none; }}
.eyebrow a:hover {{ text-decoration: underline; }}
.eyebrow time {{ color: var(--paper-dim); }}

main {{ flex: 1; padding-block: clamp(2.5rem, 7vw, 5.5rem) clamp(3rem, 8vw, 6rem); }}

/* Hero -------------------------------------------------------------------- */
.hero {{ max-width: 46rem; }}
.hero-title {{
  font-weight: 400;
  font-size: clamp(2.6rem, 7vw, 5.2rem);
  line-height: .98;
  letter-spacing: -.02em;
  margin: 0 0 1.2rem;
}}
.hero-lede {{
  font-style: italic;
  font-size: clamp(1.15rem, 1.6vw, 1.4rem);
  color: var(--paper-dim);
  margin: 0;
  max-width: 34ch;
}}
.hero-404 .hero-lede {{ max-width: 44ch; }}

/* Ledger ------------------------------------------------------------------ */
.ledger {{
  list-style: none;
  margin: clamp(3rem, 7vw, 5.5rem) 0 0;
  padding: 0;
  border-top: 1px solid var(--rule);
}}
.entry {{
  display: grid;
  grid-template-columns: 10rem minmax(0, 1fr);
  gap: 1rem 2.5rem;
  padding-block: 1.75rem 1.9rem;
  border-bottom: 1px solid var(--rule);
  position: relative;
  animation: rise .7s cubic-bezier(.2, .7, .2, 1) both;
  animation-delay: calc(var(--i, 0) * 70ms + 120ms);
}}
.entry::before {{
  content: "";
  position: absolute;
  left: 0;
  top: -1px;
  height: 1px;
  width: 0;
  background: var(--brass);
  transition: width .5s cubic-bezier(.2, .7, .2, 1);
}}
.entry:hover::before {{ width: 10rem; }}
.entry-date {{
  font-family: var(--mono);
  font-size: .78rem;
  letter-spacing: .06em;
  color: var(--brass);
  padding-top: .55em;
}}
.entry-title {{
  font-weight: 400;
  font-size: clamp(1.55rem, 2.8vw, 2.3rem);
  line-height: 1.12;
  letter-spacing: -.012em;
  margin: 0 0 .55rem;
  text-wrap: balance;
}}
.entry-title a {{ text-decoration: none; transition: color .25s ease; }}
.entry:hover .entry-title a {{ color: var(--brass); }}
.entry-summary {{
  margin: 0;
  color: var(--paper-dim);
  max-width: var(--measure);
  font-size: 1rem;
}}
.empty {{
  margin-top: 4rem;
  font-family: var(--mono);
  font-size: .85rem;
  color: var(--paper-faint);
  border-top: 1px solid var(--rule);
  padding-top: 1.5rem;
}}

/* Article ----------------------------------------------------------------- */
.article {{ max-width: 48rem; }}
.article-head {{ margin-bottom: clamp(2.5rem, 6vw, 4rem); }}
.article-title {{
  font-weight: 400;
  font-size: clamp(2.2rem, 5.5vw, 3.8rem);
  line-height: 1.02;
  letter-spacing: -.02em;
  margin: 0 0 1.25rem;
  text-wrap: balance;
}}
.article-lede {{
  font-style: italic;
  font-size: clamp(1.15rem, 1.5vw, 1.35rem);
  color: var(--paper-dim);
  margin: 0;
  padding-bottom: 1.75rem;
  border-bottom: 1px solid var(--rule);
  position: relative;
}}
.article-lede::after {{
  content: "";
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 5rem;
  height: 1px;
  background: var(--brass);
}}

.prose {{ max-width: var(--measure); }}
.prose > * {{ margin-block: 0 1.25em; }}
.prose p {{ hanging-punctuation: first; }}
.prose > p:first-child::first-letter {{
  float: left;
  font-size: 3.4em;
  line-height: .82;
  padding: .08em .12em 0 0;
  color: var(--brass);
}}
.prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {{
  font-weight: 400;
  line-height: 1.15;
  letter-spacing: -.01em;
  margin-top: 2.2em;
  text-wrap: balance;
}}
.prose h2 {{ font-size: 1.75rem; }}
.prose h3 {{ font-size: 1.35rem; }}
.prose h4, .prose h5, .prose h6 {{
  font-family: var(--mono);
  font-size: .78rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--brass);
}}
.prose ul, .prose ol {{ padding-left: 1.4em; }}
.prose li {{ margin-block: .35em; }}
.prose li::marker {{ color: var(--brass); font-family: var(--mono); font-size: .9em; }}
.prose a {{ text-decoration: underline; text-decoration-color: var(--brass-dim); }}
.prose a:hover {{ color: var(--brass); }}
.prose em {{ font-style: italic; }}
.prose strong {{ font-weight: 700; color: var(--paper); }}
.prose code {{
  font-family: var(--mono);
  font-size: .86em;
  background: rgba(243, 234, 215, .06);
  padding: .1em .35em;
  border-radius: 2px;
}}
.prose pre {{
  font-family: var(--mono);
  font-size: .82rem;
  line-height: 1.6;
  background: var(--ink-raised);
  border-left: 2px solid var(--brass);
  padding: 1rem 1.25rem;
  overflow-x: auto;
  color: var(--paper-dim);
}}
.prose pre code {{ background: none; padding: 0; font-size: inherit; }}

/* Sources ----------------------------------------------------------------- */
.sources {{
  margin-top: clamp(3rem, 7vw, 5rem);
  padding-top: 1.75rem;
  border-top: 1px solid var(--rule);
  max-width: var(--measure);
}}
.sources ol {{
  list-style: none;
  counter-reset: src;
  margin: 0;
  padding: 0;
}}
.sources li {{
  counter-increment: src;
  display: grid;
  grid-template-columns: 2.4rem minmax(0, 1fr);
  gap: 0 .5rem;
  padding-block: .6rem;
  border-bottom: 1px dashed var(--rule);
  font-size: .95rem;
}}
.sources li::before {{
  content: counter(src, decimal-leading-zero);
  font-family: var(--mono);
  font-size: .74rem;
  color: var(--brass);
  padding-top: .3em;
}}
.sources li a {{ text-decoration: none; }}
.sources li a:hover {{ color: var(--brass); text-decoration: underline; }}
.source-url {{
  display: block;
  grid-column: 2;
  font-family: var(--mono);
  font-size: .7rem;
  color: var(--paper-faint);
  word-break: break-all;
  margin-top: .15rem;
}}

/* Colophon ---------------------------------------------------------------- */
.colophon {{
  border-top: 1px solid var(--rule);
  padding-block: 1.4rem 2.2rem;
  font-family: var(--mono);
  font-size: .72rem;
  letter-spacing: .04em;
  color: var(--paper-faint);
  display: flex;
  flex-wrap: wrap;
  gap: .6rem;
}}
.colophon-sep {{ color: var(--brass); }}

/* Motion ------------------------------------------------------------------ */
@keyframes rise {{
  from {{ opacity: 0; transform: translateY(.6rem); }}
  to {{ opacity: 1; transform: none; }}
}}
.hero, .article-head {{ animation: rise .8s cubic-bezier(.2, .7, .2, 1) both; }}
.prose, .sources {{ animation: rise .8s cubic-bezier(.2, .7, .2, 1) both; animation-delay: .15s; }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}

/* Narrow ------------------------------------------------------------------ */
@media (max-width: 40rem) {{
  .entry {{ grid-template-columns: 1fr; gap: .4rem; }}
  .entry-date {{ padding-top: 0; }}
  .entry:hover::before {{ width: 4rem; }}
  .masthead {{ flex-direction: column; gap: .4rem; align-items: flex-start; }}
  .prose > p:first-child::first-letter {{ font-size: 2.8em; }}
}}

@media print {{
  body {{ background: #fff; color: #000; }}
  body::before {{ display: none; }}
  .notice, .colophon {{ color: #000; border-color: #000; }}
}}
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
    listed = [a for a in articles if not a.unlisted]
    print(f"  {len(articles)} article(s) loaded ({len(listed)} listed, {len(articles) - len(listed)} unlisted)")

    reset_dist()
    write(DIST / "index.html", render_index(listed))
    for article in articles:
        write(DIST / "articles" / article.dir_name / "index.html", render_article(article))
    write(DIST / "404.html", render_404())
    write(DIST / "styles.css", STYLES)
    write(DIST / "robots.txt", render_robots())
    write(DIST / "llms.txt", render_llms(listed))
    write(DIST / "sitemap.xml", render_sitemap(listed))
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
