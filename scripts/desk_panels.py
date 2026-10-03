#!/usr/bin/env python3
"""HTML fragments for the Pearl desk panels. Reads committed JSON. No network."""

from __future__ import annotations

import json
from pathlib import Path

import pearl_desk as desk


def _load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _cell(value) -> str:
    if value is None or value == "":
        return "n/a"
    if isinstance(value, float):
        if abs(value) >= 100:
            text = f"{value:,.2f}".rstrip("0").rstrip(".")
            return text
        return f"{value:.6g}"
    return str(value)


def render_scorecard(falsifiers: list[dict]) -> str:
    if not falsifiers:
        return ""
    rows = []
    for item in falsifiers:
        due = item.get("due") or "no date"
        rows.append(
            "<tr>"
            f"<td>{desk.esc(item.get('id', ''))}</td>"
            f"<td>{desk.esc(item.get('side', ''))}</td>"
            f"<td>{desk.esc(due)}</td>"
            f"<td>{desk.esc(item.get('check', ''))}</td>"
            f"<td>{desk.esc(item.get('text', ''))}</td>"
            "</tr>"
        )
    return f"""<section class="desk panel" aria-labelledby="scorecard-heading">
  <div class="panel-head"><span id="scorecard-heading">Falsifier scorecard</span><span class="data">drafts only</span></div>
  <p>A dated falsifier is graded by the nightly job into drafts/. Nothing here is copied into the ledger.</p>
  <table class="desk-table">
    <thead><tr><th>Id</th><th>Side</th><th>Due</th><th>Check</th><th>Text</th></tr></thead>
    <tbody>
{''.join(rows)}
    </tbody>
  </table>
</section>
"""


def render_catalysts(catalysts: list[dict]) -> str:
    if not catalysts:
        return ""
    rows = []
    for item in catalysts:
        rows.append(
            "<tr>"
            f"<td>{desk.esc(item.get('due') or 'undated')}</td>"
            f"<td>{desk.esc(item.get('title', ''))}</td>"
            f"<td>{desk.esc(item.get('status', ''))}</td>"
            f"<td>{desk.esc(item.get('window', ''))}</td>"
            "</tr>"
        )
    return f"""<section class="desk panel" aria-labelledby="catalyst-heading">
  <div class="panel-head"><span id="catalyst-heading">Catalyst calendar</span><span class="data">from the note</span></div>
  <table class="desk-table">
    <thead><tr><th>Due</th><th>Catalyst</th><th>Status</th><th>Window</th></tr></thead>
    <tbody>
{''.join(rows)}
    </tbody>
  </table>
</section>
"""


def render_peers(root: Path) -> str:
    payload = _load(root / "data" / "pearl-desk" / "peers.json")
    if not payload:
        return """<section class="desk panel"><div class="panel-head"><span>Peer table</span><span class="data">missing</span></div>
  <p>No peer archive yet.</p></section>
"""
    desk.assert_peer_columns(tuple(payload.get("columns") or desk.PEER_COLUMNS))
    rows = []
    for row in payload.get("rows") or []:
        vol = row.get("realized_vol_30d_ann")
        vol_cell = "n/a" if vol is None else f"{vol * 100:.1f}%"
        vom = row.get("vol_over_mc")
        vom_cell = "n/a" if vom is None else f"{vom:.4f}"
        iss = row.get("issuance_yield")
        iss_cell = "n/a" if iss is None else f"{iss * 100:.1f}%"
        gap = f' <span class="key-note">{desk.esc(row.get("gap"))}</span>' if row.get("gap") else ""
        rows.append(
            "<tr>"
            f"<td>{desk.esc(row.get('ticker'))}</td>"
            f"<td>{desk.esc(_cell(row.get('price_usd')))}</td>"
            f"<td>{vom_cell}</td>"
            f"<td>{vol_cell}</td>"
            f"<td>{iss_cell}{gap}</td>"
            "</tr>"
        )
    return f"""<section class="desk panel" aria-labelledby="peers-heading">
  <div class="panel-head"><span id="peers-heading">Peer table</span><span class="data">fixed rows</span></div>
  <p>Rows are PRL, TAO, RENDER, AKT, ZEC, BTC. Columns are price, 24h volume over market cap, 30d realized vol computed by us, and issuance yield where we have a chain print. No third-party TVL feed. No revenue-multiple feed. Not advice.</p>
  <table class="desk-table">
    <thead><tr><th>Ticker</th><th>Price USD</th><th>Vol/MC</th><th>30d vol ann.</th><th>Issuance yield</th></tr></thead>
    <tbody>
{''.join(rows)}
    </tbody>
  </table>
  <p class="credit"><a href="https://www.coingecko.com/" rel="noopener">{desk.esc(desk.CREDIT)}</a></p>
</section>
"""


