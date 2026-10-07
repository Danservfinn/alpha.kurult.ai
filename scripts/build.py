#!/usr/bin/env python3
"""Static site builder for alpha.kurult.ai.

Python 3 standard library only. Reads articles/YYYY-MM-DD-slug.md and writes
dist/. One first-party script draws the market panels. No third-party script host.

Last line of output is BUILD_OK or BUILD_FAIL.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import desk_html
from desk_panels import desk_sections

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "articles"
DIST = ROOT / "dist"
MARK_SRC = ROOT / "mark.svg"
ASSETS_DIR = ROOT / "assets"

SITE_HOST = "alpha.kurult.ai"
SITE_URL = f"https://{SITE_HOST}"
SITE_NAME = "alpha.kurult.ai"
SITE_BRAND = "Kurultai Alpha"
SITE_KICKER = "Arghun, Crypto Analyst"
SITE_TAGLINE = "Daily research notes. Research only. Not a trading desk."

DISCLAIMER = (
    "Research only. Not financial advice. Nothing on this site is an offer "
    "to buy, sell, or hold any asset. No wallet. No comments."
)
DRAFT_BANNER = "DRAFT. Not published. No outside post. Research only. Not financial advice."

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


def parse_pair_list(
    lines: list[str], i: int, name: str, fields: tuple[str, ...], label: str
) -> tuple[list[dict], int]:
    items: list[dict] = []
    field_re = re.compile(r"^(" + "|".join(fields) + r"):\s*(.*)$")
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line[0] not in " \t-":
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append({})
            stripped = stripped[2:].strip()
        if not items:
            raise BuildError(f"{name}: malformed {label} list near {line!r}")
        m = field_re.match(stripped)
        if not m:
            raise BuildError(f"{name}: unexpected {label} line {line!r}")
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
            meta[key], i = parse_pair_list(lines, i + 1, name, ("label", "url"), "sources")
            continue
        if key == "keys":
            if value:
                raise BuildError(f"{name}: keys must be a list")
            meta[key], i = parse_pair_list(lines, i + 1, name, ("label", "value", "note"), "keys")
            continue
        if key in ("falsifiers", "catalysts", "alerts"):
            if value:
                raise BuildError(f"{name}: {key} must be a list")
            fields = {
                "falsifiers": (
                    "id",
                    "side",
                    "text",
                    "due",
                    "check",
                    "threshold",
                    "window_blocks",
                    "window_days",
                    "closes",
                    "requires",
                ),
                "catalysts": ("id", "title", "due", "window", "status"),
                "alerts": (
                    "id",
                    "kind",
                    "threshold",
                    "threshold_pct",
                    "window_blocks",
                    "versus",
                    "baseline",
                ),
            }[key]
            meta[key], i = parse_pair_list(lines, i + 1, name, fields, key)
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


def opt_str(meta: dict, key: str, name: str) -> str:
    value = meta.get(key, "")
    if value is None or value == "":
        return ""
    if not isinstance(value, str):
        raise BuildError(f"{name}: frontmatter '{key}' must be a string")
    return value.strip()


def validate_desk(meta: dict, name: str) -> None:
    """Call, position, rating, and keys are optional. Render nothing when absent."""
    keys = meta.get("keys", None)
    if keys is None or keys == "":
        return
    if not isinstance(keys, list):
        raise BuildError(f"{name}: keys must be a list")
    for idx, item in enumerate(keys, 1):
        if not isinstance(item, dict):
            raise BuildError(f"{name}: key {idx} must be a mapping")
        label = str(item.get("label", "")).strip()
        value = str(item.get("value", "")).strip()
        if not label or not value:
            raise BuildError(f"{name}: key {idx} needs label and value")
    for list_key, required in (
        ("falsifiers", ("id", "side", "text", "check")),
        ("catalysts", ("id", "title", "status")),
        ("alerts", ("id", "kind")),
    ):
        items = meta.get(list_key, None)
        if items is None or items == "":
            continue
        if not isinstance(items, list):
            raise BuildError(f"{name}: {list_key} must be a list")
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                raise BuildError(f"{name}: {list_key} {idx} must be a mapping")
            for field in required:
                if not str(item.get(field, "")).strip():
                    raise BuildError(f"{name}: {list_key} {idx} needs {field}")
            side = str(item.get("side", "")).strip()
            if list_key == "falsifiers" and side not in ("bullish", "bearish"):
                raise BuildError(f"{name}: falsifier {idx} side must be bullish or bearish")


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
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?")


def check_images(body: str, article_path: Path) -> None:
    for match in IMAGE_RE.finditer(body):
        ref = match.group(1).strip()
        if ref.startswith(("http://", "https://", "data:")):
            continue
        rel = ref.split("?", 1)[0].split("#", 1)[0]
        if rel.startswith("/"):
            candidates = [ROOT / rel.lstrip("/")]
        else:
            candidates = [
                article_path.parent / rel,
                ROOT / rel,
                ARTICLES_DIR / rel,
            ]
        if not any(path.is_file() for path in candidates):
            raise BuildError(f"{article_path.name}: missing image {ref}")


# Block image: a line on its own, ![alt](/assets/<article>/<file> "optional caption")
IMG_RE = re.compile(r'^!\[([^\]\n]*)\]\((\S+?)(?:\s+"([^"\n]*)")?\)\s*$')
IMG_SRC_RE = re.compile(r"^/assets/[a-z0-9][a-z0-9._/-]*\.(svg|png|jpe?g|webp)$")


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


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def is_block_start(line: str) -> bool:
    return bool(
        not line.strip()
        or FENCE_RE.match(line)
        or HEADING_RE.match(line)
        or UL_RE.match(line)
        or OL_RE.match(line)
        or is_table_row(line)
        or IMG_RE.match(line)
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
    # Article title owns <h1>. ## is h2. ### is h3. A lone # is h2, not a second h1.
    raw = len(m.group(1))
    level = 2 if raw <= 2 else min(raw, 6)
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


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


def render_table(lines: list[str], i: int, out: list[str], name: str) -> int:
    header = split_table_row(lines[i])
    if i + 1 >= len(lines) or not TABLE_SEP_RE.match(lines[i + 1]):
        raise BuildError(f"{name}: table at line {i + 1} is missing a separator row")
    i += 2
    rows: list[list[str]] = []
    while i < len(lines) and is_table_row(lines[i]):
        cells = split_table_row(lines[i])
        if len(cells) != len(header):
            raise BuildError(
                f"{name}: table row has {len(cells)} cells, header has {len(header)}"
            )
        rows.append(cells)
        i += 1
    if not rows:
        raise BuildError(f"{name}: table has a header and no rows")
    head = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    body = []
    for row in rows:
        cells = "".join(
            f'<td data-label="{esc(header[idx])}">{render_inline(cell)}</td>'
            for idx, cell in enumerate(row)
        )
        body.append(f"<tr>{cells}</tr>")
    out.append(
        '<div class="table-wrap"><table>'
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )
    return i


VIEWBOX_RE = re.compile(r'viewBox="\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*"')


def figure_dims(src: str) -> tuple[str, str]:
    """Intrinsic size from the SVG viewBox. Without width and height, a lazy
    image collapses and never intersects, so the chart never paints."""
    text = (ROOT / src.lstrip("/")).read_text(encoding="utf-8")
    match = VIEWBOX_RE.search(text)
    if not match:
        return "", ""

    def px(raw: str) -> str:
        value = float(raw)
        return str(int(value)) if value.is_integer() else raw

    return px(match.group(1)), px(match.group(2))


def render_figure(m: re.Match, out: list[str], name: str) -> None:
    alt, src, caption = m.group(1).strip(), m.group(2), (m.group(3) or "").strip()
    if not alt:
        raise BuildError(f"{name}: image {src!r} needs alt text")
    if not IMG_SRC_RE.match(src) or ".." in src:
        raise BuildError(f"{name}: image src must be a local /assets/... path, got {src!r}")
    if not (ROOT / src.lstrip("/")).is_file():
        raise BuildError(f"{name}: image file not found: {src}")
    cap = f"<figcaption>{render_inline(caption)}</figcaption>" if caption else ""
    w, h = figure_dims(src)
    dims = f' width="{esc(w)}" height="{esc(h)}"' if w and h else ""
    out.append(
        f'<figure class="figure"><a href="{esc(src)}"><img src="{esc(src)}" alt="{esc(alt)}"{dims} '
        f'loading="eager" decoding="async"></a>{cap}</figure>'
    )


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
        elif IMG_RE.match(line):
            render_figure(IMG_RE.match(line), out, name)
            i += 1
        elif UL_RE.match(line):
            i = render_list(lines, i, out, UL_RE, "ul")
        elif OL_RE.match(line):
            i = render_list(lines, i, out, OL_RE, "ol")
        elif is_table_row(line):
            i = render_table(lines, i, out, name)
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
        validate_desk(self.meta, path.name)
        self.date = dt.date.fromisoformat(self.meta["date"])
        self.title = self.meta["title"].strip()
        self.summary = self.meta["summary"].strip()
        self.sources = self.meta["sources"]
        self.ticker = opt_str(self.meta, "ticker", path.name)
        self.rating = opt_str(self.meta, "rating", path.name)
        self.horizon = opt_str(self.meta, "horizon", path.name)
        self.conviction = opt_str(self.meta, "conviction", path.name)
        self.price = opt_str(self.meta, "price", path.name)
        self.call = opt_str(self.meta, "call", path.name)
        self.position = opt_str(self.meta, "position", path.name)
        self.keys = self.meta.get("keys") or []
        unlisted_raw = str(self.meta.get("unlisted", "")).strip().lower()
        self.unlisted = unlisted_raw in ("true", "1", "yes")
        self.body_text = body
        check_images(body, path)
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


ASSET_BY_SLUG = {"2026-10-02-pearl": "PRL"}
SECURITIES = [
    {"sym": "BTC", "name": "Bitcoin", "class": "Crypto", "cg": "bitcoin", "chart": "crypto", "chain": "BTC", "credit": desk_html.CREDIT, "credit_url": desk_html.CREDIT_URL},
    {"sym": "ETH", "name": "Ether", "class": "Crypto", "cg": "ethereum", "chart": "crypto", "chain": "ETH", "credit": desk_html.CREDIT, "credit_url": desk_html.CREDIT_URL},
    {"sym": "SOL", "name": "Solana", "class": "Crypto", "cg": "solana", "chart": "crypto", "chain": "SOL", "credit": desk_html.CREDIT, "credit_url": desk_html.CREDIT_URL},
    {"sym": "PRL", "name": "Pearl", "class": "Crypto", "cg": "pearl-2", "chart": "crypto", "chain": "PRL", "credit": desk_html.CREDIT, "credit_url": desk_html.CREDIT_URL},
    {"sym": "BTC.D", "name": "Bitcoin dominance", "class": "Index", "cg": "", "chart": "index", "chain": "", "credit": desk_html.CREDIT, "credit_url": desk_html.CREDIT_URL},
    {"sym": "TOTAL", "name": "Total crypto cap", "class": "Index", "cg": "", "chart": "index", "chain": "", "credit": desk_html.CREDIT, "credit_url": desk_html.CREDIT_URL},
    {"sym": "EURUSD", "name": "Euro reference rate", "class": "Crncy", "cg": "", "chart": "rate", "chain": "", "credit": "Source: ECB statistics", "credit_url": "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html"},
    {"sym": "UST2Y", "name": "Treasury par yield, 2 year", "class": "Govt", "cg": "", "chart": "rate", "chain": "", "credit": "U.S. Department of the Treasury", "credit_url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve"},
    {"sym": "UST10Y", "name": "Treasury par yield, 10 year", "class": "Govt", "cg": "", "chart": "rate", "chain": "", "credit": "U.S. Department of the Treasury", "credit_url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve"},
    {"sym": "SOFR", "name": "SOFR", "class": "M-Mkt", "cg": "", "chart": "rate", "chain": "", "credit": "Federal Reserve Bank of New York. The SOFR data is subject to the Terms of Use posted at newyorkfed.org.", "credit_url": "https://www.newyorkfed.org/markets/reference-rates/sofr"},
]
HOME_SYMBOLS = tuple(row["sym"] for row in SECURITIES if row["chart"] == "crypto")
VENDOR_SHA = "e21cc5caa0226ef30bd8549c50b9ef926615f2a4ee6b4e486353477a55f598cf"


def security_by_sym(sym: str) -> dict | None:
    want = sym.upper()
    for row in SECURITIES:
        if row["sym"] == want:
            return row
    return None


def article_asset(article: Article) -> str | None:
    raw = str(article.meta.get("asset", "")).strip().upper()
    if re.fullmatch(r"[A-Z0-9]{2,8}", raw):
        return raw
    return ASSET_BY_SLUG.get(article.dir_name)


def chip_placeholders() -> str:
    """Reserve the macro row so market.js can fill values without moving the source list."""
    rows = (
        ("UST10Y", "Source: U.S. Treasury"),
        ("UST2Y", "Source: U.S. Treasury"),
        ("SOFR", "Source: Federal Reserve Bank of New York"),
        ("EURUSD", "Source: ECB statistics"),
        ("BTC.D", "Source: CoinGecko"),
        ("TOTAL", "Source: CoinGecko"),
        ("F&G", "Source: alternative.me"),
    )
    return "".join(
        f'<span class="chip" role="listitem" tabindex="0" title="{esc(source)}" data-chip="{esc(cid)}">'
        f'<span class="chip-id">{esc(cid)}</span>'
        f'<span class="chip-px">…</span>'
        f'<span class="chip-asof">n/a</span>'
        f"</span>"
        for cid, source in rows
    )


def ticker_html() -> str:
    ticks = "\n    ".join(
        f'<span class="tick" data-symbol="{sym}"><span class="tick-sym">{sym}</span> '
        f'<span class="tick-px">…</span> <span class="tick-chg"></span></span>'
        for sym in HOME_SYMBOLS
    )
    return f"""<div class="ticker" id="ticker" role="region" aria-label="Aggregated prices">
  <div class="ticker-row sheet">
    <span class="tick tick-cmd" aria-hidden="true">&gt;_</span>
    {ticks}
    <span class="tick tick-state" id="ticker-state">loading</span>
  </div>
