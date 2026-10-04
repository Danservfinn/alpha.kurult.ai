#!/usr/bin/env python3
"""Nightly Pearl desk runner.

Reruns the saved-pull scripts into data/pearl-kpi/<stamp>/, appends the series,
writes a sha256 manifest, and drafts falsifier grades and threshold alerts.
The pearlchain crawl asks for 1,000 blocks. The payee alert is counted from
that crawl, or from a saved 1,000-block crawl, with the first-output rule.
A short crawl does not replace a measured fire. Never copies a draft into
articles/. Never posts. Never deploys.

CoinGecko bodies are JSON only, and the raw files stay out of git.
Coinglass is not called. Hyperliquid market data is not displayed.
Lighter is not fetched and not displayed.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import pearl_desk as desk

ROOT = Path(__file__).resolve().parent.parent
NOTE_DATA = ROOT / "data" / "2026-10-02-pearl"
DESK = ROOT / "data" / "pearl-desk"
DRAFTS = ROOT / "drafts"
SCRIPTS = NOTE_DATA / "scripts"
UA = {"User-Agent": "alpha.kurult.ai research (read-only)", "accept": "application/json"}

PEERS = (
    ("PRL", "pearl-2"),
    ("TAO", "bittensor"),
    ("RENDER", "render-token"),
    ("AKT", "akash-network"),
    ("ZEC", "zcash"),
    ("BTC", "bitcoin"),
)


def newest(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern))
    return matches[-1] if matches else None


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def seed_kpis() -> dict:
    """Baseline print from the 2026-10-02 saved pulls. No network. No invented fields."""
    stats_path = newest(NOTE_DATA / "pearlchain", "stats_*.json")
    charts_path = newest(NOTE_DATA / "pearlchain", "charts_*.json")
    coin_path = newest(NOTE_DATA / "coingecko", "pearl-2_coin_*.json")
    kpis: dict = {"source": "data/2026-10-02-pearl", "gaps": []}
    if stats_path:
        stats = load_json(stats_path)
        kpis["height"] = stats.get("blockHeight")
        hps = stats.get("networkHashPs")
        kpis["hashrate_ehs"] = round(hps / 1e18, 4) if isinstance(hps, (int, float)) else None
        minted = stats.get("mintedPct")
        kpis["supply_m"] = round(2100 * minted / 100, 4) if isinstance(minted, (int, float)) else None
        fees = stats.get("totalFeesGrains")
        try:
            kpis["fees_prl"] = round(int(fees) / 1e8, 4)
        except (TypeError, ValueError):
            kpis["fees_prl"] = None
            kpis["gaps"].append("fees")
        kpis["stats_file"] = stats_path.name
    else:
        kpis["gaps"].append("stats")
    if charts_path:
        charts = load_json(charts_path)
        daily = {}
        for row in charts.get("blocksDaily") or []:
            stamp = dt.datetime.fromtimestamp(row["time"], dt.timezone.utc).date()
            daily[stamp.isoformat()] = row.get("coins")
        kpis["issuance_oct1_prl"] = daily.get("2026-10-01")
        kpis["charts_file"] = charts_path.name
    if coin_path:
        coin = load_json(coin_path)
        md = coin.get("market_data") or {}
        kpis["price_usd"] = (md.get("current_price") or {}).get("usd")
        kpis["market_cap_usd"] = (md.get("market_cap") or {}).get("usd")
        kpis["volume_24h_usd"] = (md.get("total_volume") or {}).get("usd")
        kpis["price_as_of"] = "CoinGecko coins/pearl-2, 2026-10-02 18:41 ET"
        kpis["coin_file"] = coin_path.name
    return {
        "id": "2026-10-02-note",
        "fetched_et": "2026-10-02T19:33:00-04:00",
        "kpis": kpis,
    }


NO_HISTORY_GAP = "365-day history not available. 30d vol not computed. Last print only."


def committed_peer_rows(path: Path | None = None) -> dict[str, dict]:
    """Rows from the committed data/pearl-desk/peers.json, keyed by ticker."""
    path = path or DESK / "peers.json"
    if not path.is_file():
        return {}
    try:
        payload = load_json(path)
    except (OSError, ValueError):
        return {}
    return {str(r.get("ticker")): r for r in payload.get("rows") or [] if isinstance(r, dict) and r.get("ticker")}


def peer_row_from_chart(ticker: str, coin_id: str, note_data: Path | None = None, committed: dict[str, dict] | None = None) -> dict:
    """One peer row. Reads saved CoinGecko chart JSON if it is on disk (the raws are
    not committed, so normally it is not). Without it, the committed peers.json row
    is kept as is, so a rerun never blanks the table. Nothing is fetched or written here."""
    desk.assert_peer_columns(desk.PEER_COLUMNS)
    note_data = note_data or NOTE_DATA
    row = {
        "ticker": ticker,
        "coin_id": coin_id,
        "price_usd": None,
        "as_of": None,
        "vol_over_mc": None,
        "realized_vol_30d_ann": None,
        "issuance_yield": None,
        "gap": None,
        "credit": desk.CREDIT,
        "vol_label": "30d realized vol, annualized, computed by us from CoinGecko daily prices. Not advice.",
    }
    chart = newest(note_data / "coingecko", f"{coin_id}_market_chart_365_*.json")
    if chart is None:
        chart = newest(note_data / "coingecko", f"{coin_id}_market_chart_1_*.json")
        row["gap"] = NO_HISTORY_GAP
    if chart is None:
        kept = (committed if committed is not None else committed_peer_rows()).get(ticker)
        if kept:
            return dict(kept)
        row["gap"] = "No CoinGecko price on hand."
        return row
    payload = load_json(chart)
    daily = desk.daily_prices(payload)
    if daily:
        last_day = max(daily)
        row["price_usd"] = round(daily[last_day], 6)
        row["as_of"] = f"{last_day.isoformat()} 00:00 UTC daily stamp, file {chart.name}"
        row["realized_vol_30d_ann"] = _round(desk.realized_vol_30d(daily), 4)
    ts, cap = desk.last_chart_point(payload, "market_caps")
    _, vol = desk.last_chart_point(payload, "total_volumes")
    if cap and vol is not None and cap > 0:
        row["vol_over_mc"] = round(vol / cap, 6)
        if ts is not None:
            row["vol_mc_as_of"] = ts.strftime("%Y-%m-%d %H:%M UTC")
    if ticker == "PRL":
        row["issuance_yield"] = issuance_yield_from_note()
        coin = newest(note_data / "coingecko", "pearl-2_coin_*.json")
        if coin:
            md = load_json(coin).get("market_data") or {}
            spot = (md.get("current_price") or {}).get("usd")
            if spot is not None:
                row["price_usd"] = spot
                row["as_of"] = "CoinGecko coins/pearl-2, 2026-10-02 18:41 ET"
                mcap = (md.get("market_cap") or {}).get("usd")
                vol24 = (md.get("total_volume") or {}).get("usd")
                if mcap and vol24 is not None and mcap > 0:
                    row["vol_over_mc"] = round(vol24 / mcap, 6)
                    row["vol_mc_as_of"] = "CoinGecko coins/pearl-2, 2026-10-02 18:41 ET"
    return row


def issuance_yield_from_note() -> float | None:
    charts_path = newest(NOTE_DATA / "pearlchain", "charts_*.json")
    if not charts_path:
        return None
    charts = load_json(charts_path)
    rows = charts.get("blocksDaily") or []
    if not rows:
        return None
    by_day = {}
    supply = 0.0
    for row in rows:
        day = dt.datetime.fromtimestamp(row["time"], dt.timezone.utc).date()
        by_day[day] = float(row.get("coins") or 0)
        supply += float(row.get("coins") or 0)
    if supply <= 0:
        return None
    end = dt.date(2026, 10, 1)
    window = [by_day.get(end - dt.timedelta(days=i)) for i in range(3)]
    if any(v is None for v in window):
        return None
    avg = sum(window) / 3
    return round(avg * 365 / supply, 4)


def _round(value, places):
    if value is None:
        return None
    return round(value, places)


def build_seed() -> None:
    desk.assert_peer_columns(desk.PEER_COLUMNS)
    committed = committed_peer_rows()
    DESK.mkdir(parents=True, exist_ok=True)
    series = {
        "schema": "pearl-desk-series/v1",
        "credit": desk.CREDIT,
        "prints": [seed_kpis()],
    }
    peers = {
        "schema": "pearl-desk-peers/v1",
        "columns": list(desk.PEER_COLUMNS),
        "excluded": ["third-party TVL feed", "revenue-multiple feed", "MC/TVL", "P/F", "P/revenue"],
        "credit": desk.CREDIT,
        "rows": [peer_row_from_chart(ticker, coin_id, committed=committed) for ticker, coin_id in PEERS],
    }
    (DESK / "series.json").write_text(json.dumps(series, indent=2) + "\n", encoding="utf-8")
    (DESK / "peers.json").write_text(json.dumps(peers, indent=2) + "\n", encoding="utf-8")
    fresh_payee = desk.payee_alert({}, window=desk.PAYEE_WINDOW_BLOCKS)
    fresh_payee["reason"] = (
        "Oct 2 crawl is 200 blocks. Need 1,000. Not evaluated. The 52.5% figure in the note is not this alert."
    )
    alerts = {
        "schema": "pearl-desk-alerts/v1",
        "as_of": "2026-10-02",
        "items": [
            desk.keep_measured_payee(fresh_payee, load_prior_payee()),
            desk.price_move(None, None),
        ],
    }
    (DESK / "alerts.json").write_text(json.dumps(alerts, indent=2) + "\n", encoding="utf-8")
    desk.write_manifest(DESK)


def self_test(as_of: dt.date | None = None) -> Path:
    """Produce a test draft from a dated falsifier. Does not touch articles/."""
    when = as_of or dt.date(2026, 10, 3)
    items = [
        {
            "id": "test-dated",
            "side": "bearish",
            "text": "TEST fixture. A dated falsifier whose date has passed. Not a grade of the live Pearl call.",
            "due": "2026-10-01",
            "check": "manual",
        }
    ]
    out = DRAFTS / "test"
    paths = desk.evaluate_falsifiers(items, when, out)
    if len(paths) != 1:
        raise SystemExit(f"expected 1 test draft, got {paths}")
    text = paths[0].read_text(encoding="utf-8")
    if "articles/" in str(paths[0].resolve()).split("drafts")[0]:
        raise SystemExit("draft path escaped drafts/")
    if "publish: false" not in text or "not_graded" not in text:
        raise SystemExit("test draft missing draft markers")
    if "\u2014" in text:
        raise SystemExit("em dash in test draft")
    print(paths[0])
    return paths[0]


def fetch_json(url: str, dest: Path, attempts: int = 4) -> dict | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = b""
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
            dest.write_bytes(body)
            return json.loads(body)
        except Exception as exc:
            last = str(exc).encode()
            import time
            time.sleep(2 * (i + 1))
    dest.with_suffix(dest.suffix + ".error").write_bytes(last)
    return None


def pearlchain_argv(out: Path, n: int = desk.PAYEE_WINDOW_BLOCKS) -> list[str]:
    """Caller must pass the window. The fetcher defaults to 200 if this is omitted."""
    fetcher = SCRIPTS / "fetch_pearlchain.py"
    return [sys.executable, str(fetcher), str(out), str(n)]


def archive_root(path: Path) -> Path:
    for parent in path.parents:
        if parent.parent.name == "pearl-kpi":
            return parent
    raise RuntimeError(f"no pearl-kpi archive for {path}")


def best_payee_crawl(root: Path | None = None) -> tuple[Path, dict[str, int]] | None:
    root = root or ROOT
    kpi = root / "data" / "pearl-kpi"
    if not kpi.is_dir():
        return None
    best: tuple[int, float, Path, dict[str, int]] | None = None
    for path in sorted(kpi.glob("**/coinbase_crawl_*.jsonl")):
        counts = desk.count_first_output_payees(path.read_text(encoding="utf-8").splitlines())
        n = sum(counts.values())
        stamp = path.stat().st_mtime
        if best is None or n > best[0] or (n == best[0] and stamp >= best[1]):
            best = (n, stamp, path, counts)
    if best is None:
        return None
    return best[2], best[3]


def load_prior_payee() -> dict | None:
    path = DESK / "alerts.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    for item in payload.get("items") or []:
        if item.get("id") == "payee-50":
            return item
    return None


def payee_from_disk(root: Path | None = None) -> dict:
    """Count a saved crawl. Do not replace a measured fire with an empty dict."""
    root = root or ROOT
    found = best_payee_crawl(root)
    prior = load_prior_payee()
    if found is None:
        return desk.keep_measured_payee(desk.payee_alert({}), prior)
    path, counts = found
    item = desk.payee_alert(counts)
    if item["status"] == "not_evaluated":
        return desk.keep_measured_payee(item, prior)
    item["blocks"] = sum(counts.values())
    item["crawl"] = path.relative_to(root).as_posix()
    return item


def pull(stamp: str) -> Path:
    """One archive directory. JSON only. Asks the existing fetcher for 1,000 blocks."""
    out = ROOT / "data" / "pearl-kpi" / stamp
    pc = out / "pearlchain"
    cg = out / "coingecko"
    pc.mkdir(parents=True, exist_ok=True)
    cg.mkdir(parents=True, exist_ok=True)
    subprocess.run(pearlchain_argv(pc), check=True)
    for coin_id in ("pearl-2", "bittensor", "render-token", "zcash", "akash-network", "bitcoin"):
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
        fetch_json(url, cg / f"{coin_id}_coin.json")
    desk.write_manifest(out)
    return out


def grade_article(as_of: dt.date | None = None) -> list[Path]:
    """Evaluate the live note. Writes drafts/ only. Does not copy into articles/."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build

    article = ROOT / "articles" / "2026-10-02-pearl.md"
    front, _body = build.split_frontmatter(article.read_text(encoding="utf-8"), article.name)
    meta = build.parse_frontmatter(front, article.name)
    when = as_of or dt.datetime.now().astimezone().date()
    paths = desk.evaluate_falsifiers(meta.get("falsifiers") or [], when, DRAFTS)
    for path in paths:
        if "articles" in path.resolve().parts:
            raise SystemExit(f"draft landed in articles: {path}")
    return paths