def render_derivatives(root: Path) -> str:
    """Off. Lighter terms grant no display right. No written permission in data/terms/."""
    del root
    return ""


def render_kpis(root: Path) -> str:
    payload = _load(root / "data" / "pearl-desk" / "series.json")
    prints = (payload or {}).get("prints") or []
    if not prints:
        return ""
    fields = (
        ("Height", ("kpis", "height")),
        ("Hashrate EH/s", ("kpis", "hashrate_ehs")),
        ("Supply M", ("kpis", "supply_m")),
        ("Fees PRL", ("kpis", "fees_prl")),
        ("Price USD", ("kpis", "price_usd")),
    )
    rows = []
    for label, path in fields:
        values = desk.series_values(prints, path)
        delta = desk.since_last_note(prints, path)
        if delta["status"] == "ok":
            change = f"{delta['delta_pct']:+.2f}% {desk.NOTE_DELTA_LABEL}"
        else:
            change = "no print versus the 2026-10-02 note"
        spark = desk.sparkline_svg(values)
        rows.append(
            "<tr>"
            f"<td>{desk.esc(label)}</td>"
            f"<td>{desk.esc(_cell(values[-1] if values else None))}</td>"
            f"<td>{spark}</td>"
            f"<td>{desk.esc(change)}</td>"
            "</tr>"
        )
    return f"""<section class="desk panel" aria-labelledby="kpi-heading">
  <div class="panel-head"><span id="kpi-heading">KPI archive</span><span class="data">{len(prints)} prints</span></div>
  <p>Baseline is the 2026-10-02 note archive. A second print is a nightly rerun. Chain cells keep a sha256 manifest. Price is a derived figure. Raw JSON does not back every print. CoinGecko raw JSON is not in this tree.</p>
  <table class="desk-table">
    <thead><tr><th>KPI</th><th>Latest</th><th>Sparkline</th><th>Since 2026-10-02 note</th></tr></thead>
    <tbody>
{''.join(rows)}
    </tbody>
  </table>
  <p class="credit"><a href="https://www.coingecko.com/" rel="noopener">{desk.esc(desk.CREDIT)}</a> for the price cell.</p>
</section>
"""


INTERNAL_ALERT_IDS = frozenset({"payee-50"})


def render_alerts(root: Path) -> str:
    payload = _load(root / "data" / "pearl-desk" / "alerts.json")
    items = [
        item
        for item in ((payload or {}).get("items") or [])
        if item.get("id") not in INTERNAL_ALERT_IDS
    ]
    if not items:
        return ""
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{desk.esc(item.get('id'))}</td>"
            f"<td>{desk.esc(item.get('status'))}</td>"
            f"<td>{desk.esc(item.get('reason'))}</td>"
            "</tr>"
        )
    return f"""<section class="desk panel" aria-labelledby="alerts-heading">
  <div class="panel-head"><span id="alerts-heading">Threshold alerts</span><span class="data">drafts only</span></div>
  <p>Rule: price +/-10% vs the prior archived close.</p>
  <table class="desk-table">
    <thead><tr><th>Id</th><th>Status</th><th>Detail</th></tr></thead>
    <tbody>
{''.join(rows)}
    </tbody>
  </table>
  <p class="credit"><a href="https://www.coingecko.com/" rel="noopener">{desk.esc(desk.CREDIT)}</a> for the price-move cell.</p>
</section>
"""


def desk_sections(meta: dict, root: Path) -> str:
    if not (meta.get("falsifiers") or meta.get("catalysts")):
        return ""
    parts = [
        render_scorecard(meta.get("falsifiers") or []),
        render_catalysts(meta.get("catalysts") or []),
        render_peers(root),
        render_derivatives(root),
        render_kpis(root),
        render_alerts(root),
    ]
    return "\n".join(p for p in parts if p)


def draft_pages(root: Path) -> list[tuple[str, str, str]]:
    """Grading notes stay in drafts/. They are not deploy pages."""
    del root
    return []