</div>
<p class="credit sheet">
  <a href="https://www.coingecko.com/" rel="noopener">Data provided by CoinGecko</a>
  <span class="credit-note">Aggregated price, not one exchange. Not a quote. Updates at most once a minute.</span>
</p>
<div class="chips sheet" id="chips" role="list" aria-label="Macro readings">{chip_placeholders()}</div>
<ul class="src-list sheet">
  <li>UST10Y and UST2Y: <a href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve" rel="noopener">U.S. Department of the Treasury</a>.</li>
  <li>SOFR: <a href="https://www.newyorkfed.org/markets/reference-rates/sofr" rel="noopener">Federal Reserve Bank of New York</a>. The SOFR data is subject to the Terms of Use posted at newyorkfed.org. The New York Fed is not responsible for publication of SOFR by alpha.kurult.ai, does not endorse this republication, and has no liability for your use.</li>
  <li>EURUSD: <a href="https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html" rel="noopener">Source: ECB statistics</a>. Daily reference rate.</li>
  <li>BTC.D and TOTAL: <a href="https://www.coingecko.com/" rel="noopener">Data provided by CoinGecko</a>.</li>
  <li>F&amp;G: <a href="https://alternative.me/crypto/fear-and-greed-index/" rel="noopener">Fear and Greed Index by alternative.me</a>.</li>
