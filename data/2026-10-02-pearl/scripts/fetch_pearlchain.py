#!/usr/bin/env python3
"""Fresh keyless pulls from the pearlchain.live public explorer API.
Saves raw response bytes with ET timestamps in filenames; logs to fetch.log."""
import json, time, urllib.request, datetime, hashlib, os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = "https://pearlchain.live/api/explorer"
UA = {"User-Agent": "alpha.kurult.ai research (read-only)"}
def now(): return datetime.datetime.now().astimezone()
def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return r.read()
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise err
log = open(os.path.join(OUT, "fetch.log"), "a")
def save(name, url):
    t = now(); b = get(url)
    fn = f"{name}_{t.strftime('%Y%m%dT%H%M%S%z')}.json"
    open(os.path.join(OUT, fn), "wb").write(b)
    log.write(f"{t.isoformat()}\t{url}\t{fn}\t{len(b)}\t{hashlib.sha256(b).hexdigest()}\n"); log.flush()
    return json.loads(b)
save("stats", f"{BASE}/stats")
save("charts", f"{BASE}/charts")
save("addresses_page1_limit25", f"{BASE}/addresses?page=1&limit=25")
save("pools", f"{BASE}/pools")
tip = save("blocks_latest", f"{BASE}/blocks")["tipHeight"]
# coinbase crawl: last 200 blocks ending at tip
t0 = now(); lines = []
for h in range(tip - 199, tip + 1):
    u = f"{BASE}/block/{h}"; tb = now(); b = get(u)
    lines.append(json.dumps({"url": u, "fetched_et": tb.isoformat(), "body": b.decode()}))
    blk = json.loads(b)
    cb = [x for x in blk["transactions"] if x.get("isCoinbase")][0]["txid"]
    u2 = f"{BASE}/tx/{cb}"; tt = now(); b2 = get(u2)
    lines.append(json.dumps({"url": u2, "fetched_et": tt.isoformat(), "body": b2.decode()}))
    time.sleep(0.15)
t1 = now()
fn = f"coinbase_crawl_{tip-199}-{tip}_{t0.strftime('%Y%m%dT%H%M%S%z')}.jsonl"
data = ("\n".join(lines) + "\n").encode()
open(os.path.join(OUT, fn), "wb").write(data)
log.write(f"{t0.isoformat()}..{t1.isoformat()}\t{BASE}/block/<h> + /tx/<coinbase> for h={tip-199}..{tip}\t{fn}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\n")
print("done", tip, fn)
