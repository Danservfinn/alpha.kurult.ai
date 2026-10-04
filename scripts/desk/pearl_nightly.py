#!/usr/bin/env python3
"""Pearl desk nightly: KPI archive, peer comps, derivatives, falsifier scorecard, catalyst alerts.

Default quality of evidence: only numbers returned by the public endpoints below.
Uncheckable falsifiers stay uncheckable. Prints nothing when no alert trips, so a
no_agent cron stays silent. Pass --report to always print the summary.
"""
import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "articles" / "2026-10-02-pearl.md"
DESK = ROOT / "data" / "desk"
UA = {"User-Agent": "alpha.kurult.ai research (read-only)", "Accept": "application/json"}
PEERS = [
    ("pearl-2", "PRL"),
    ("bittensor", "TAO"),
    ("render-token", "RENDER"),
    ("akash-network", "AKT"),
    ("zcash", "ZEC"),
    ("bitcoin", "BTC"),
]
LIGHTER_MARKET = 4097
PRICE_ALERT_PCT = 15.0


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def parse_list(text, key, fields):
    lines = text.splitlines()
    items = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == f"{key}:":
            i += 1
            break
        i += 1
    else:
        return []
    current = None
    while i < len(lines):
        raw = lines[i]
        if raw and raw[0] not in " \t-":
            break
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("- "):
            current = {}
            items.append(current)
            stripped = stripped[2:].strip()
        if current is None:
            break
        if ":" in stripped:
            name, value = stripped.split(":", 1)
            name = name.strip()
            if name in fields:
                current[name] = value.strip().strip('"')
        i += 1
    return items


def load_lists():
    text = ARTICLE.read_text(encoding="utf-8")
    return {
        "falsifiers": parse_list(text, "falsifiers", ("id", "text", "metric", "op", "threshold", "window", "due")),
        "catalysts": parse_list(text, "catalysts", ("date", "text")),
    }


def prior_row(today):
    files = sorted(DESK.glob("20*.json"))
    files = [p for p in files if p.name != "latest.json" and p.stem < today]
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def coingecko():
    ids = ",".join(pid for pid, _ in PEERS)
    rows = get(
        "https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&ids={ids}&sparkline=false"
    )
    by_id = {row["id"]: row for row in rows}
    out = []
    for pid, label in PEERS:
        row = by_id.get(pid) or {}
        cap = row.get("market_cap") or 0
        vol = row.get("total_volume") or 0
        out.append({
            "id": pid,
            "label": label,
            "price": row.get("current_price"),
            "market_cap": cap,
            "volume": vol,
            "vol_mc": (vol / cap) if cap else None,
            "change_24h": row.get("price_change_percentage_24h"),
        })
    return out


def derivatives():
    book = get(
        "https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails"
        f"?market_id={LIGHTER_MARKET}"
    )
    ob = book["order_book_details"][0]
    mark = float(ob["mark_price"])
    index = float(ob["index_price"])
    basis = (mark - index) / index if index else None
    rates = get("https://mainnet.zklighter.elliot.ai/api/v1/funding-rates")
    rate = None
    exchange = None
    for item in rates.get("funding_rates") or []:
        if item.get("market_id") == LIGHTER_MARKET and item.get("exchange") in (None, "lighter", "Lighter"):
            rate = item.get("rate")
            exchange = item.get("exchange")
            break
    if rate is None:
        for item in rates.get("funding_rates") or []:
            if item.get("market_id") == LIGHTER_MARKET:
                rate = item.get("rate")
                exchange = item.get("exchange")
                break
    return {
        "source": "lighter",
        "market_id": LIGHTER_MARKET,
        "symbol": ob.get("symbol"),
        "mark": mark,
        "index": index,
        "basis": basis,
        "open_interest": float(ob["open_interest"]),
        "last": float(ob["last_trade_price"]),
        "funding_rate": rate,
        "funding_exchange": exchange,
    }


def chain():
    stats = get("https://pearlchain.live/api/explorer/stats")
    return {
        "block_height": stats.get("blockHeight"),
        "block_reward_pearl": stats.get("blockRewardPearl"),
        "network_hash_ps": stats.get("networkHashPs"),
        "minted_pct": stats.get("mintedPct"),
        "hash_unit_note": stats.get("hashUnitNote"),
    }


def github_tag():
    rels = get("https://api.github.com/repos/pearl-research-labs/pearl/releases?per_page=1")
    if not rels:
        return None
    return rels[0].get("tag_name")


