"""P0 pages for the desk: chart mount, asset pages, search, help.

The securities table itself lives in build.py. This module only renders.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any


CREDIT = "Data provided by CoinGecko"
CREDIT_URL = "https://www.coingecko.com/"
BLOCKED_RANGE = "Needs more than 1 year of licensed history"

RANGES = ("1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "Max")
LIVE_RANGES = {"1D", "5D", "1M", "3M", "6M", "YTD", "1Y"}

CODES = (
    {"code": "DES", "title": "Asset page", "example": "PRL DES", "status": "live", "detail": "Opens the asset page, with the latest note linked."},
    {"code": "GP", "title": "Price chart, line", "example": "BTC GP", "status": "live", "detail": "Opens the asset chart at 1Y, line."},
    {"code": "GIP", "title": "Intraday chart", "example": "BTC GIP", "status": "live", "detail": "Opens the asset chart at 1D, line."},
    {"code": "GPO", "title": "Bar chart", "example": "BTC GPO", "status": "live", "detail": "Opens the asset chart at 1Y, bars."},
    {"code": "GPC", "title": "Candle chart", "example": "BTC GPC", "status": "live", "detail": "Opens the asset chart at 1Y, candles."},
    {"code": "COMP", "title": "Compare", "example": "COMP BTC ETH", "status": "live", "detail": "Opens a compare view, rebased to 100. Max 4 extra series."},
    {"code": "TOP", "title": "Ledger", "example": "TOP", "status": "live", "detail": "Opens the research ledger."},
    {"code": "HELP", "title": "Help", "example": "HELP", "status": "live", "detail": "Opens this page."},
    {"code": "GMM", "title": "Markets", "example": "GMM", "status": "live", "detail": "Opens the markets panel."},
    {"code": "MOST", "title": "Markets", "example": "MOST", "status": "live", "detail": "Same as GMM."},
    {"code": "BTMM", "title": "Rates", "example": "BTMM", "status": "live", "detail": "Opens the rates strip."},
    {"code": "5Y", "title": "Five-year chart", "example": "5Y", "status": "not buildable", "detail": BLOCKED_RANGE},
    {"code": "Max", "title": "Max chart", "example": "Max", "status": "not buildable", "detail": BLOCKED_RANGE},
    {"code": "ECO", "title": "Economic calendar", "example": "ECO", "status": "not buildable", "detail": "Follow-on. Not in this release."},
    {"code": "EVTS", "title": "Events calendar", "example": "EVTS", "status": "not buildable", "detail": "No licensed events source yet."},
    {"code": "CSV", "title": "Export table", "example": "CSV", "status": "not buildable", "detail": "CoinGecko download is not approved. No CSV of that data."},
    {"code": "AAPL GP", "title": "Equity chart", "example": "AAPL GP", "status": "not buildable", "detail": "No licensed equity source yet."},
    {"code": "RSI", "title": "RSI study", "example": "RSI", "status": "not buildable", "detail": "Follow-on study. Not in this release."},
)


def esc(text: object) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def sym_path(sym: str) -> str:
    return f"/s/{sym.lower()}/"


def crypto_symbols(securities: list[dict]) -> tuple[str, ...]:
    return tuple(row["sym"] for row in securities if row.get("chart") == "crypto")


def keywords(text: str, limit: int = 400) -> str:
    words = re.findall(r"[a-z0-9]{3,}", text.lower())
    seen: list[str] = []
    bag = set()
    for word in words:
        if word in bag:
            continue
        bag.add(word)
        seen.append(word)
        if len(seen) >= limit:
            break
    return " ".join(seen)


def search_index(articles: list[Any], securities: list[dict]) -> dict:
    notes = []
    for article in articles:
        if getattr(article, "unlisted", False):
            continue
        notes.append({
            "title": article.title,
            "summary": article.summary,
            "path": article.path,
            "date": article.date.isoformat(),
            "ticker": article.ticker,
            "tags": [article.ticker] if article.ticker else [],
            "keywords": keywords(" ".join([article.title, article.summary, getattr(article, "body_text", "")])),
        })
    assets = [{
        "sym": row["sym"],
        "name": row["name"],
        "class": row["class"],
        "path": sym_path(row["sym"]),
        "chart": row["chart"],
        "cg": row.get("cg") or "",
    } for row in securities]
    pages = [
        {"title": "Ledger", "path": "/#ledger", "words": "home ledger notes research top"},
        {"title": "Markets", "path": "/#markets-panel", "words": "markets movers gainers losers volume gmm most"},
        {"title": "Rates", "path": "/#chips", "words": "rates sofr treasury ust2y ust10y eurusd btmm fx"},
        {"title": "Help", "path": "/help/", "words": "help codes credits sources"},
        {"title": "Search", "path": "/search/", "words": "search notes assets"},
    ]
    codes = [{
        "code": row["code"],
        "title": row["title"],
        "example": row["example"],
        "status": row["status"],
        "href": "/help/#codes",
    } for row in CODES]
    return {"notes": notes, "assets": assets, "pages": pages, "codes": codes}


def asset_links(securities: list[dict], current: str = "") -> str:
    bits = []
    for row in securities:
        current_attr = ' aria-current="page"' if row["sym"] == current else ""
        bits.append(
            '<a class="seg-btn asset-link" href="%s" data-asset="%s"%s>%s</a>'
            % (esc(sym_path(row["sym"])), esc(row["sym"]), current_attr, esc(row["sym"]))
        )
    return '<nav class="asset-select seg" aria-label="Asset">%s</nav>' % "".join(bits)


def chart_panel(row: dict, securities: list[dict], locked: bool, lazy: bool, home: bool) -> str:
    symbol = row["sym"]
    ranges = []
    for item in RANGES:
        if item in LIVE_RANGES:
            pressed = "true" if item == "1Y" else "false"
            ranges.append(
                f'<button type="button" class="seg-btn" data-range="{item}" aria-pressed="{pressed}">{item}</button>'
            )
        else:
            ranges.append(
                f'<button type="button" class="seg-btn is-blocked" data-range="{item}" disabled'
                f' aria-describedby="range-block">{item}</button>'
            )
    types = (
        '<button type="button" class="seg-btn" data-type="line" aria-pressed="true">Line</button>'
        '<button type="button" class="seg-btn" data-type="candle" aria-pressed="false">Candles</button>'
        '<button type="button" class="seg-btn" data-type="bar" aria-pressed="false">Bars</button>'
    )
    studies = (
        '<button type="button" class="seg-btn" data-ma="50" aria-pressed="false">MA 50</button>'
        '<button type="button" class="seg-btn" data-ma="200" aria-pressed="false">MA 200</button>'
    )
    chips = []
    for peer in securities:
        if peer.get("chart") != "crypto" or peer["sym"] == symbol:
            continue
        chips.append(
            f'<button type="button" class="seg-btn" data-cmp="{esc(peer["sym"])}" aria-pressed="false">{esc(peer["sym"])}</button>'
        )
    return f"""<section class="panel desk-chart" id="chart-panel" data-symbol="{esc(symbol)}" data-cg="{esc(row.get("cg") or "")}" data-name="{esc(row["name"])}" data-lazy="{"true" if lazy else "false"}" data-locked="{"true" if locked else "false"}" data-home="{"true" if home else "false"}" aria-labelledby="chart-heading">
  <div class="panel-head"><span id="chart-heading">Chart</span><span class="badge" id="chart-badge">aggregated</span></div>
  <div class="panel-body">
    <p class="chart-head"><span class="chart-name">{esc(row["name"])}</span> <span class="chart-ticker">{esc(symbol)}</span> <span class="chart-last">…</span> <span class="chart-asof"></span></p>
    <div class="chart-toolbar">
      <div class="seg" role="group" aria-label="Range">{"".join(ranges)}</div>
      <p class="range-block" id="range-block">{BLOCKED_RANGE}</p>
      <div class="seg" role="group" aria-label="Type">{types}</div>
      <div class="seg" role="group" aria-label="Studies">{studies}</div>
      <div class="seg" role="group" aria-label="Scale"><button type="button" class="seg-btn" data-log="1" aria-pressed="false">Log</button></div>
      <button type="button" class="seg-btn" data-compare-toggle aria-expanded="false">Compare</button>
      <button type="button" class="seg-btn" data-reset>Reset</button>
    </div>
    <div class="compare-row" hidden>
      <p>Compare, rebased to 100. Max 4 extra series.</p>
      <div class="seg" role="group" aria-label="Compare">{"".join(chips)}<button type="button" class="seg-btn" data-vs-btc aria-pressed="false">vs BTC</button></div>
      <label class="compare-add">Add <input type="search" data-compare-add placeholder="BTC" aria-label="Add a licensed asset"></label>
    </div>
    <p class="chart-legend" id="chart-legend"></p>
    <div class="chart-plot" tabindex="0" role="img" aria-label="{esc(row["name"])} price chart"><p class="chart-empty">Loading chart.</p></div>
    <p class="chart-volume-label">24h volume (rolling)</p>
    <p class="src-foot chart-foot"><a href="{CREDIT_URL}" rel="noopener">{CREDIT}</a> <span data-bar-size></span> <span>Aggregated price, not one exchange.</span> <a href="/help/#credits">Chart library credit</a></p>
    <p class="chart-status" id="chart-status" aria-live="polite"></p>
    <noscript><p class="noscript">This chart needs JavaScript. <a href="{CREDIT_URL}" rel="noopener">{CREDIT}</a>. Notes and sources stay available without it.</p></noscript>
  </div>
