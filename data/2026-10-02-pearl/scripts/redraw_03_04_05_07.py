"""Redraw charts 03, 04, 05 and 07 of the 2026-10-02 Pearl note from fresh raw pulls saved for this note.
No network calls. Same file names, figure sizes and style as the approved v4 charts. All times ET.
Inputs:
  sources/pearlchain/  pearlchain.live explorer API pulls, 2026-10-02 19:33 to 19:36 ET (fetch.log, manifest.md)
  sources/coingecko/   CoinGecko market_chart days=365 for pearl-2 (pulled 18:51 ET) and coins/pearl-2 (18:41 ET)
Chart 05's X-posts panel was cut (no reproducible, status-ID-level sample saved)."""
import json, glob, collections, datetime as dt
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

SRC = Path("/workspace/state/arghun/sources")
PC, CG = SRC / "pearlchain", SRC / "coingecko"
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "2026-10-02-pearl"

INK, RAISED, PAPER, DIM, FAINT = "#14120e", "#1b1813", "#f3ead7", "#c9c0ae", "#8a8273"
BRASS, TEAL, RUST, SAGE, SLATE = "#b08d57", "#5fa8a0", "#c4664a", "#8fa86b", "#7f8fa8"
RULE = "#3a3226"
plt.rcParams.update({
    "figure.facecolor": INK, "axes.facecolor": INK, "savefig.facecolor": INK,
    "axes.edgecolor": RULE, "axes.labelcolor": DIM, "axes.titlecolor": PAPER,
    "xtick.color": DIM, "ytick.color": DIM, "text.color": PAPER,
    "grid.color": RULE, "grid.linewidth": 0.6, "axes.grid": True, "grid.alpha": 0.7,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans", "font.size": 10.5, "axes.titlesize": 13.5,
    "axes.titleweight": "normal", "axes.titlelocation": "left", "axes.titlepad": 12,
    "legend.frameon": False, "legend.labelcolor": DIM, "svg.fonttype": "path",
    "axes.unicode_minus": False, "text.parse_math": False,
    "svg.hashsalt": "pearl-v4-clean",
})
UTC = dt.timezone.utc
def one(pattern, base=PC): return sorted(glob.glob(str(base / pattern)))[-1]
def load(pattern, base=PC): return json.load(open(one(pattern, base)))
def utcdate(t): return dt.datetime.fromtimestamp(t, UTC).date()
def et(t): return dt.datetime.fromtimestamp(t).astimezone()