def cmp(op, value, threshold):
    if op == "gte":
        return value >= threshold
    if op == "gt":
        return value > threshold
    if op == "lte":
        return value <= threshold
    if op == "lt":
        return value < threshold
    raise ValueError(op)


def scorecard(falsifiers, peers, deriv, history):
    price = next(p["price"] for p in peers if p["id"] == "pearl-2")
    closes = []
    for row in history:
        for peer in row.get("peers") or []:
            if peer.get("id") == "pearl-2" and peer.get("price") is not None:
                closes.append(peer["price"])
    closes.append(price)
    out = []
    for item in falsifiers:
        metric = item.get("metric") or "manual"
        status = "uncheckable"
        detail = "no public series for this falsifier"
        if metric == "price_usd" and item.get("threshold"):
            threshold = float(item["threshold"])
            window = 5
            if "5" in (item.get("window") or ""):
                window = 5
            recent = closes[-window:]
            if len(recent) < window:
                status = "pending"
                detail = f"price {price} vs {threshold}; {len(recent)}/{window} archived closes"
            else:
                hit = all(cmp(item.get("op") or "gte", v, threshold) for v in recent)
                status = "tripped" if hit else "holding"
                detail = f"last {window} closes {recent} vs {threshold}"
        elif metric == "funding_sign" and deriv.get("funding_rate") is not None:
            rate = float(deriv["funding_rate"])
            status = "tripped" if rate < 0 else "holding"
            detail = f"funding {rate} on {deriv.get('funding_exchange')}"
        out.append({"id": item.get("id"), "text": item.get("text"), "status": status, "detail": detail, "due": item.get("due")})
    return out


def alerts(today, catalysts, card, peers, deriv, tag, prev):
    found = []
    for item in catalysts:
        if item.get("date") == today:
            found.append({"kind": "catalyst", "text": item.get("text")})
    for item in card:
        if item["status"] == "tripped":
            found.append({"kind": "falsifier", "text": f"{item['id']}: {item['detail']}"})
    if prev:
        old = next((p["price"] for p in prev.get("peers") or [] if p.get("id") == "pearl-2"), None)
        new = next(p["price"] for p in peers if p["id"] == "pearl-2")
        if old and new and abs(new - old) / old * 100 >= PRICE_ALERT_PCT:
            found.append({"kind": "price", "text": f"PRL {old} -> {new}"})
        old_rate = (prev.get("derivatives") or {}).get("funding_rate")
        new_rate = deriv.get("funding_rate")
        if old_rate is not None and new_rate is not None and (float(old_rate) < 0) != (float(new_rate) < 0):
            found.append({"kind": "funding", "text": f"funding sign flip {old_rate} -> {new_rate}"})
        old_tag = prev.get("github_tag")
        if tag and old_tag and tag != old_tag:
            found.append({"kind": "release", "text": f"github release {old_tag} -> {tag}"})
    return found


def history_rows(today):
    rows = []
    for path in sorted(DESK.glob("20*.json")):
        if path.stem == today or path.name == "latest.json":
            continue
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    today = dt.date.today().isoformat()
    lists = load_lists()
    if not lists["falsifiers"] or not lists["catalysts"]:
        sys.exit("pearl article missing falsifiers or catalysts")
    peers = coingecko()
    deriv = derivatives()
    chain_stats = chain()
    tag = github_tag()
    prev = prior_row(today)
    card = scorecard(lists["falsifiers"], peers, deriv, history_rows(today))
    tripped = alerts(today, lists["catalysts"], card, peers, deriv, tag, prev)
    payload = {
        "date": today,
        "peers": peers,
        "derivatives": deriv,
        "chain": chain_stats,
        "github_tag": tag,
        "scorecard": card,
        "alerts": tripped,
        "note": "MC/TVL and Token Terminal P/F are not in these free payloads. vol/MC is the comp column.",
    }
    DESK.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    (DESK / f"{today}.json").write_text(text, encoding="utf-8")
    (DESK / "latest.json").write_text(text, encoding="utf-8")
    if args.report or tripped:
        for item in tripped:
            print(f"ALERT {item['kind']}: {item['text']}")
        if args.report:
            prl = next(p for p in peers if p["id"] == "pearl-2")
            print(f"PRL {prl['price']} vol/MC {prl['vol_mc']:.4f} OI {deriv['open_interest']} basis {deriv['basis']}")
            print(f"scorecard {[c['status'] for c in card]}")
            print(f"wrote {DESK / today}.json")


if __name__ == "__main__":
    main()