</section>"""


def render_help(notice: str) -> str:
    rows = "\n".join(
        "<tr><td>" + esc(row["code"]) + "</td><td>" + esc(row["title"]) + "</td><td>" + esc(row["example"]) + "</td><td>" + esc(row["status"]) + ". " + esc(row["detail"]) + "</td></tr>"
        for row in CODES
    )
    return f"""<section class="panel" id="help">
  <div class="panel-head"><span>Help</span><span class="data">codes</span></div>
  <div class="panel-body prose">
    <p>Click any note, asset, or panel. Search finds them by plain words. Codes are optional and never required.</p>
    <p>No login. No tutorial. The browser Back button leaves a page.</p>
    <p>Charts are aggregated prices, not a quote from one exchange. Research only. Not advice.</p>
    <h2>Ways to get around</h2>
    <ul>
      <li>Click a ledger row, an asset button, or a panel.</li>
      <li>Type a name in the search box, such as pearl.</li>
      <li>Optional codes are listed below. You do not need them.</li>
    </ul>
    <h2 id="codes">Codes</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Code</th><th>What it does</th><th>Example</th><th>Status</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table></div>
    <h2 id="credits">Sources and credits</h2>
    <ul>
      <li><a href="{CREDIT_URL}" rel="noopener">{CREDIT}</a>. Used for crypto prices, volume, movers, dominance, and total cap.</li>
      <li><a href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve" rel="noopener">U.S. Department of the Treasury</a>. UST2Y and UST10Y.</li>
      <li><a href="https://www.newyorkfed.org/markets/reference-rates/sofr" rel="noopener">Federal Reserve Bank of New York</a>. The SOFR data is subject to the Terms of Use posted at newyorkfed.org. The New York Fed is not responsible for publication of SOFR by alpha.kurult.ai, does not endorse this republication, and has no liability for your use.</li>
      <li><a href="https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html" rel="noopener">Source: ECB statistics</a>. EURUSD daily reference rate.</li>
      <li><a href="https://alternative.me/crypto/fear-and-greed-index/" rel="noopener">Fear and Greed Index by alternative.me</a>.</li>
      <li><a href="https://mempool.space/" rel="noopener">mempool.space</a>, with <a href="https://blockstream.info/" rel="noopener">Blockstream</a> as fallback. Not affiliated.</li>
      <li>Pearl chain stats, when shown, come from pearlchain.live. Not an affiliation.</li>
      <li id="chart-library">{esc(notice.strip())} <a href="https://www.tradingview.com/" rel="noopener">tradingview.com</a></li>
    </ul>
  </div>
