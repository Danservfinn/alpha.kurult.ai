"""Redraw chart 01 of the 2026-10-02 Pearl note from CoinGecko data only.
Same file names, figure sizes and style as the approved v4 charts. No network calls.
Inputs: /workspace/state/arghun/sources/coingecko/*.json (pulled 2026-10-02 18:44 to 18:55 ET)
All times ET."""
import json, glob, math, datetime as dt
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

CG = Path("/workspace/state/arghun/sources/coingecko")
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "2026-10-02-pearl"
OUT.mkdir(parents=True, exist_ok=True)

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

def finish(fig, name, caption):
    fig.text(0.01, 0.012, caption, fontsize=7.6, color=FAINT, ha="left", va="bottom", linespacing=1.45)
    fig.text(0.99, 0.985, "alpha.kurult.ai | research only", fontsize=7.6, color=FAINT, ha="right", va="top")
    fig.savefig(OUT / f"{name}.svg", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", name)

def cg_daily(coin):
    f = sorted(glob.glob(str(CG / f"{coin}_market_chart_365_*.json")))[-1]
    out = {}
    for ts, p in json.load(open(f))["prices"]:
        t = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc)
        if (t.hour, t.minute, t.second) == (0, 0, 0):
            out[t.date()] = p
    return out

# ---------------------------------------------------------------- 01 relative performance
def chart_relative():
    start, end = dt.date(2026, 8, 20), dt.date(2026, 10, 2)
    days = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    names = [("PRL", "pearl-2", BRASS, 2.4), ("TAO", "bittensor", TEAL, 1.6), ("RENDER", "render-token", SLATE, 1.6), ("BTC", "bitcoin", RUST, 1.6)]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.07, right=0.88, top=0.86, bottom=0.17)
    offs = {"PRL": 0, "TAO": 7, "RENDER": -7, "BTC": 0}
    for k, coin, col, lw in names:
        s = cg_daily(coin)
        y = [100 * s[d] / s[start] for d in days]
        ax.plot(days, y, color=col, lw=lw)
        ax.annotate(f"{k} {y[-1]:.0f}", (days[-1], y[-1]), xytext=(6, offs[k]), textcoords="offset points", color=col, va="center", fontsize=10)
    ax.axhline(100, color=FAINT, lw=0.8, ls=":")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    ax.set_yticks([80, 100, 150, 200, 300, 400, 500])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_ylabel("Daily price, indexed to 100 on Aug 20 (log scale)")
    ax.set_title("PRL re-rated about 4x since Aug 20; AI-crypto peers and BTC did not")
    finish(fig, "01-relative-performance",
           "Source: CoinGecko public API, market_chart days=365 for pearl-2, bittensor, render-token and bitcoin; daily prices at 00:00 UTC, Aug 20 to Oct 2.\n"
           "Pulled 2026-10-02 18:45 to 18:55 ET. Data provided by CoinGecko.")

# chart 05 is now drawn by redraw_03_04_05_07.py (posts panel cut; addresses from fresh pearlchain pulls)

chart_relative()
