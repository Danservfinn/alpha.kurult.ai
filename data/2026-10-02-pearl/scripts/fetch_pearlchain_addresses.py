#!/usr/bin/env python3
"""Fetch address detail for the top 25 ranked holders and the top 5 coinbase payees
from the saved ranking and crawl. Raw bodies kept in one JSONL; logged to fetch.log."""
import json, glob, time, urllib.request, datetime, hashlib, os, sys, collections
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = "https://pearlchain.live/api/explorer"
UA = {"User-Agent": "alpha.kurult.ai research (read-only)"}
now = lambda: datetime.datetime.now().astimezone()
def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r: return r.read()
        except Exception as e: err = e; time.sleep(2 * (i + 1))
    raise err
rank = json.load(open(sorted(glob.glob(os.path.join(OUT, "addresses_page1_limit25_*.json")))[-1]))
addrs = [h["address"] for h in rank["topHolders"]]
pay = collections.Counter()
for l in open(sorted(glob.glob(os.path.join(OUT, "coinbase_crawl_*.jsonl")))[-1]):
    r = json.loads(l)
    if "/tx/" in r["url"]:
        outs = [o for o in json.loads(r["body"])["vout"] if o["address"] and o["value"]]
        pay[outs[0]["address"]] += 1
addrs += [a for a, _ in pay.most_common(5) if a not in addrs]
t0 = now(); lines = []
for a in addrs:
    u = f"{BASE}/address/{a}"; t = now(); b = get(u)
    lines.append(json.dumps({"url": u, "fetched_et": t.isoformat(), "body": b.decode()})); time.sleep(0.2)
t1 = now(); data = ("\n".join(lines) + "\n").encode()
fn = f"address_detail_top25_payees5_{t0.strftime('%Y%m%dT%H%M%S%z')}.jsonl"
open(os.path.join(OUT, fn), "wb").write(data)
open(os.path.join(OUT, "fetch.log"), "a").write(f"{t0.isoformat()}..{t1.isoformat()}\t{BASE}/address/<a> for {len(addrs)} addresses\t{fn}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\n")
print(fn, len(addrs))