</ul>
<p class="visually-hidden" id="market-status" aria-live="polite"></p>
<noscript><p class="noscript sheet">Live readings need JavaScript. The notes do not.</p></noscript>"""


def chart_mount(symbols: tuple[str, ...], default: str, locked: bool) -> str:
    symbol_btns = "".join(
        f'<button type="button" class="seg-btn" data-symbol="{esc(sym)}" aria-pressed="{"true" if sym == default else "false"}"'
        f'{"" if not locked or sym == default else " disabled"}>{esc(sym)}</button>'
        for sym in symbols
    )
    tf_btns = "".join(
        f'<button type="button" class="seg-btn" data-tf="{tf}" aria-pressed="{"true" if tf == "1D" else "false"}">{tf}</button>'
        for tf in ("1H", "4H", "1D")
    )
    return f"""<section class="panel" id="chart-panel" data-symbols="{esc(",".join(symbols))}" data-default="{esc(default)}" data-locked="{"true" if locked else "false"}" aria-labelledby="chart-heading">
  <div class="panel-head"><span id="chart-heading">Chart</span><span class="badge" id="chart-badge">aggregated</span></div>
  <div class="panel-body">
    <div class="seg" role="group" aria-label="Asset">{symbol_btns}</div>
    <div class="seg" role="group" aria-label="Timeframe">{tf_btns}</div>
    <p class="chart-note" id="chart-note">Aggregated price, not one exchange. 1H is hourly, 4H is 4-hour OHLC, 1D is daily. Weekly is not offered.</p>
    <div class="chart-frame" id="chart-frame"><p class="chart-empty">Loading chart.</p></div>
    <p class="chart-readout" id="chart-readout"></p>
    <p class="src-foot"><a href="https://www.coingecko.com/" rel="noopener">Data provided by CoinGecko</a></p>
  </div>
</section>"""


def markets_mount() -> str:
    return """<section class="panel" id="markets-panel" aria-labelledby="markets-heading">
  <div class="panel-head"><span id="markets-heading">Markets</span><span class="badge" id="markets-badge">…</span></div>
  <div class="panel-body" id="markets-body"><p class="chart-empty">Loading markets.</p></div>
</section>"""


def chain_mount(scope: str) -> str:
    return f"""<section class="panel" id="chain-panel" data-chain="{esc(scope)}" aria-labelledby="chain-heading">
  <div class="panel-head"><span id="chain-heading">On-chain</span><span class="badge" id="chain-badge">…</span></div>
  <div class="panel-body" id="chain-body"><p class="chart-empty">Loading chain stats.</p></div>
  <p class="src-foot chain-credit">Bitcoin figures come from <a href="https://mempool.space/" rel="noopener">mempool.space</a>, with <a href="https://blockstream.info/" rel="noopener">Blockstream</a> as fallback. alpha.kurult.ai is not affiliated with either. Ether gas and Solana epoch come from public RPCs through our cache. Pearl chain stats, when shown, come from pearlchain.live and are not an affiliation.</p>
</section>"""


def script_tags(market_chrome: bool, chart: bool, lazy_chart: bool) -> str:
    tags = [
        '<script src="/desk-logic.js" defer></script>',
        '<script src="/search.js" defer></script>',
    ]
    if market_chrome:
        tags.append('<script src="/market.js" defer></script>')
    if chart and not lazy_chart:
        tags.append('<script src="/vendor/lightweight-charts-5.2.1.js" defer></script>')
    if chart:
        tags.append('<script src="/chart.js" defer></script>')
    return "\n".join(tags)


def asset_jump(securities: list[dict]) -> str:
    opts = ['<option value="">Asset</option>']
    for row in securities:
        opts.append(
            '<option value="%s">%s</option>' % (esc(desk_html.sym_path(row["sym"])), esc(row["sym"]))
        )
    return '<select class="asset-jump" aria-label="Asset">%s</select>' % "".join(opts)


def page(
    title: str,
    description: str,
    path: str,
    body: str,
    body_class: str,
    market_chrome: bool = True,
    chart: bool = False,
    lazy_chart: bool = False,
) -> str:
    chrome = ticker_html() if market_chrome else ""
    scripts = script_tags(market_chrome, chart, lazy_chart)
    securities = desk_html.securities_payload(SECURITIES)
    assets = desk_html.asset_links(SECURITIES)
    jump = asset_jump(SECURITIES)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self' https://api.coingecko.com https://markets.newyorkfed.org https://data-api.ecb.europa.eu https://api.alternative.me https://mempool.space https://blockstream.info; font-src 'self'; object-src 'none'; base-uri 'self'">
<link rel="canonical" href="{esc(SITE_URL + path)}">
<link rel="icon" href="/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="/styles.css">
</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <input class="search-open" id="search-open" type="checkbox">
  <div class="sheet masthead-row">
    <a class="wordmark" href="/" aria-label="{esc(SITE_BRAND)} home">
      <img class="mark" src="/mark.svg" alt="" width="22" height="22">
      <span class="wordmark-text">{esc(SITE_BRAND)}</span>
    </a>
    <span class="kicker">{esc(SITE_KICKER)}</span>
    <label class="search-toggle" for="search-open">Search</label>
    {jump}
  </div>
  <form class="sheet desk-search" role="search" action="/search/" method="get">
    <label class="visually-hidden" for="q">Search notes and assets</label>
    <input id="q" name="q" type="search" role="combobox" aria-expanded="false" aria-controls="search-list" aria-autocomplete="list" placeholder="Search notes and assets, e.g. pearl" autocomplete="off">
    <button type="submit">Search</button>
    <ul id="search-list" role="listbox" hidden></ul>
    <p id="search-live" class="visually-hidden" aria-live="polite"></p>
  </form>
</header>
<nav class="fnkeys" aria-label="Function keys">
  <div class="sheet fnkeys-row">
    <a class="fnkey" href="/">F1 LEDGER</a>
    <a class="fnkey" href="/help/">HELP</a>
    {assets}
  </div>
</nav>
{chrome}
<aside class="notice" role="note" aria-label="Disclaimer">
  <div class="sheet"><span class="notice-mark" aria-hidden="true">!</span>{esc(DISCLAIMER)}</div>
</aside>
<main id="main" class="sheet">
{body}
</main>
<footer class="colophon sheet">
  <span>{esc(SITE_NAME)}</span>
  <span class="colophon-sep" aria-hidden="true">|</span>
  <span class="colophon-credit"><a href="{desk_html.CREDIT_URL}" rel="noopener">{desk_html.CREDIT}</a></span>
  <span class="colophon-sep" aria-hidden="true">|</span>
  <a href="/help/">Help</a>
  <span class="colophon-sep" aria-hidden="true">|</span>
  <a href="/help/#credits">Credits</a>
  <span class="colophon-sep" aria-hidden="true">|</span>
  <span>No wallet. No comments. No analytics. No third-party script host.</span>
</footer>
<script type="application/json" id="alpha-securities">{securities}</script>
{scripts}
</body>
</html>
"""