def price_fields_from_coin(path: Path) -> dict:
    """Derived price only. The raw body is not committed."""
    payload = load_json(path)
    md = payload.get("market_data") or {}
    pulled = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    fields = {
        "price_usd": (md.get("current_price") or {}).get("usd"),
        "price_pulled_et": pulled.isoformat(timespec="seconds"),
        "price_as_of": (
            f"CoinGecko coins/pearl-2, pulled {pulled.strftime('%Y-%m-%d %H:%M:%S %z')}. {desk.CREDIT}."
        ),
    }
    vendor = md.get("last_updated")
    if vendor:
        fields["price_vendor_stamp"] = vendor
    return fields


def ingest(archive: Path) -> None:
    """Append one print from a pull directory. No Lighter. No Coinglass. No Hyperliquid numbers."""
    series_path = DESK / "series.json"
    series = json.loads(series_path.read_text(encoding="utf-8")) if series_path.is_file() else {
        "schema": "pearl-desk-series/v1",
        "credit": desk.CREDIT,
        "prints": [],
    }
    stats_path = newest(archive / "pearlchain", "stats_*.json")
    coin_path = archive / "coingecko" / "pearl-2_coin.json"
    kpis: dict = {"source": str(archive.relative_to(ROOT)), "gaps": []}
    if stats_path and stats_path.is_file():
        stats = load_json(stats_path)
        kpis["height"] = stats.get("blockHeight")
        hps = stats.get("networkHashPs")
        kpis["hashrate_ehs"] = round(hps / 1e18, 4) if isinstance(hps, (int, float)) else None
        minted = stats.get("mintedPct")
        kpis["supply_m"] = round(2100 * minted / 100, 4) if isinstance(minted, (int, float)) else None
        fees = stats.get("totalFeesGrains")
        try:
            kpis["fees_prl"] = round(int(fees) / 1e8, 4)
        except (TypeError, ValueError):
            kpis["fees_prl"] = None
    if coin_path.is_file():
        kpis.update(price_fields_from_coin(coin_path))
    stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    series["prints"].append({"id": archive.name, "fetched_et": stamp, "kpis": kpis})
    series_path.write_text(json.dumps(series, indent=2) + "\n", encoding="utf-8")
    prior = series["prints"][-2] if len(series["prints"]) > 1 else None
    prior_px = ((prior or {}).get("kpis") or {}).get("price_usd")
    latest_px = kpis.get("price_usd")
    payee = payee_from_disk()
    alerts = {
        "schema": "pearl-desk-alerts/v1",
        "as_of": stamp,
        "items": [
            payee,
            desk.price_move(prior_px, latest_px),
        ],
    }
    if payee.get("crawl"):
        alerts["payee_crawl"] = payee["crawl"]
    (DESK / "alerts.json").write_text(json.dumps(alerts, indent=2) + "\n", encoding="utf-8")
    write_alert_drafts(alerts, dt.datetime.now().astimezone().date().isoformat())
    desk.write_manifest(DESK)


