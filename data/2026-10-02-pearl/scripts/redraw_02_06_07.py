"""Redraw charts 02 and 06 of the 2026-10-02 Pearl note from saved raw pulls. Same file names, sizes and
style as the approved v4 charts; annotations are placed at the positions they had in the approved v4 SVG
(svgtext.replay; text positions only, no data is read from the old images). No network calls. All times ET.
  02: supply = 2.1B x h / (h + 650,226), anchored at height 122,400 at the 194 s target pace (saved
      pearlchain.live stats, 2026-10-02 19:33 ET); market cap $369.1M from the saved coins/pearl-2 pull
      (last_updated 18:41 ET); implied prices recomputed. The v4 observed-pace line was dropped.
  06: flat-mcap prices from the same anchor; spot from the saved coins/pearl-2 pull; scenario ranges are
      Arghun's subjective inputs.
Chart 07 moved to redraw_03_04_05_07.py."""
import json, glob, math, datetime as dt
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
import svgtext

HERE = Path(__file__).resolve().parent
V4 = Path("/workspace/state/arghun/v4-recovered/assets/2026-10-02-pearl")
OUT = HERE.parent / "assets" / "2026-10-02-pearl"
CG = Path("/workspace/state/arghun/sources/coingecko")

INK, PAPER, DIM, FAINT = "#14120e", "#f3ead7", "#c9c0ae", "#8a8273"
BRASS, RUST, SAGE, SLATE = "#b08d57", "#c4664a", "#8fa86b", "#7f8fa8"
RULE = "#3a3226"
plt.rcParams.update({
    "figure.facecolor": INK, "axes.facecolor": INK, "savefig.facecolor": INK,
    "axes.edgecolor": RULE, "axes.labelcolor": DIM, "axes.titlecolor": PAPER,
    "xtick.color": DIM, "ytick.color": DIM, "text.color": PAPER,
    "grid.color": RULE, "grid.linewidth": 0.6, "axes.grid": True, "grid.alpha": 0.7,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans", "font.size": 10.5,
    "legend.frameon": False, "legend.labelcolor": DIM, "svg.fonttype": "path",
    "axes.unicode_minus": False, "text.parse_math": False,
    "svg.hashsalt": "pearl-v4-clean",
})

coin = json.load(open(sorted(glob.glob(str(CG / "pearl-2_coin_*.json")))[-1]))
md = coin["market_data"]
MCAP = md["market_cap"]["usd"] / 1e6          # 369.132545
SPOT = md["current_price"]["usd"]             # 1.11
VOL24 = md["total_volume"]["usd"] / 1e6       # 4.800375
assert md["last_updated"].startswith("2026-10-02T22:41"), md["last_updated"]
STAMP = "CoinGecko coins/pearl-2, last updated 2026-10-02 18:41 ET"

def save(fig, name):
    fig.savefig(OUT / f"{name}.svg", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", name)

def rect(fig, l, r, b, t):
    return fig.add_axes([l, b, r - l, t - b])

# ---------------------------------------------------------------- 02 supply dilution
PCSTATS = json.load(open(sorted(glob.glob("/workspace/state/arghun/sources/pearlchain/stats_*.json"))[-1]))
H0, K = PCSTATS["blockHeight"], 650226         # 122,400 (pearlchain.live stats, 2026-10-02 19:33 ET)
assert PCSTATS["targetBlockSecs"] == 194
def supply(h): return 2100 * h / (h + K)        # M PRL
BPD_TARGET = 86400 / 194                         # 194 s target (445 blocks/day)

def chart_02():
    T = svgtext.texts(V4 / "02-supply-dilution.svg")
    fig = plt.figure(figsize=(11, 5.4))
    a1 = rect(fig, 0.07, 0.4647, 0.2, 0.82)
    d0 = dt.date(2026, 10, 2)
    days = [d0 + dt.timedelta(i) for i in range(366)]
    s_t = [supply(H0 + BPD_TARGET * i) for i in range(366)]
    a1.plot(days, s_t, color=BRASS, lw=2.2, label="194 s target pace (445 blocks/day)")
    for i in (0, 92, 365):
        a1.scatter([days[i]], [s_t[i]], s=28, color=PAPER, zorder=5)
    a1.set_ylim(300, 700)
    a1.xaxis.set_major_locator(FixedLocator([mdates.date2num(dt.date(y, m, 1)) for y, m in [(2026, 11), (2027, 1), (2027, 3), (2027, 5), (2027, 7), (2027, 9)]]))
    a1.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    a1.set_yticks(range(300, 701, 50))
    a1.legend(loc="lower right", fontsize=8.5)
    a2 = rect(fig, 0.5753, 0.97, 0.2, 0.82)
    vals = [MCAP / supply(H0), MCAP / supply(H0 + BPD_TARGET * 92), MCAP / supply(H0 + BPD_TARGET * 365)]
    V4H = 122270                                  # anchor of the approved v4 bars, used only to move the value labels
    old = [368.7 / supply(V4H), 368.7 / supply(V4H + BPD_TARGET * 92), 368.7 / supply(V4H + BPD_TARGET * 365)]
    a2.bar([0, 1, 2], vals, width=0.55, color=[BRASS, "#8c6f44", "#6b5434"])
    a2.set_xticks([0, 1, 2]); a2.set_xticklabels(["Now", "+3m", "+12m"])
    a2.set_ylim(0, 1.35); a2.set_yticks([0, .2, .4, .6, .8, 1.0, 1.2])
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}"))
    a2.grid(axis="x", visible=False)
    labels = [f"${v:.3f}" for v in vals]
    rep = {"332M": f"{supply(H0):.0f}M", "421M (+27%)": f"{supply(H0 + BPD_TARGET * 92):.0f}M (+{100 * (supply(H0 + BPD_TARGET * 92) / supply(H0) - 1):.0f}%)",
           "640M (+92%)": f"{supply(H0 + BPD_TARGET * 365):.0f}M (+{100 * (supply(H0 + BPD_TARGET * 365) / supply(H0) - 1):.0f}%)",
           "$1.109": labels[0], "$0.875": labels[1], "$0.576": labels[2],
           "Price if market cap stays at $368.7M": f"Price if market cap stays at ${MCAP:.1f}M",
           "Supply: emission formula supply = 2.1B x t / (t + 650,226), anchored at height 122,270 (pearlchain.live stats, 2026-10-02 11:45 ET); block pace from the same file.":
           f"Supply: emission formula supply = 2.1B x t / (t + 650,226), anchored at height {H0:,} at the 194 s target pace (pearlchain.live stats, 2026-10-02 19:33 ET).",
           "Market cap $368.7M and spot $1.11: CoinGecko simple price, last updated 2026-10-02 16:06 ET. Derived and unconfirmed.":
           f"Market cap ${MCAP:.1f}M and spot ${SPOT:.2f}: {STAMP}. Derived and unconfirmed. Data provided by CoinGecko."}
    # bar value labels follow the bar tops (bar height change converted to figure fraction)
    shift = {labels[i]: (vals[i] - old[i]) / 1.35 * 0.62 for i in range(3)}
    for t in T:
        if t["s"].startswith(("194 s", "201 s")):
            continue
        s = rep.get(t["s"], t["s"])
        y = t["y"] + shift.get(s, 0.0)
        fig.text(t["x"], y, s, fontsize=t["fs"], color=t["color"], ha="left", va="baseline", rotation=t["rot"], rotation_mode="anchor")
    save(fig, "02-supply-dilution")
    return vals

