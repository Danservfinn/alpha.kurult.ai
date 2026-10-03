#!/usr/bin/env python3
"""Print every pearlchain.live-derived figure used in the 2026-10-02 Pearl note from the saved raw pulls.
No network calls. Usage: derive_pearlchain.py [pearlchain_dir] [coingecko_dir]"""
import json, glob, sys, collections, datetime as dt, statistics as st
PC = sys.argv[1] if len(sys.argv) > 1 else "/workspace/state/arghun/sources/pearlchain"
CG = sys.argv[2] if len(sys.argv) > 2 else "/workspace/state/arghun/sources/coingecko"
one = lambda d, p: sorted(glob.glob(f"{d}/{p}"))[-1]
J = lambda d, p: json.load(open(one(d, p)))
UTC = dt.timezone.utc
ud = lambda t: dt.datetime.fromtimestamp(t, UTC).date()
et = lambda t: dt.datetime.fromtimestamp(t).astimezone().strftime("%b %d %H:%M ET")
s = J(PC, "stats_*.json"); c = J(PC, "charts_*.json"); a = J(PC, "addresses_page1_limit25_*.json"); pools = J(PC, "pools_*.json")
print("height", s["blockHeight"], "hashrate EH/s", round(s["networkHashPs"] / 1e18, 1), "minted %", round(s["mintedPct"], 2),
      "supply M", round(2100 * s["mintedPct"] / 100, 1), "reward", round(s["blockRewardPearl"]), "fees PRL", round(int(s["totalFeesGrains"]) / 1e8))
G = int(a["totalGrains"])
print("address total M", round(G / 1e14, 1), "addresses", a["totalAddresses"],
      "top10/100/1000 %", [round(100 * int(a[k]) / G, 1) for k in ("top10Grains", "top100Grains", "top1000Grains")])
print("tiers", [(t["tier"], t["count"], t["sharePct"]) for t in a["distribution"]])
bd = {ud(r["time"]): r for r in c["blocksDaily"]}
print("issuance Sep29-Oct1", [round(bd[d]["coins"]) for d in (dt.date(2026, 9, 29), dt.date(2026, 9, 30), dt.date(2026, 10, 1))])
supply = sum(r["coins"] for r in c["blocksDaily"])
launch = sum(r["coins"] for d, r in bd.items() if dt.date(2026, 4, 27) <= d <= dt.date(2026, 5, 3))
print("blocksDaily supply M", round(supply / 1e6, 2), "launch week M", round(launch / 1e6, 1), "share %", round(100 * launch / supply, 1))
b30 = [bd[dt.date(2026, 10, 1) - dt.timedelta(i)]["blocks"] for i in range(30)]
print("blocks/day last 30 UTC days", round(sum(b30) / 30, 1))
avg = st.mean(bd[dt.date(2026, 10, 1) - dt.timedelta(i)]["coins"] for i in range(3))
print("annual issuance % of supply (3-day avg)", round(100 * avg * 365 / supply, 1))
daily = {ud(r["time"]): r for r in c["daily"]}
for m in (6, 8, 9):
    x = [r for d, r in daily.items() if d.month == m]
    print(f"month {m}: avg txs {st.mean(r['txs'] for r in x):.0f} avg addrs {st.mean(r['addrs'] for r in x):.0f}")
pk = max(daily.items(), key=lambda kv: kv[1]["addrs"]); print("addr ATH", pk[0], pk[1]["addrs"])
wk = lambda d0, k: sum(daily[d0 + dt.timedelta(i)][k] for i in range(7))
for k in ("addrs", "txs"):
    print(f"week ratio {k}", round(wk(dt.date(2026, 9, 21), k) / wk(dt.date(2026, 8, 24), k), 2))
for day in ("04-30", "06-02", "07-23", "07-26", "08-11", "09-21", "09-27", "10-02"):
    x = [r for r in c["hashrateSamples"] if dt.datetime.fromtimestamp(r["time"]).strftime("%m-%d %H") == day + " 08"]
    print("hashrate sample", day, "08:00 ET", round(x[0]["hashrate"] / 1e18, 2))
blocks, txs = {}, {}
for line in open(one(PC, "coinbase_crawl_*.jsonl")):
    r = json.loads(line); b = json.loads(r["body"])
    (blocks if "/block/" in r["url"] else txs)[b["height"] if "/block/" in r["url"] else b["blockHeight"]] = b
pay = collections.Counter(); split = 0
for tx in txs.values():
    o = [v for v in tx["vout"] if v["address"] and v["value"]]; split += len(o) > 1; pay[o[0]["address"]] += 1
print("crawl", min(blocks), max(blocks), et(blocks[min(blocks)]["time"]), "to", et(blocks[max(blocks)]["time"]),
      "top5", pay.most_common(5), "split", split, "coinbase-only", sum(b["txCount"] == 1 for b in blocks.values()))
det = [json.loads(json.loads(l)["body"]) for l in open(one(PC, "address_detail_*.jsonl"))]
top25 = det[:25]
never = [d for d in top25 if d["totalSent"] == 0]
print("top25 never sent", len(never), round(sum(d["balance"] for d in never) / 1e14, 1), "M PRL; pure miners",
      [(d["address"][-4:], round(d["balance"] / 1e14, 2), et(d["lastTime"])) for d in never if d["totalMined"] > 0])
print("rank-1 address", top25[0]["address"][-6:], "balance", top25[0]["balance"], "first", et(top25[0]["firstTime"]), "last", et(top25[0]["lastTime"]))
for a_, _ in pay.most_common(2):
    d = next(x for x in det if x["address"] == a_)
    print("payee", a_[-4:], "sent/mined %", round(100 * d["totalSent"] / d["totalMined"], 2))
k = next(p for p in pools["directory"] if p["id"] == "kryptex")
print("pools 24h kryptex", k["blocks24h"], "of", pools["concentration"]["blocks"], round(k["share24h"], 1))