</section>"""


def render_search_page(index: dict) -> str:
    groups = []
    for note in index["notes"]:
        groups.append(f'<li><a href="{esc(note["path"])}">{esc(note["title"])}</a></li>')
    for asset in index["assets"]:
        groups.append(f'<li><a href="{esc(asset["path"])}">{esc(asset["sym"])} {esc(asset["name"])}</a></li>')
    for page in index["pages"]:
        groups.append(f'<li><a href="{esc(page["path"])}">{esc(page["title"])}</a></li>')
    listed = "\n".join(groups)
    return f"""<section class="panel" id="search-page">
  <div class="panel-head"><span>Search</span><span class="data">notes and assets</span></div>
  <div class="panel-body">
    <p>Every note and asset on this desk. Type in the box above, or use the list.</p>
    <div id="search-static"><ul class="search-all">
{listed}
    </ul></div>
  </div>
</section>"""


def notes_for(articles: list[Any], sym: str) -> list[Any]:
    found = []
    for article in articles:
        if getattr(article, "unlisted", False):
            continue
        ticker = str(getattr(article, "ticker", "") or "").upper()
        if ticker == sym:
            found.append(article)
    return found


def render_asset_body(row: dict, articles: list[Any], securities: list[dict], chain_html: str) -> str:
    notes = notes_for(articles, row["sym"])
    latest = ""
    if notes:
        note = notes[0]
        call = f'<p class="callstrip">{esc(note.call)}</p>' if getattr(note, "call", "") else ""
        latest = f"""<section class="panel" aria-label="Latest note">
  <div class="panel-head"><span>Latest note</span><span class="data">{esc(note.date.isoformat())}</span></div>
  <div class="panel-body">
    {call}
    <h2 class="entry-title"><a href="{esc(note.path)}">{esc(note.title)}</a></h2>
    <p>{esc(note.summary)}</p>
  </div>
