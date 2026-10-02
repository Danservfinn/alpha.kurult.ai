"""Intraday CoinGecko reads used in the note, taken from the saved market_chart days=1 pulls
(5-minute points). Prints price, market cap, 24h volume and volume/market cap at 11:45 ET Oct 2."""
import json, glob, datetime as dt
from pathlib import Path
CG = Path("/workspace/state/arghun/sources/coingecko")
ET = dt.timezone(dt.timedelta(hours=-4))
AT = dt.datetime(2026, 10, 2, 11, 45, tzinfo=ET)
for coin in ["pearl-2", "bittensor", "render-token", "zcash", "akash-network"]:
    fs = sorted(glob.glob(str(CG / f"{coin}_market_chart_1_*.json")))
    if not fs:
        print(coin, "MISSING"); continue
    d = json.load(open(fs[-1]))
    want = int(AT.timestamp() * 1000)
    i = min(range(len(d["prices"])), key=lambda k: abs(d["prices"][k][0] - want))
    ts, p = d["prices"][i]; m = d["market_caps"][i][1]; v = d["total_volumes"][i][1]
    t = dt.datetime.fromtimestamp(ts / 1000, ET)
    print(f"{coin:14s} {Path(fs[-1]).name} point {t:%H:%M:%S} ET price {p:.4f} mcap {m/1e6:.2f}M vol {v/1e6:.3f}M vol/mcap {v/m:.4f}")