# ---------------------------------------------------------------- 06 scenario fan
def chart_06(flat):
    T = svgtext.texts(V4 / "06-scenario-fan.svg")
    fig = plt.figure(figsize=(10.5, 6))
    ax = rect(fig, 0.08, 0.8, 0.2, 0.86)
    sc = {1: [("Bear", .40, .35, .70, .50, RUST), ("Base", .40, .80, 1.40, 1.05, BRASS), ("Bull", .20, 1.80, 3.00, 2.30, SAGE)],
          2: [("Bear", .45, .15, .45, .30, RUST), ("Base", .35, .50, 1.10, .80, BRASS), ("Bull", .20, 2.00, 5.00, 3.00, SAGE)]}
    off = {"Bear": -0.13, "Base": 0.0, "Bull": 0.13}
    for x, rows in sc.items():
        for name, p, lo, hi, mid, col in rows:
            w = 0.05 + 0.2 * p; c = x + off[name]
            ax.fill_between([c - w / 2, c + w / 2], lo, hi, color=col, alpha=0.35, lw=0)
            ax.plot([c - w / 2, c + w / 2], [mid, mid], color=col, lw=2)
            ax.plot([0, c], [SPOT, mid], color=col, lw=0.6, alpha=0.4)
        wmid = sum(p * mid for _, p, _, _, mid, _ in rows)
        ax.scatter([x + 0.28], [wmid], marker="D", s=26, color=PAPER, zorder=5)
    ax.axhline(SPOT, color=FAINT, lw=0.7, ls=":")
    ax.scatter([0], [SPOT], s=40, color=PAPER, zorder=5)
    ax.scatter([0.70, 1.70], flat, marker="_", s=200, color=DIM, linewidths=1.5, zorder=5)
    ax.set_yscale("log"); ax.set_ylim(0.12, 6.5); ax.set_xlim(-0.35, 2.4)
    ax.set_yticks([0.15, 0.25, 0.5, 1, 2, 3, 5])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: {0.15: "$0.15", 0.25: "$0.25", 0.5: "$0.5"}.get(round(v, 2), f"${v:.0f}")))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["Now (Oct 2)", "3 months (~Jan 2027)", "12 months (~Oct 2027)"])
    ax.grid(axis="x", visible=False)
    rep = {"$0.875": f"${flat[0]:.3f}", "$0.576": f"${flat[1]:.3f}",
           "Spot $1.11: CoinGecko 2026-10-02 16:06 ET. Flat-mcap prices from chart 02 (unconfirmed supply).":
           f"Spot ${SPOT:.2f}: {STAMP}. Flat-mcap prices from chart 02 (unconfirmed supply). Data provided by CoinGecko."}
    svgtext.replay(fig, T, rep)
    save(fig, "06-scenario-fan")

if __name__ == "__main__":
    vals = chart_02()
    chart_06(vals[1:])
    # chart 07 is now drawn by redraw_03_04_05_07.py from the fresh pearlchain pulls
    print("mcap", MCAP, "spot", SPOT, "vol", VOL24, "implied", [round(v, 4) for v in vals])