def finish(fig, name, caption):
    fig.text(0.01, 0.012, caption, fontsize=7.6, color=FAINT, ha="left", va="bottom", linespacing=1.45)
    fig.text(0.99, 0.985, "alpha.kurult.ai | research only", fontsize=7.6, color=FAINT, ha="right", va="top")
    fig.savefig(OUT / f"{name}.svg", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", name)

def cg_stamps(key):
    out = {}
    for ts, v in load("pearl-2_market_chart_365_*.json", CG)[key]:
        t = dt.datetime.fromtimestamp(ts / 1000, UTC)
        if (t.hour, t.minute, t.second) == (0, 0, 0):
            out[t.date()] = v
    return out

# ---------------------------------------------------------------- 03 holder concentration
def chart_03():
    a = load("addresses_page1_limit25_*.json")
    G = int(a["totalGrains"])
    top = [("Top 10", int(a["top10Grains"])), ("Top 100", int(a["top100Grains"])), ("Top 1,000", int(a["top1000Grains"]))]
    tiers = a["distribution"]
    big = tiers[:5]
    small = sum(t["sharePct"] for t in tiers[5:])
    n_top2 = big[0]["count"] + big[1]["count"]
    fig = plt.figure(figsize=(10.5, 4.8))
    a1 = fig.add_axes([0.08, 0.2, 0.33, 0.6]); a2 = fig.add_axes([0.56, 0.2, 0.41, 0.6])
    ys = [2, 1, 0]
    a1.barh(ys, [100] * 3, color=RAISED, height=0.55)
    vals = [100 * g / G for _, g in top]
    a1.barh(ys, vals, color=BRASS, height=0.55)
    for y, v in zip(ys, vals):
        a1.text(v + 1.5, y, f"{v:.1f}%", va="center", fontsize=11)
    a1.set_yticks(ys); a1.set_yticklabels([t for t, _ in top], fontsize=10.5)
    a1.set_xlim(0, 100); a1.set_xlabel("Share of tracked supply, %"); a1.grid(axis="y", visible=False)
    a1.set_title(f"Top addresses, of {a['totalAddresses']:,} total", fontsize=11.5)
    cols = [BRASS, "#8c6f44", "#6b5434", "#4f3f2b", "#c4a06a"]
    ys2 = list(range(len(big)))[::-1]
    a2.barh(ys2, [t["sharePct"] for t in big], color=cols, height=0.6)
    for y, t in zip(ys2, big):
        a2.text(t["sharePct"] + 0.5, y, f"{t['sharePct']:.1f}%", va="center", fontsize=11)
    a2.set_yticks(ys2)
    a2.set_yticklabels([f"{t['tier']} (>= {int(t['minGrains']) // 10**8:,} PRL)\n{t['count']:,} addresses" for t in big], fontsize=8.6)
    a2.set_xlim(0, 45); a2.set_xlabel("Share of tracked supply, %"); a2.grid(axis="y", visible=False)
    a2.set_title(f"By explorer tier (smaller tiers: {small:.1f}%)", fontsize=11.5)
    share2 = big[0]["sharePct"] + big[1]["sharePct"]
    fig.text(0.08, 0.92, f"{n_top2} addresses hold about two thirds of PRL ({share2:.1f}%)", fontsize=13.5, color=PAPER)
    finish(fig, "03-holder-concentration",
           f"Source: pearlchain.live explorer API, addresses?page=1&limit=25 (rankings, tier table and top-N totals), fetched 2026-10-02 19:33 ET. Shares use the\n"
           f"explorer's own address total of {G / 1e8 / 1e6:.1f}M PRL (unconfirmed). Address-level, not owner-level: exchanges and pools can pool users, and one owner can split across many addresses.")
    return dict(top=vals, tiers=[(t["tier"], t["count"], t["sharePct"]) for t in tiers], total=G / 1e8, n=a["totalAddresses"], n_top2=n_top2, share2=share2)

# ---------------------------------------------------------------- 04 payout-address share
def crawl():
    blocks, txs = {}, {}
    for line in open(one("coinbase_crawl_*.jsonl")):
        r = json.loads(line); b = json.loads(r["body"])
        if "/block/" in r["url"]: blocks[b["height"]] = b
        else: txs[b["blockHeight"]] = b
    return blocks, txs

def chart_04():
    blocks, txs = crawl()
    assert len(blocks) == 200 and len(txs) == 200
    pay = collections.Counter(); split = 0
    for h, tx in txs.items():
        outs = [o for o in tx["vout"] if o["address"] and o["value"]]
        split += len(outs) > 1
        pay[outs[0]["address"]] += 1
    lo, hi = min(blocks), max(blocks)
    t_lo, t_hi = et(blocks[lo]["time"]), et(blocks[hi]["time"])
    top5 = pay.most_common(5)
    others = 200 - sum(c for _, c in top5)
    labels = [f"Payee {i + 1}\n{a[:8]}...{a[-4:]}" for i, (a, _) in enumerate(top5)] + ["All others"]
    counts = [c for _, c in top5] + [others]
    pct = [100 * c / 200 for c in counts]
    cols = [RUST, "#b38d5a", "#8c6f44", SLATE, SLATE, "#8a8273"]
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.84, bottom=0.2)
    ax.bar(range(6), pct, color=cols, width=0.62)
    for i, (p, c) in enumerate(zip(pct, counts)):
        ax.text(i, p + 1.0, f"{p:.1f}%\n({c} blocks)", ha="center", va="bottom", fontsize=10)
    ax.axhline(50, color=RUST, lw=0.9, ls="--", alpha=0.8)
    ax.text(5.35, 50.8, "50%", color=RUST, fontsize=9.5, ha="right")
    ax.set_xticks(range(6)); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 65); ax.set_ylabel("Share of blocks found, %"); ax.grid(axis="x", visible=False)
    top3 = sum(pct[:3])
    ax.set_title(f"One payout address found {pct[0]:.1f}% of the last 200 blocks; the top three found {top3:.1f}%")
    finish(fig, "04-pool-share",
           f"Source: pearlchain.live explorer API, block and coinbase-tx detail for blocks {lo:,} to {hi:,} ({t_lo:%b %d %H:%M} to {t_hi:%b %d %H:%M} ET), crawl 2026-10-02 19:33 to 19:35 ET.\n"
           f"Payee = coinbase payout address; {split} split-coinbase blocks counted to their first output.")
    coinbase_only = sum(1 for b in blocks.values() if b["txCount"] == 1)
    return dict(pct=pct, counts=counts, top3=top3, split=split, lo=lo, hi=hi, t_lo=t_lo, t_hi=t_hi, coinbase_only=coinbase_only,
                payees=[a for a, _ in top5])