def render_index_entry(article: Article, i: int) -> str:
    tape = render_tape(article)
    summary = article.call or article.summary
    return f"""  <li class="entry" style="--i:{i}">
    {tape}
    <h2 class="entry-title"><a href="{esc(article.path)}">{esc(article.title)}</a></h2>
    <p class="entry-summary">{esc(summary)}</p>
  </li>"""


def render_tape(article: Article) -> str:
    cells = [time_tag(article)]
    if article.ticker:
        cells.append(f'<span class="entry-ticker">{esc(article.ticker)}</span>')
    if article.rating:
        cells.append(f'<span class="entry-rating">{esc(article.rating)}</span>')
    if article.horizon:
        cells.append(f'<span class="entry-horizon">{esc(article.horizon)}</span>')
    if article.conviction:
        cells.append(f'<span class="entry-conviction">{esc(article.conviction)}</span>')
    if article.price:
        cells.append(f'<span class="entry-price">{esc(article.price)}</span>')
    if len(cells) == 1:
        return f'<p class="entry-tape">{cells[0]}</p>'
    sep = '<span class="pipe" aria-hidden="true">|</span>'
    return f'<p class="entry-tape">{sep.join(cells)}</p>'


def render_index(articles: list[Article]) -> str:
    n = len(articles)
    count = f"{n} {'entry' if n == 1 else 'entries'}"
    if articles:
        entries = "\n".join(render_index_entry(a, i) for i, a in enumerate(articles))
        ledger_core = f'<ol class="ledger" reversed>\n{entries}\n  </ol>'
    else:
        ledger_core = '<p class="empty">No entries filed.</p>'
    btc = security_by_sym("BTC")
    chart = desk_html.chart_panel(btc, SECURITIES, locked=False, lazy=True, home=True) if btc else ""
    body = f"""<div class="desk-grid">
  <div class="desk-chart-slot">{chart}</div>
  <div class="desk-markets">{markets_mount()}</div>
  <div class="desk-chain">{chain_mount("all")}</div>
  <section class="panel desk-intro">
    <div class="panel-head"><span>Alpha desk</span><span class="data">{esc(count)}</span></div>
    <div class="panel-body">
      <h1 class="command-title">{esc(SITE_NAME)}</h1>
      <p class="command-lede">{esc(SITE_TAGLINE)}</p>
    </div>
  </section>
  <section class="panel desk-ledger" id="ledger" aria-label="Article ledger">
    <div class="panel-head"><span>Ledger</span><span class="data">{esc(count)}</span></div>
{ledger_core}
  </section>
</div>"""
    return page(SITE_NAME, SITE_TAGLINE, "/", body, "page-index", chart=True, lazy_chart=True)


def render_sources(article: Article) -> str:
    items = "\n".join(
        f'    <li><a href="{esc(s["url"].strip())}" rel="noopener">{esc(s["label"].strip())}</a>'
        f'<span class="source-url">{esc(s["url"].strip())}</span></li>'
        for s in article.sources
    )
    return f"""<section class="sources panel" aria-labelledby="sources-heading">
  <div class="panel-head"><span id="sources-heading">Sources</span><span class="data">{len(article.sources)} ref</span></div>
  <ol class="source-table">
{items}
  </ol>
</section>"""


def render_tearsheet(article: Article) -> str:
    parts: list[str] = []
    if article.call:
        ticker = f"<strong>{esc(article.ticker)}.</strong> " if article.ticker else ""
        parts.append(f'  <p class="callstrip">{ticker}{esc(article.call)}</p>')
    if article.position:
        parts.append(f'  <p class="position-box">{esc(article.position)}</p>')
    cell_bits: list[str] = []
    for item in article.keys:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        value = str(item.get("value", "")).strip()
        if not label or not value:
            continue
        note = str(item.get("note", "")).strip()
        note_html = f'<span class="key-note">{esc(note)}</span>' if note else ""
        cell_bits.append(f"<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd>{note_html}</div>")
    if cell_bits:
        parts.append(f'  <dl class="keystrip">{"".join(cell_bits)}</dl>')
    if not parts:
        return ""
    return "\n".join(parts) + "\n"


def render_article(article: Article) -> str:
    asset = article_asset(article)
    row = security_by_sym(asset) if asset else None
    rail_bits = [render_tearsheet(article)]
    chart = False
    if row and row.get("chart") == "crypto":
        rail_bits.append(desk_html.chart_panel(row, SECURITIES, locked=True, lazy=False, home=False))
        rail_bits.append(chain_mount(asset or ""))
        chart = True
    elif asset:
        rail_bits.append(chain_mount(asset))
    rail = "\n".join(bit for bit in rail_bits if bit)
    panels = desk_sections(article.meta, ROOT)
    desk = f'\n  <div class="article-desk">\n{panels}\n  </div>' if panels else ""
    body = f"""<div class="article-layout">
  <aside class="article-rail">
{rail}
  </aside>
  <article class="article panel">
    <div class="panel-head"><span><a href="/">&laquo; Ledger</a></span><span class="data">{time_tag(article)}</span></div>
    <header class="article-head">
      <h1 class="article-title">{esc(article.title)}</h1>
      <p class="article-lede">{esc(article.summary)}</p>
    </header>
    <div class="prose">
{article.body_html}
    </div>
  </article>{desk}
</div>
{render_sources(article)}"""
    return page(
        f"{article.title} | {SITE_NAME}",
        article.summary,
        article.path,
        body,
        "page-article",
        market_chrome=False,
        chart=chart,
        lazy_chart=False,
    )


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