def write_alert_drafts(alerts: dict, as_of: str) -> None:
    DRAFTS.mkdir(parents=True, exist_ok=True)
    for item in alerts["items"]:
        if not item.get("draft"):
            continue
        path = DRAFTS / f"{as_of}-{item['id']}.md"
        if "articles" in path.resolve().parts:
            raise SystemExit("refusing alert draft under articles")
        path.write_text(desk.alert_draft_markdown(item, as_of), encoding="utf-8")


def repair() -> None:
    """Offline fix: drop Lighter payloads, count the saved crawl, rewrite manifests."""
    kpi = ROOT / "data" / "pearl-kpi"
    touched = []
    for path in sorted(kpi.glob("**/lighter_*.json")):
        touched.append(archive_root(path))
        path.unlink()
    for archive in dict.fromkeys(touched):
        desk.write_manifest(archive)
    payee = payee_from_disk()
    if payee.get("preserved") or payee.get("status") not in ("fired", "clear"):
        raise SystemExit(f"repair did not measure a 1,000-block crawl: {payee}")
    if payee.get("blocks") != desk.PAYEE_WINDOW_BLOCKS:
        raise SystemExit(f"payee window is not {desk.PAYEE_WINDOW_BLOCKS}: {payee}")
    series = json.loads((DESK / "series.json").read_text(encoding="utf-8"))
    prints = series.get("prints") or []
    prior = prints[-2] if len(prints) > 1 else None
    latest = prints[-1] if prints else {}
    alerts = {
        "schema": "pearl-desk-alerts/v1",
        "as_of": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "items": [
            payee,
            desk.price_move(
                ((prior or {}).get("kpis") or {}).get("price_usd"),
                ((latest or {}).get("kpis") or {}).get("price_usd"),
            ),
        ],
        "payee_crawl": payee.get("crawl"),
    }
    (DESK / "alerts.json").write_text(json.dumps(alerts, indent=2) + "\n", encoding="utf-8")
    write_alert_drafts(alerts, dt.datetime.now().astimezone().date().isoformat())
    desk.write_manifest(DESK)
    print(payee["reason"])
    print("REPAIR_OK")


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        self_test()
        print("SELF_TEST_OK")
        return 0
    if "--seed" in argv:
        build_seed()
        print("SEED_OK")
        return 0
    if "--grade" in argv:
        paths = grade_article()
        if not paths:
            print("NONE_DUE")
        else:
            for path in paths:
                print(path)
        print("GRADE_OK")
        return 0
    if "--repair" in argv:
        repair()
        return 0
    if "--pull" in argv:
        stamp = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        path = pull(stamp)
        ingest(path)
        grade_article()
        print(path)
        print("PULL_OK")
        return 0
    print("usage: pearl_nightly.py --self-test | --seed | --grade | --repair | --pull", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
