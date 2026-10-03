#!/usr/bin/env python3
"""Pearl always-on desk. Drafts only. Never publishes. No network in this module."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import math
from pathlib import Path

# Display decisions from data/terms/, checked 2026-10-03 ET.
DISPLAY_COINGLASS = False
DISPLAY_HYPERLIQUID = False
# Lighter terms grant no display right and bar US persons. Off until a written
# permission is quoted in data/terms/. No such file is on disk.
DISPLAY_LIGHTER = False

FORBIDDEN_PEER_COLUMNS = ("defillama", "token_terminal", "tvl", "p/f", "p_f", "revenue")
PEER_COLUMNS = (
    "ticker",
    "price_usd",
    "as_of",
    "vol_over_mc",
    "realized_vol_30d_ann",
    "issuance_yield",
)
PRICE_MOVE_PCT_DEFAULT = 10.0
PAYEE_WINDOW_BLOCKS = 1000
PAYEE_THRESHOLD = 0.50
NOTE_PRINT_ID = "2026-10-02-note"
NOTE_DELTA_LABEL = "since 2026-10-02 note"

CREDIT = "Data provided by CoinGecko"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _skip_manifest(directory: Path, rel: str) -> bool:
    """CoinGecko raws and Lighter payloads are not committed, so they are not hashed."""
    if "pearl-kpi" not in directory.parts:
        return False
    parts = rel.split("/")
    if "coingecko" in parts:
        return True
    name = parts[-1]
    return name.startswith("lighter_")


def write_manifest(directory: Path) -> Path:
    """sha256 of every committed file under directory, except the manifest itself."""
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        if path.name == "MANIFEST.sha256":
            continue
        rel = path.relative_to(directory).as_posix()
        if _skip_manifest(directory, rel):
            continue
        digest = sha256_bytes(path.read_bytes())
        rows.append(f"{digest}  {rel}")
    out = directory / "MANIFEST.sha256"
    out.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    return out


def parse_due(raw: str) -> dt.date | None:
    text = (raw or "").strip().strip("\"'")
    if not text:
        return None
    return dt.date.fromisoformat(text)


def falsifiers_due(items: list[dict], as_of: dt.date) -> list[dict]:
    due = []
    for item in items:
        when = parse_due(str(item.get("due", "")))
        if when is not None and when <= as_of:
            due.append(item)
    return due


def grade_falsifier(item: dict, as_of: dt.date, observation: dict | None) -> dict:
    """Grade one due falsifier. Missing data stays ungraded. Never invents a pass."""
    obs = observation or {}
    measured = obs.get("measured")
    grade = "not_graded"
    reason = "Date reached. No measurement in the archive."
    if measured is True:
        grade = "tripped"
        reason = str(obs.get("reason") or "Measurement met the falsifier.")
    elif measured is False:
        grade = "not_tripped"
        reason = str(obs.get("reason") or "Measurement did not meet the falsifier.")
    return {
        "id": item.get("id", ""),
        "side": item.get("side", ""),
        "text": item.get("text", ""),
        "due": item.get("due", ""),
        "as_of": as_of.isoformat(),
        "grade": grade,
        "reason": reason,
        "status": "draft",
        "publish": False,
    }


def draft_markdown(grade: dict) -> str:
    """Grading note. status draft. Not an article."""
    lines = [
        "---",
        "status: draft",
        "kind: falsifier-scorecard",
        "publish: false",
        f"id: {grade['id']}",
        f"title: \"DRAFT scorecard: {grade['id']}\"",
        f"date: {grade['as_of']}",
        "---",
        "",
        "DRAFT. Not published. Research only. Not financial advice.",
        "",
        f"Falsifier: {grade['text']}",
        f"Side: {grade['side']}",
        f"Due: {grade['due']}",
        f"As of: {grade['as_of']}",
        f"Grade: {grade['grade']}",
        f"Reason: {grade['reason']}",
        "",
        "This file is a review draft. The nightly job must not copy it into articles/.",
        "",
    ]
    return "\n".join(lines)


def write_draft(drafts_dir: Path, grade: dict) -> Path:
    """Write a draft. Refuses articles/ and any publish flag."""
    if grade.get("publish"):
        raise RuntimeError("refusing to write a publishable grade")
    resolved = drafts_dir.resolve()
    if resolved.name == "articles" or "articles" in resolved.parts[-2:]:
        raise RuntimeError(f"refusing to write a draft under articles: {resolved}")
    drafts_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{grade['as_of']}-{grade['id']}.md"
    if "/" in slug or slug.startswith("."):
        raise RuntimeError(f"bad draft slug {slug}")
    path = drafts_dir / slug
    path.write_text(draft_markdown(grade), encoding="utf-8")
    return path


def evaluate_falsifiers(
    items: list[dict],
    as_of: dt.date,
    drafts_dir: Path,
    observations: dict[str, dict] | None = None,
) -> list[Path]:
    observations = observations or {}
    written = []
    for item in falsifiers_due(items, as_of):
        grade = grade_falsifier(item, as_of, observations.get(str(item.get("id", ""))))
        written.append(write_draft(drafts_dir, grade))
    return written


def payee_share(counts: dict[str, int]) -> tuple[float, int]:
    total = sum(counts.values())
    if total <= 0:
        return 0.0, 0
    top = max(counts.values())
    return top / total, total


def payee_alert(counts: dict[str, int], threshold: float = PAYEE_THRESHOLD, window: int = PAYEE_WINDOW_BLOCKS) -> dict:
    share, n = payee_share(counts)
    if n < window:
        return {
            "id": "payee-50",
            "status": "not_evaluated",
            "reason": f"Crawl has {n} blocks. Need {window}. A shorter crawl does not fire this alert.",
            "share": None,
            "draft": False,
        }
    fired = share > threshold
    return {
        "id": "payee-50",
        "status": "fired" if fired else "clear",
        "reason": f"Top payee share {share:.1%} over {n} blocks. Threshold {threshold:.0%}.",
        "share": round(share, 6),
        "draft": fired,
    }


def count_first_output_payees(lines) -> dict[str, int]:
    """Same first-output rule as derive_pearlchain.py: first vout with address and value."""
    txs: dict = {}
    for line in lines:
        if not str(line).strip():
            continue
        row = json.loads(line)
        url = row.get("url") or ""
        body = row.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        if "/block/" in url or not isinstance(body, dict):
            continue
        txs[body.get("blockHeight")] = body
    counts: dict[str, int] = {}
    for tx in txs.values():
        outs = [v for v in tx.get("vout") or [] if v.get("address") and v.get("value")]
        if not outs:
            continue
        addr = outs[0]["address"]
        counts[addr] = counts.get(addr, 0) + 1
    return counts


def keep_measured_payee(fresh: dict, prior: dict | None) -> dict:
    """A short crawl must not replace a measured fire or clear with an empty dict."""
    if fresh.get("status") != "not_evaluated" or not prior:
        return fresh
    if prior.get("id") != "payee-50":
        return fresh
    if prior.get("status") not in ("fired", "clear") or prior.get("share") is None:
        return fresh
    kept = dict(prior)
    kept["preserved"] = True
    return kept


def funding_flip(prior: float | None, latest: float | None) -> dict:
    """Sign rule only. Do not emit this alert. Lighter display is off."""
    if prior is None or latest is None:
        return {
            "id": "funding-flip",
            "status": "not_evaluated",
            "reason": "Need two Lighter funding prints. One print is a baseline, not a flip.",
            "draft": False,
        }
    if prior == 0 or latest == 0:
        return {
            "id": "funding-flip",
            "status": "not_evaluated",
            "reason": "A zero print is not a sign. Not treated as a flip.",
            "draft": False,
        }
    flipped = (prior > 0) != (latest > 0)
    return {
        "id": "funding-flip",
        "status": "fired" if flipped else "clear",
        "reason": f"Prior {prior:.6g}, latest {latest:.6g}.",
        "draft": flipped,
    }


def price_move(prior: float | None, latest: float | None, threshold_pct: float = PRICE_MOVE_PCT_DEFAULT) -> dict:
    if prior is None or latest is None or prior == 0:
        return {
            "id": "price-move",
            "status": "not_evaluated",
            "reason": "Need a prior archived close and a new print.",
            "draft": False,
        }
    pct = (latest / prior - 1.0) * 100.0
    fired = abs(pct) >= threshold_pct
    return {
        "id": "price-move",
        "status": "fired" if fired else "clear",
        "reason": f"Move {pct:+.2f}% vs prior close. Threshold +/-{threshold_pct:.0f}%.",
        "pct": round(pct, 4),
        "draft": fired,
        "credit": CREDIT,
    }


def alert_draft_markdown(alert: dict, as_of: str) -> str:
    return "\n".join(
        [
            "---",
            "status: draft",
            "kind: threshold-alert",
            "publish: false",
            f"id: {alert['id']}",
            f"title: \"DRAFT alert: {alert['id']}\"",
            f"date: {as_of}",
            "---",
            "",
            "DRAFT. Not published. No outside post. Research only. Not financial advice.",
            "",
            f"Alert: {alert['id']}",
            f"Status: {alert['status']}",
            f"Detail: {alert['reason']}",
            "",
        ]
    )


def sparkline_svg(values: list[float], width: int = 120, height: int = 28) -> str:
    clean = [v for v in values if v is not None and math.isfinite(v)]
    if not clean:
        return ""
    lo, hi = min(clean), max(clean)
    span = hi - lo or 1.0
    n = len(clean)
    pts = []
    for i, v in enumerate(clean):
        x = 2 if n == 1 else 2 + (width - 4) * i / (n - 1)
        y = 2 + (height - 4) * (1 - (v - lo) / span)
        pts.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg class="spark" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="sparkline {n} points">'
        f'<polyline fill="none" stroke="#f1bd59" stroke-width="1.5" points="{" ".join(pts)}"/>'
        f"</svg>"
    )


def daily_prices(payload: dict) -> dict[dt.date, float]:
    out: dict[dt.date, float] = {}
    for ts, price in payload.get("prices") or []:
        stamp = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc)
        if stamp.hour == 0 and stamp.minute == 0 and stamp.second == 0:
            out[stamp.date()] = float(price)
    return out


def realized_vol_30d(daily: dict[dt.date, float]) -> float | None:
    days = sorted(daily)
    if len(days) < 31:
        return None
    window = days[-31:]
    rets = []
    for i in range(1, len(window)):
        a, b = daily[window[i - 1]], daily[window[i]]
        if a <= 0 or b <= 0:
            return None
        rets.append(math.log(b / a))
    if len(rets) < 30:
        return None
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(365)


def last_chart_point(payload: dict, key: str):
    rows = payload.get(key) or []
    if not rows:
        return None, None
    ts, value = rows[-1]
    stamp = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc)
    return stamp, float(value)


def assert_peer_columns(columns: tuple[str, ...]) -> None:
    banned = set(FORBIDDEN_PEER_COLUMNS)
    for col in columns:
        if col.lower() in banned:
            raise RuntimeError(f"forbidden peer column {col}")


def series_values(prints: list[dict], path: tuple[str, ...]) -> list[float]:
    values = []
    for item in prints:
        cur = item
        ok = True
        for key in path:
            if not isinstance(cur, dict) or key not in cur or cur[key] is None:
                ok = False
                break
            cur = cur[key]
        if ok:
            try:
                values.append(float(cur))
            except (TypeError, ValueError):
                continue
    return values


def _at(item: dict, path: tuple[str, ...]) -> float | None:
    cur = item
    for key in path:
        if not isinstance(cur, dict) or key not in cur or cur[key] is None:
            return None
        cur = cur[key]
    try:
        return float(cur)
    except (TypeError, ValueError):
        return None


def since_last_note(prints: list[dict], path: tuple[str, ...], note_id: str = NOTE_PRINT_ID) -> dict:
    """Delta versus the 2026-10-02 note print, not versus the prior nightly print."""
    note = next((item for item in prints if item.get("id") == note_id), None)
    if note is None:
        return {"status": "no_note_print", "delta": None, "baseline": note_id}
    if not prints or prints[-1].get("id") == note_id:
        return {"status": "no_second_print", "delta": None, "baseline": note_id}
    prior = _at(note, path)
    latest = _at(prints[-1], path)
    if prior is None or latest is None:
        return {"status": "missing_value", "delta": None, "baseline": note_id}
    if prior == 0:
        return {"status": "prior_zero", "delta": None, "prior": prior, "latest": latest, "baseline": note_id}
    return {
        "status": "ok",
        "prior": prior,
        "latest": latest,
        "delta_pct": round((latest / prior - 1.0) * 100.0, 4),
        "baseline": note_id,
        "label": NOTE_DELTA_LABEL,
    }


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)