</section>"""
    all_notes = ""
    if notes:
        items = "\n".join(
            f'<li><a href="{esc(note.path)}">{esc(note.title)}</a></li>' for note in notes
        )
        all_notes = f'<section class="panel"><div class="panel-head"><span>Notes</span></div><div class="panel-body"><ul>{items}</ul></div></section>'
    chart = ""
    if row.get("chart") == "crypto":
        chart = chart_panel(row, securities, locked=True, lazy=False, home=False)
    else:
        chart = f"""<section class="panel" aria-label="Chart">
  <div class="panel-head"><span>Chart</span></div>
  <div class="panel-body">
    <p>Interactive history for this series is not on this page yet. The latest reading, when we have one, is on the <a href="/#chips">rates strip</a>.</p>
    <p class="src-foot"><a href="{esc(row["credit_url"])}" rel="noopener">{esc(row["credit"])}</a></p>
  </div>
</section>"""
    klass = row["class"]
    return f"""<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">&gt;</span> <a href="/search/?q={esc(klass.lower())}">{esc(klass)}</a> <span aria-hidden="true">&gt;</span> <span>{esc(row["sym"])}</span></nav>
<div class="asset-layout">
  <div class="asset-main">
    <section class="panel">
      <div class="panel-head"><span>{esc(row["name"])}</span><span class="data">{esc(row["sym"])}</span></div>
      <div class="panel-body">
        <h1 class="command-title">{esc(row["name"])} <span class="chart-ticker">{esc(row["sym"])}</span></h1>
        <p class="src-foot"><a href="{esc(row["credit_url"])}" rel="noopener">{esc(row["credit"])}</a></p>
      </div>
    </section>
    {latest}
    {all_notes}
  </div>
  <div class="asset-rail">
    {chart}
    {chain_html if row.get("chain") else ""}
  </div>
</div>"""


def securities_payload(securities: list[dict]) -> str:
    payload = [{
        "sym": row["sym"],
        "name": row["name"],
        "class": row["class"],
        "cg": row.get("cg") or "",
        "chart": row["chart"],
        "chain": row.get("chain") or "",
        "path": sym_path(row["sym"]),
    } for row in securities]
    return json.dumps(payload, separators=(",", ":"))