STYLES = """/* Terminal palette.
   Sampled 2026-10-02 from reference terminal screenshots, not from a brand sheet.

   Screen colors: reference terminal screenshots.
   Left monitor of an in-use terminal. Glyph cores are local-maxima pixels
   so antialiased edges do not darken the ink. Solid fills are
   4-neighbor-stable pixels.

   --bg      #000000  pure black field. Empty cells in the photo are
                      near-black; JPEG noise keeps them off zero, so this
                      is the terminal field, not a sampled nonzero hex.
   --amber   #f1bd59  primary text and labels. Median of orange glyph cores
                      (hue 16-46). 12.16:1 on #000000. 9.79:1 on --blue.
   --data    #ffffff  data values. Unsaturated white-family p90 on the same
                      screen was #ffffff. Core median was #e4feff, a
                      camera/LCD cyan cast, so the chosen value is the p90.
                      21:1 on #000000. 16.89:1 on --blue.
   --yellow  #f8c800  on-screen highlight fill. Mode of solid yellow fills
                      (the CLM6 COMB highlight bar). Black text on it is 13.25:1.
   --key     #c89830  function-key yellow. Mode of the yellow key row in
                      a reference terminal screenshot, crop y=580-640.
                      Black text on it is 7.99:1.
   --blue    #001060  header, title bar, and panel-header fill. Mode of the
                      solid blue command-bar fill (n=34962 in the dense stripe).
                      Not used as text on black (1.24:1, would fail AA).
   --up      #39d441  up. Median of green glyph cores. 10.67:1 on #000000.
   --down    #dc5d5e  down. Median of red glyph cores. 5.77:1 on #000000.
                      The red Actions-bar fill #c0132a is 3.37:1 and is not used.
   --rule    #507098  hairline only, from the header-row blue mode. Not used
                      as text: amber on it is 2.96:1.

   No lightness adjustment. Every text color above clears WCAG AA 4.5:1 on
   the background it is painted on. Focus is a 2px #f8c800 outline, offset
   2px, so it sits on black (13.25:1) or on the blue bar (10.66:1).
*/
:root {
  --bg: #000000;
  --panel: #000000;
  --panel-head: #001060;
  --amber: #f1bd59;
  --amber-mid: #f1bd59;
  --amber-dim: #f1bd59;
  --amber-faint: #f1bd59;
  --text: #f1bd59;
  --text-dim: #f1bd59;
  --data: #ffffff;
  --yellow: #f8c800;
  --key: #c89830;
  --blue: #001060;
  --up: #39d441;
  --down: #dc5d5e;
  --go: #39d441;
  --stop: #c0132a;
  --field: #f1bd59;
  --rule: #507098;
  --edge: #507098;
  --edge-soft: #1a2a55;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace;
  --serif: Georgia, serif;
  --gutter: clamp(1rem, 3vw, 2rem);
}

*, *::before, *::after { box-sizing: border-box; }

html {
  background: var(--bg);
  color: var(--text);
  font-family: var(--mono), var(--serif);
  font-size: 100%;
  -webkit-text-size-adjust: 100%;
  text-rendering: optimizeLegibility;
  overflow-x: clip;
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
  overflow-x: clip;
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
    rgba(241, 189, 89, .04) 0,
    rgba(241, 189, 89, .04) 1px,
    transparent 1px,
    transparent 3px
  );
}

::selection { background: var(--yellow); color: #000; }

a { color: var(--amber); text-decoration-color: var(--rule); text-underline-offset: .18em; }
a:hover { background: var(--yellow); color: #000; text-decoration: none; }
:focus-visible { outline: 2px solid var(--yellow); outline-offset: 2px; }
.fnkey:focus-visible, .skip:focus-visible { outline-color: var(--yellow); }

.sheet { width: 100%; max-width: none; margin-inline: 0; padding-inline: var(--gutter); }

.skip {
  position: absolute;
  left: var(--gutter);
  top: -3rem;
  background: var(--key);
  color: #000;
  padding: .5rem .75rem;
  font-size: .8rem;
  text-decoration: none;
  z-index: 10;
}
.skip:focus { top: .5rem; }

/* Masthead: blue title bar ----------------------------------------------- */
.masthead {
  background: var(--blue);
  border-bottom: 2px solid var(--rule);
  color: var(--amber);
}
.masthead-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-block: .7rem;
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
  /* 44px tap target; the negative margin keeps the masthead height unchanged. */
  min-height: 44px;
  margin-block: -9px;
  box-sizing: border-box;
}
.wordmark:hover { background: var(--yellow); color: #000; }
.mark { width: 22px; height: 22px; display: block; flex: none; }
.kicker {
  font-size: .72rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--amber);
}

/* Function keys ------------------------------------------------------------ */
.fnkeys { background: var(--bg); border-bottom: 1px solid var(--edge); }
.fnkeys-row {
  display: flex;
  flex-wrap: wrap;
  gap: .4rem;
  padding-block: .45rem;
}
.fnkey, .tick-cmd {
  display: inline-block;
  background: var(--key);
  color: #000;
  font-weight: 700;
  letter-spacing: .08em;
  text-decoration: none;
  text-transform: uppercase;
  padding: .15rem .45rem;
  border: 1px solid #000;
}
.fnkey:hover, .tick-cmd:hover { background: var(--yellow); color: #000; }

/* Ticker bar -------------------------------------------------------------- */
.ticker { border-block: 1px solid var(--edge); background: #000; overflow-x: clip; }
.ticker-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  /* Command chip is taller than a price. Three rows are reserved so a
     fetched price cannot add a line and push the source list. */
  grid-template-rows: 1.75rem 1.4rem 1.4rem;
  gap: .15rem .55rem;
  padding-block: .5rem;
  font-size: .72rem;
  letter-spacing: .02em;
  text-transform: uppercase;
  align-items: center;
  overflow: hidden;
}
.ticker-row .tick { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
@media (min-width: 900px) {
  .ticker-row {
    display: flex;
    flex-wrap: nowrap;
    gap: .25rem 1.1rem;
    letter-spacing: .10em;
    overflow-x: auto;
    scrollbar-width: none;
  }
  .ticker-row::-webkit-scrollbar { display: none; }
  .ticker-row .tick { overflow: visible; text-overflow: clip; min-width: auto; }
}
.tick { color: var(--data); white-space: nowrap; }
.tick-sym { color: var(--amber); }
.tick-up { color: var(--up); }
.tick-down { color: var(--down); }
.tick-state { color: var(--amber); }
.tick-stale, .tick-na { color: var(--amber); }
.tick.tick-cmd { color: #000; background: var(--key); }
.tick.flash { animation: flash .3s ease; }
@keyframes flash {
  from { background: rgba(241, 189, 89, .28); }
  to { background: transparent; }
}

.credit { margin: .45rem auto 0; font-size: .75rem; color: var(--text-dim); }
.credit a { color: var(--amber); }
.credit-note { display: block; margin-top: .15rem; }
.chips {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: .4rem;
  padding-block: .7rem .2rem;
}
@media (min-width: 900px) {
  .chips { grid-template-columns: repeat(7, minmax(0, 1fr)); }
}
.chip {
  display: grid;
  gap: .05rem;
  min-width: 0;
  min-height: 3.6rem;
  padding: .35rem .5rem;
  border: 1px solid var(--edge);
  background: #000;
  color: var(--text);
}
.chip-id, .chip-px, .chip-asof {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chip-id { color: var(--amber); font-size: .68rem; letter-spacing: .08em; }
.chip-px { font-size: .84rem; }
.chip-asof { color: var(--text-dim); font-size: .68rem; }
.chip-stale .chip-asof { color: var(--amber-mid); }
.src-list {
  width: auto;
  max-width: calc(100% - 2 * max(1rem, var(--gutter)));
  margin: 0 auto .4rem;
  padding-block: 0 .4rem;
  padding-inline: 0;
  list-style: none;
  font-size: .72rem;
  line-height: 1.45;
  color: var(--text-dim);
  overflow-wrap: anywhere;
}
.src-list li { margin: .2rem 0; overflow-wrap: anywhere; }
.noscript { color: var(--amber-mid); font-size: .78rem; }
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.seg { display: flex; flex-wrap: wrap; gap: .35rem; margin: 0 0 .7rem; }
.seg-btn {
  font: inherit;
  font-size: .72rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text);
  background: #000;
  border: 1px solid var(--edge);
  padding: .35rem .55rem;
  cursor: pointer;
}
.seg-btn[aria-pressed="true"] { color: #000; background: var(--amber); border-color: var(--amber); }
.seg-btn:disabled, .seg-btn.is-blocked { opacity: 1; color: var(--amber); background: #000; border-style: dashed; cursor: not-allowed; }
.seg-btn:focus-visible, .chip:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
.chart-note, .chart-readout, .src-foot, .breadth, .macro-line {
  color: var(--text-dim);
  font-size: .75rem;
  margin: .35rem 0;
}
.chart-empty { color: var(--text-dim); margin: 0; }
.chart-svg { width: 100%; height: auto; display: block; }
.badge { color: var(--text-dim); }
.desk-split { display: grid; gap: 1.25rem; }
.mkt-grid { display: grid; gap: 1rem; }
.mkt { width: 100%; border-collapse: collapse; font-size: .78rem; }
.mkt th, .mkt td { text-align: right; padding: .28rem .35rem; border-bottom: 1px solid var(--edge-soft); }
.mkt th:first-child, .mkt td:first-child { text-align: left; }
.mkt th { color: var(--amber); font-weight: 700; letter-spacing: .06em; }
.mkt-title { margin: 0 0 .3rem; color: var(--amber); font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; }
.chain-list { margin: 0; padding-left: 1.1rem; color: var(--text); }
.chain-card { margin: 0 0 .9rem; }
.chain-credit { padding: 0 .9rem .8rem; }

/* Disclaimer strip -------------------------------------------------------- */
.notice {
  border-bottom: 1px solid var(--edge-soft);
  background: #000;
  font-size: .74rem;
  line-height: 1.6;
  color: var(--amber);
}
.notice .sheet { padding-block: .55rem; display: flex; flex-wrap: wrap; gap: .6rem; align-items: baseline; min-width: 0; }
.notice-mark { color: var(--down); font-weight: 700; flex: none; }

main { flex: 1; padding-block: 1.75rem 3rem; display: grid; gap: 1.25rem; grid-template-columns: minmax(0, 1fr); }

/* Panels ------------------------------------------------------------------ */
.panel { border: 1px solid var(--edge); background: var(--panel); }
.panel-head {
  display: flex;
  justify-content: space-between;
  gap: .5rem 1rem;
  flex-wrap: wrap;
  padding: .45rem .9rem;
  background: var(--blue);
  border-bottom: 2px solid var(--rule);
  font-size: .70rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--amber);
}
.panel-head a { color: var(--amber); text-decoration: none; }
/* 44px tap target for head links such as the Ledger breadcrumb; the negative
   margin keeps the head height, so the phone fold does not move. */
.panel-head a { display: inline-flex; align-items: center; min-height: 44px; margin-block: -16px; vertical-align: middle; }
.panel-head a:hover { background: var(--yellow); color: #000; }
.panel-head .data, .panel-head time { color: var(--data); letter-spacing: .06em; text-transform: none; }
.panel-body { padding: 1.1rem 1.15rem 1.25rem; min-width: 0; }
.panel-error { border-color: var(--down); }
.panel-error .panel-head {
  color: var(--down);
  background: #000;
  border-bottom-color: var(--down);
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
  display: flex;
  flex-direction: column;
  gap: .2rem;
  padding: .7rem .9rem;
  border-bottom: 1px solid var(--edge-soft);
  min-width: 0;
  animation: rise .3s ease both;
  animation-delay: calc(var(--i, 0) * 60ms);
}
.entry:last-child { border-bottom: 0; }
.entry:hover,
.entry:hover .entry-tape,
.entry:hover .entry-title a,
.entry:hover .entry-summary { background: var(--yellow); color: #000; }
.entry-tape {
  display: flex;
  flex-wrap: wrap;
  gap: .15rem .4rem;
  margin: 0;
  font-size: .74rem;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--data);
  min-width: 0;
}
.entry-tape .pipe { color: var(--amber); }
.entry-title { margin: 0; font-size: 1.02rem; line-height: 1.3; font-weight: 700; }
.entry-title a { color: var(--amber); text-decoration: none; }
.entry-title a:hover { background: none; color: #000; text-decoration: underline; }
.entry-title a:focus-visible { outline-offset: 2px; }
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
.article-head { padding: .7rem 1.15rem 0; }
.page-article main { padding-top: .4rem; gap: .7rem; }
.page-article .article-head { padding-top: .3rem; }
.page-article .notice .sheet { padding-block: .3rem; }
.page-article .callstrip { padding: .3rem .55rem; margin-bottom: .3rem; }
.page-article .position-box { padding: .28rem .55rem; margin-bottom: .3rem; }
.page-article .keystrip { margin-bottom: .45rem; }
.page-article .keystrip div { padding: .2rem .4rem; }
.callstrip {
  font-family: var(--mono);
  font-size: .78rem;
  letter-spacing: .04em;
  text-transform: uppercase;
  border: 1px solid var(--rule);
  padding: .45rem .7rem;
  margin: 0 0 .45rem;
}
.callstrip strong { color: var(--amber); }
.position-box {
  border: 1px solid var(--edge);
  padding: .4rem .7rem;
  margin: 0 0 .45rem;
  font-size: .84rem;
  line-height: 1.35;
}
.keystrip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  background: var(--edge);
  border: 1px solid var(--edge);
  margin: 0 0 .7rem;
}
.keystrip div { background: #000; padding: .32rem .5rem; min-width: 0; }
.keystrip dt {
  font-size: .68rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--amber);
}
.keystrip dd {
  margin: 0;
  color: var(--data);
  font-size: .84rem;
  overflow-wrap: anywhere;
}
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

.prose { padding: 1.15rem 1.15rem 1.4rem; min-width: 0; overflow-wrap: break-word; }
.table-wrap { min-width: 0; max-width: 100%; overflow-x: clip; }
figure, table, pre { max-width: 100%; }
.prose table {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: .78rem;
  margin: 0 0 1.1em;
}
.prose th, .prose td {
  border: 1px solid var(--edge);
  padding: .4rem .5rem;
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
}
.prose th {
  background: var(--blue);
  color: var(--amber);
  letter-spacing: .06em;
  text-transform: uppercase;
  font-weight: 700;
}
.prose td { color: var(--data); }
.prose > * { margin-block: 0 1.1em; }
.prose p, .prose li { color: var(--text); }
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
  background: var(--blue);
  color: var(--amber);
  border-bottom: 2px solid var(--rule);
  padding: .35rem .6rem;
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
  color: var(--data);
  background: #000;
  border: 1px solid var(--edge);
  padding: .08em .3em;
}
.prose pre {
  font-size: .8rem;
  line-height: 1.6;
  background: #000;
  border: 1px solid var(--edge-soft);
  border-left: 3px solid var(--yellow);
  padding: .9rem 1rem;
  max-width: 100%;
  overflow-x: auto;
  color: var(--data);
}
.prose pre code { background: none; padding: 0; font-size: inherit; color: inherit; }
.prose figure { margin: 2.2em 0; width: 100%; max-width: 100%; }
.prose figure a { display: block; text-decoration: none; }
.prose figure img {
  display: block;
  width: 100%;
  height: auto;
  border: 1px solid var(--edge);
  background: var(--bg);
}
.prose figcaption {
  margin-top: .6rem;
  font-family: var(--mono);
  font-size: .7rem;
  line-height: 1.55;
  color: var(--data);
}

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
.source-table a { color: var(--text); text-decoration: none; overflow-wrap: anywhere; }
.source-url {
  grid-column: 2;
  display: none;
  font-size: .7rem;
  color: var(--data);
  overflow-wrap: anywhere;
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
.colophon { align-items: center; }
.colophon a { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; min-width: 44px; }
.search-all a { display: flex; align-items: center; min-height: 44px; }

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
@media (min-width: 40rem) {
  .keystrip { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 48rem) {
  .entry { grid-template-columns: 7.5rem minmax(0, 1fr); }
  .entry-summary { grid-column: 2; }
}
@media (min-width: 64rem) {
  .desk-split { grid-template-columns: minmax(0, 1.4fr) minmax(0, .8fr); }
  .mkt-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 72rem) {
  .entry { grid-template-columns: 7.5rem 17rem minmax(0, 1fr); }
  .entry-summary { grid-column: 3; }
}

/* Narrow ------------------------------------------------------------------ */
@media (max-width: 40rem) {
  .keystrip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .prose table, .prose thead, .prose tbody, .prose tr, .prose th, .prose td {
    display: block;
    width: 100%;
  }
  .prose thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
  }
  .prose tr {
    border: 1px solid var(--edge);
    margin: 0 0 .75rem;
    padding: .35rem .55rem;
  }
  .prose td { border: 0; padding: .28rem 0; }
  .prose td::before {
    content: attr(data-label);
    display: block;
    font-size: .68rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--amber);
  }
}
@media (max-width: 48rem) {
  .masthead-row { flex-direction: column; align-items: flex-start; gap: .45rem; }
  .prose, .article-head { padding-inline: .9rem; }
  .panel-head { padding: .4rem .7rem; }
  .entry { padding: .65rem .7rem; }
  .source-table li { padding-inline: .7rem; grid-template-columns: 2.2rem minmax(0, 1fr); }
}

/* Phone fold: key numbers sit under the call and above the position box.
   Desktop source order (call, position, keys) is unchanged above 700px. */
@media (max-width: 700px) {
  .article-head { display: flex; flex-direction: column; min-width: 0; }
  .article-head .callstrip { order: 1; margin-bottom: .3rem; }
  .article-head .keystrip { order: 2; margin-bottom: .3rem; }
  .article-head .position-box { order: 3; }
  .article-head .article-title { order: 4; }
  .article-head .article-lede { order: 5; }
  .keystrip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .keystrip div {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    align-items: baseline;
    column-gap: .28rem;
    padding: .12rem .28rem;
  }
  .keystrip dd { order: 1; font-size: .7rem; line-height: 1.1; }
  .keystrip dt { order: 2; font-size: .52rem; line-height: 1.1; letter-spacing: .02em; overflow-wrap: anywhere; min-width: 0; }
  .keystrip .key-note { display: none; }
}

.desk { margin: .6rem 0; }
.desk-table { width: 100%; border-collapse: collapse; font-size: .72rem; }
.desk-table th, .desk-table td { border-bottom: 1px solid var(--edge); text-align: left; padding: .28rem .35rem; vertical-align: top; }
.desk-table th { color: var(--amber); font-weight: 500; }
.draft-banner { color: var(--yellow); }
.draft-pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: .68rem; }
.spark { display: inline-block; vertical-align: middle; }

@media print {
  body { background: #fff; color: #000; }
  body::before, .ticker, .fnkeys { display: none; }
  .panel { border-color: #000; background: #fff; }
  .panel-head, .notice, .colophon { color: #000; border-color: #000; background: none; }
  a { color: #000; background: none; }
  .source-url { display: block; color: #000; }
}

/* Full-width desk grid. Mobile stays one column. */
.desk-grid, .asset-layout, .article-layout { display: grid; gap: 1rem; grid-template-columns: minmax(0, 1fr); }
.desk-chart-slot, .desk-markets, .desk-chain, .desk-intro, .desk-ledger, .asset-main, .asset-rail, .article-rail, .article, .article-desk { min-width: 0; }
.chart-plot { height: 28rem; width: 100%; max-width: 100%; touch-action: pan-y; }
.chart-plot canvas, .chart-plot table, .chart-plot * { touch-action: pan-y !important; }
.chart-toolbar, .seg, .fnkeys-row, .desk-search { max-width: 100%; }
.chart-toolbar .seg-btn, .asset-link, .desk-search input, .desk-search button, .fnkey, .search-toggle, .asset-jump { min-height: 44px; min-width: 44px; }
.desk-search { display: flex; flex-wrap: wrap; gap: .4rem; padding-block: .45rem; align-items: center; }
.desk-search input { flex: 1 1 12rem; font: inherit; background: #000; color: var(--data); border: 1px solid var(--field); padding: .35rem .55rem; }
.desk-search input:focus { background: var(--field); color: #000; }
.desk-search button { font: inherit; background: var(--go); color: #000; border: 1px solid #000; padding: .35rem .7rem; cursor: pointer; }
.search-list, #search-list { list-style: none; margin: 0; padding: 0; width: 100%; background: #000; border: 1px solid var(--edge); }
.search-list [role="option"], #search-list [role="option"] { padding: .45rem .55rem; cursor: pointer; }
.search-group { color: var(--amber); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; padding: .35rem .55rem; }
.chart-legend, .chart-last, .tick, .chip, .mkt { font-variant-numeric: tabular-nums; }
.chart-legend { color: var(--data); min-height: 2.4rem; }
.chart-volume-label, .range-block, .crumbs { color: var(--amber); font-size: .75rem; }
.crumbs a { display: inline-flex; align-items: center; min-height: 44px; min-width: 44px; padding-inline: .35rem; }
.chart-head { color: var(--data); margin: 0 0 .4rem; }
.chart-name, .chart-ticker { color: var(--amber); }
.compare-row { border: 1px solid var(--edge-soft); padding: .45rem; margin: 0 0 .45rem; }
.tick-on { outline: 1px solid var(--amber); }
@media (max-width: 40rem) { .chart-plot { height: 18rem; } }
@media (min-width: 48rem) {
  .desk-grid, .asset-layout { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .desk-chart-slot, .desk-intro, .desk-ledger { grid-column: 1 / -1; }
  .ledger { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .article-layout { grid-template-columns: minmax(0, 1fr) minmax(16rem, 24rem); align-items: start; }
  .article { grid-column: 1; grid-row: 1; }
  .article-rail { grid-column: 2; grid-row: 1 / span 2; }
  .article-desk { grid-column: 1; grid-row: 2; }
}
@media (min-width: 90rem) {
  .desk-grid, .asset-layout { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .desk-chart-slot { grid-column: span 2; }
  .desk-intro, .desk-ledger { grid-column: 1 / -1; }
  .ledger { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .asset-main { grid-column: span 1; grid-row: 1; }
  .asset-rail { grid-column: span 3; grid-row: 1; }
  .article-layout { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(18rem, 26rem); }
  .article { grid-column: 1 / span 2; grid-row: 1; }
  .article-rail { grid-column: 3; grid-row: 1 / span 2; }
  .article-desk { grid-column: 1 / span 2; grid-row: 2; }
}
@media (max-width: 700px) {
  .article-layout { gap: 0; }
  .article-rail { display: contents; }
  .article { display: contents; }
  .article > .panel-head { order: 0; margin-inline: 1px; }
  .article-layout .callstrip { order: 1; }
  .article-layout .keystrip { order: 2; }
  .article-layout .position-box { order: 3; }
  .article-head { order: 4; }
  .prose { order: 5; }
  .article-desk { order: 6; }
  .article-layout .desk-chart, .article-layout #chain-panel { order: 7; }
  .page-article .callstrip,
  .page-article .keystrip,
  .page-article .position-box { margin-inline: calc(.9rem + 1px); }
  .page-article .callstrip { margin-top: .3rem; }
}
.search-open {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
.search-toggle, .asset-jump { display: none; }
.fnkey {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}
.search-list [role="option"], #search-list [role="option"] { min-height: 44px; display: flex; align-items: center; }
@media (max-width: 700px) {
  .masthead { min-height: 77px; box-sizing: border-box; }
  .masthead-row {
    flex-direction: row;
    align-items: center;
    gap: .4rem;
    padding-block: .4rem;
  }
  .kicker { display: none; }
  .wordmark { min-width: 0; flex: 1 1 auto; }
  .wordmark-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .search-toggle, .asset-jump { display: inline-flex; }
  .search-toggle {
    background: var(--key);
    color: #000;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    border: 1px solid #000;
    padding: 0 .55rem;
    cursor: pointer;
  }
  .asset-jump {
    font: inherit;
    background: #000;
    color: var(--data);
    border: 1px solid var(--field);
    max-width: 7.5rem;
  }
  .fnkeys { display: block; height: 47px; overflow: hidden; }
  .fnkeys-row { flex-wrap: nowrap; padding-block: 1px; align-items: center; }
  .fnkeys .asset-select { display: none; }
  .fnkey { height: 44px; }
  .desk-search { display: none; }
  .search-open:checked ~ .desk-search { display: flex; }
  .search-open:focus-visible + .masthead-row .search-toggle {
    outline: 2px solid var(--yellow);
    outline-offset: 2px;
  }
}
"""