# ---------------------------------------------------------------- 05 price vs active addresses
def chart_05():
    daily = load("charts_*.json")["daily"]
    end = dt.date(2026, 10, 1)
    av = [(utcdate(r["time"]), r["addrs"]) for r in daily if utcdate(r["time"]) <= end]
    pr = cg_stamps("prices")
    px = sorted((d, v) for d, v in pr.items() if d <= end)
    peak_a = max(av, key=lambda r: r[1]); peak_p = max(px, key=lambda r: r[1])
    fig, axs = plt.subplots(2, 1, figsize=(10, 6.6), sharex=True)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.14, hspace=0.18)
    a2, a3 = axs
    a2.plot([p[0] for p in px], [p[1] for p in px], color=PAPER, lw=1.8, label="CoinGecko daily price (00:00 UTC)")
    a2.set_ylabel("PRL price, USD"); a2.legend(loc="upper left", fontsize=8.5)
    a3.plot([a[0] for a in av], [a[1] for a in av], color=TEAL, lw=1.6)
    a3.set_ylabel("Active addresses\n/ day (UTC days)")
    a3.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    for a in axs:
        for dd in (peak_a[0], peak_p[0]):
            a.axvline(dd, color=FAINT, lw=0.8, ls=":")
    a3.text(peak_a[0], peak_a[1] * 0.98, f"  address high {peak_a[1]:,} ({peak_a[0]:%b %d})", fontsize=8.5, color=DIM, va="top")
    a2.text(peak_p[0], peak_p[1] * 0.98, f"price high ${peak_p[1]:.3f} ({peak_p[0]:%b %d} stamp)  ", fontsize=8.5, color=DIM, va="top", ha="right")
    a3.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    a2.set_title("Hype vs use: price spiked in September; active addresses rose far less")
    finish(fig, "05-hype-vs-use",
           "Price: CoinGecko market_chart days=365 for pearl-2, daily prices at 00:00 UTC (pulled 2026-10-02 18:51 ET; data provided by CoinGecko).\n"
           f"Active addresses: pearlchain.live explorer API, charts (daily, UTC days), fetched 2026-10-02 19:33 ET. Apr 27 to Oct 1; Oct 2 excluded (partial day).")
    return dict(peak_a=peak_a, peak_p=peak_p)

# ---------------------------------------------------------------- 07 issuance vs reported volume
STAMPS = ["07-01", "07-15", "07-23", "08-01", "08-11", "08-21", "08-25", "09-01", "09-11", "09-12", "09-19", "09-23", "09-28", "09-29", "10-02"]
def chart_07():
    bd = {utcdate(r["time"]): r for r in load("charts_*.json")["blocksDaily"]}
    P, V = cg_stamps("prices"), cg_stamps("total_volumes")
    md = load("pearl-2_coin_*.json", CG)["market_data"]
    assert md["last_updated"].startswith("2026-10-02T22:41")
    spot, vol24 = md["current_price"]["usd"], md["total_volume"]["usd"]
    iss, vol, labels, rows = [], [], [], []
    for s in STAMPS:
        d = dt.date.fromisoformat("2026-" + s); mined = bd[d - dt.timedelta(1)]["coins"]
        iss.append(mined * P[d] / 1e6); vol.append(V[d] / 1e6); labels.append(f"{d:%b %d}")
        rows.append((str(d), round(mined), P[d], V[d]))
    oct1 = bd[dt.date(2026, 10, 1)]["coins"]
    iss.append(oct1 * spot / 1e6); vol.append(vol24 / 1e6); labels.append("Now*")
    fig = plt.figure(figsize=(10.5, 5.6))
    ax = fig.add_axes([0.08, 0.22, 0.89, 0.63])
    x = list(range(len(labels)))
    ax.bar([i - 0.2 for i in x], iss, width=0.4, color=RUST, label="Daily issuance, USD (PRL mined x CoinGecko price)")
    ax.bar([i + 0.2 for i in x], vol, width=0.4, color=SLATE, label="CoinGecko reported 24h volume, USD")
    for i, (a, b) in enumerate(zip(iss, vol)):
        ax.text(i, max(a, b) + 0.08, f"{100 * a / b:.0f}%", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.8)
    ax.grid(axis="x", visible=False); ax.set_ylim(0, 6.5); ax.set_ylabel("USD millions")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title("New coins are a large share of what trades: issuance as % of reported volume")
    finish(fig, "07-issuance-vs-volume",
           "Labels are 00:00 UTC stamps; each pair covers the UTC day ending at that stamp. PRL mined per UTC day: pearlchain.live explorer API charts (blocksDaily), fetched 2026-10-02 19:33 ET.\n"
           f"Price and volume: CoinGecko market_chart days=365 for pearl-2 (pulled 18:51 ET). *Now = Oct 1 UTC-day issuance ({oct1:,.0f} PRL) x ${spot:.2f} vs 24h volume of ${vol24 / 1e6:.2f}M\n"
           "(coins/pearl-2, 18:41 ET). Low-trust venues (unconfirmed). Data provided by CoinGecko.")
    return dict(iss=iss, vol=vol, labels=labels, rows=rows, oct1=oct1)

if __name__ == "__main__":
    r3 = chart_03(); r4 = chart_04(); r5 = chart_05(); r7 = chart_07()
    print("03", r3); print("04", {k: v for k, v in r4.items()}); print("05", r5)
    print("07", [f"{l} {a:.3f}/{b:.3f}={100 * a / b:.0f}%" for l, a, b in zip(r7["labels"], r7["iss"], r7["vol"])])