# --------------------------------------------------------------------------- #
# Text artefacts
# --------------------------------------------------------------------------- #


def render_robots() -> str:
    return (
        "User-agent: *\nAllow: /\nDisallow: /drafts/\n\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )


def render_llms(articles: list[Article]) -> str:
    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_TAGLINE}",
        "",
        DISCLAIMER,
        "",
        "First-party scripts only. No third-party script host. No wallet. No comments. No analytics.",
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
    entries = [url(SITE_URL + "/", newest), url(SITE_URL + "/help/", newest), url(SITE_URL + "/search/", newest)]
    entries += [url(SITE_URL + desk_html.sym_path(row["sym"]), newest) for row in SECURITIES]
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
    if "\u2014" in content:
        raise BuildError(f"em dash in {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def copy_shipped(src: Path, dest: Path) -> None:
    if not src.is_file():
        raise BuildError(f"missing {src}")
    text = src.read_bytes()
    if b"\xe2\x80\x94" in text and src.suffix in {".js", ".css", ".html", ".py"}:
        raise BuildError(f"em dash in {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    print(f"  copied {dest.relative_to(ROOT)}")


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
    # Grading notes and alert drafts stay in drafts/. They are not deploy pages.
    # payee-50 is internal. It is not rendered on the public panel.
    # robots Disallow is not a publish gate.
    notice_path = ROOT / "static" / "vendor" / "NOTICE-lightweight-charts"
    if not notice_path.is_file():
        raise BuildError("missing chart library NOTICE")
    notice = notice_path.read_text(encoding="utf-8")
    write(DIST / "help" / "index.html", page("Help | " + SITE_NAME, "Codes, sources, and credits.", "/help/", desk_html.render_help(notice), "page-help", market_chrome=False))
    index = desk_html.search_index(listed, SECURITIES)
    write(DIST / "search" / "index.html", page("Search | " + SITE_NAME, "Search notes and assets.", "/search/", desk_html.render_search_page(index), "page-search"))
    write(DIST / "search.json", json.dumps(index, indent=2) + "\n")
    for row in SECURITIES:
        chain = chain_mount(row["chain"]) if row.get("chain") else ""
        asset_body = desk_html.render_asset_body(row, listed, SECURITIES, chain)
        has_chart = row.get("chart") == "crypto"
        write(
            DIST / "s" / row["sym"].lower() / "index.html",
            page(
                f"{row['sym']} | {SITE_NAME}",
                f"{row['name']}. {row['credit']}",
                desk_html.sym_path(row["sym"]),
                asset_body,
                "page-asset",
                chart=has_chart,
            ),
        )
    write(DIST / "404.html", render_404())
    write(DIST / "styles.css", STYLES)
    for name in ("market.js", "desk-logic.js", "search.js", "chart.js"):
        copy_shipped(ROOT / "static" / name, DIST / name)
    vendor_src = ROOT / "static" / "vendor" / "lightweight-charts-5.2.1.js"
    vendor_sha = hashlib.sha256(vendor_src.read_bytes()).hexdigest()
    publish = (ROOT / "PUBLISH.md").read_text(encoding="utf-8")
    if vendor_sha != VENDOR_SHA or vendor_sha not in publish:
        raise BuildError(f"chart library sha mismatch: {vendor_sha}")
    vendor_dest = DIST / "vendor"
    vendor_dest.mkdir(parents=True)
    copy_shipped(vendor_src, vendor_dest / "lightweight-charts-5.2.1.js")
    copy_shipped(ROOT / "static" / "vendor" / "LICENSE-lightweight-charts", vendor_dest / "LICENSE-lightweight-charts")
    copy_shipped(notice_path, vendor_dest / "NOTICE-lightweight-charts")
    write(DIST / "robots.txt", render_robots())
    write(DIST / "llms.txt", render_llms(listed))
    write(DIST / "sitemap.xml", render_sitemap(listed))
    shutil.copyfile(MARK_SRC, DIST / "mark.svg")
    print("  copied mark.svg")
    if ASSETS_DIR.is_dir():
        shutil.copytree(ASSETS_DIR, DIST / "assets")
        print("  copied assets/")


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
