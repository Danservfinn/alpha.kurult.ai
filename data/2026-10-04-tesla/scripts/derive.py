#!/usr/bin/env python3
"""Derive Tesla note figures and draw EDGAR-only charts.

Inputs are filing lines, company exhibits, or labeled assumptions.
This script does not read a price feed, a price CSV, or a vendor price library.
It does not take a closing price. It does not emit a per-share level,
an equity value, an enterprise value, or earnings implied by a price.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets" / "2026-10-04-tesla"
DERIVED = Path(__file__).resolve().parents[1] / "derived.json"

# Q2 2026 update, Exhibit 99.1, filed 2026-07-22.
# https://www.sec.gov/Archives/edgar/data/1318605/000162828026049213/exhibit991.htm
QUARTERS = [
    {
        "q": "2025 Q2",
        "auto_sales_m": 15787,
        "auto_cogs_m": 13567,
        "deliveries": 384122,
        "lease_deliveries": 6670,
        "production": 410244,
        "storage_gwh": 9.6,
        "energy_rev_m": 2789,
        "energy_gp_m": 846,
        "oi_m": 923,
        "ni_m": 1172,
        "rev_m": 22496,
    },
    {
        "q": "2025 Q3",
        "auto_sales_m": 20359,
        "auto_cogs_m": 17365,
        "deliveries": 497099,
        "lease_deliveries": 10230,
        "production": 447450,
        "storage_gwh": 12.5,
        "energy_rev_m": 3415,
        "energy_gp_m": 1073,
        "oi_m": 1624,
        "ni_m": 1373,
        "rev_m": 28095,
    },
    {
        "q": "2025 Q4",
        "auto_sales_m": 16750,
        "auto_cogs_m": 13874,
        "deliveries": 418227,
        "lease_deliveries": 10996,
        "production": 434358,
        "storage_gwh": 14.2,
        "energy_rev_m": 3837,
        "energy_gp_m": 1098,
        "oi_m": 1409,
        "ni_m": 840,
        "rev_m": 24901,
    },
    {
        "q": "2026 Q1",
        "auto_sales_m": 15473,
        "auto_cogs_m": 12616,
        "deliveries": 358023,
        "lease_deliveries": 3430,
        "production": 408386,
        "storage_gwh": 8.8,
        "energy_rev_m": 2408,
        "energy_gp_m": 952,
        "oi_m": 941,
        "ni_m": 477,
        "rev_m": 22387,
    },
    {
        "q": "2026 Q2",
        "auto_sales_m": 20006,
        "auto_cogs_m": 16866,
        "deliveries": 480126,
        "lease_deliveries": 7580,
        "production": 451758,
        "storage_gwh": 13.5,
        "energy_rev_m": 3139,
        "energy_gp_m": 640,
        "oi_m": 398,
        "ni_m": 1114,
        "rev_m": 28236,
        "ocf_m": 4697,
        "capex_m": 5789,
        "credits_m": 146,
    },
]

# Form 10-Q for the quarter ended June 30, 2026, filed 2026-07-23.
# Cover shares as of July 16, 2026. Debt principal from the MD&A sentence.
SHARES_COVER = 3_949_547_394
CASH_STI_M = 43524  # June 30, 2026, Q2 update balance-sheet line
DEBT_PRINCIPAL_M = 9080

# Q3 2026 production and deliveries exhibit, filed 2026-10-02.
# Financials for this quarter are not filed. Do not invent them.
Q3 = {"production": 464391, "deliveries": 486532, "storage_gwh": 13.7}

# Stated factory floors, Q2 update capacity table. Greater-than, not a rate.
FLOORS = [
    ("California 3/Y", 550_000),
    ("Shanghai 3/Y", 950_000),
    ("Berlin Y", 375_000),
    ("Texas Y", 250_000),
    ("Cybertruck", 125_000),
    ("Cybercab", 125_000),
]

BG = "#0b0d10"
INK = "#e6e1d6"
MUTED = "#9aa3ad"
AMBER = "#f0a202"
RED = "#e85d4c"
BLUE = "#7eb6d6"
GRID = "#2a3038"
PANEL = "#14181d"


def cash_deliveries(row: dict) -> int:
    return row["deliveries"] - row["lease_deliveries"]


def unit_row(row: dict) -> dict:
    cash = cash_deliveries(row)
    sales = row["auto_sales_m"] * 1_000_000
    cogs = row["auto_cogs_m"] * 1_000_000
    gp = sales - cogs
    return {
        "q": row["q"],
        "cash_deliveries": cash,
        "asp": round(sales / cash, 2),
        "cogs_per": round(cogs / cash, 2),
        "gp_per": round(gp / cash, 2),
        "gp_m": round(gp / 1_000_000, 3),
    }


def build() -> dict:
    units = [unit_row(row) for row in QUARTERS]
    q2 = QUARTERS[-1]
    q2u = units[-1]
    ttm_rows = QUARTERS[1:]  # 2025 Q3 through 2026 Q2
    ttm_oi = sum(r["oi_m"] for r in ttm_rows)
    ttm_ni = sum(r["ni_m"] for r in ttm_rows)
    ttm_rev = sum(r["rev_m"] for r in ttm_rows)
    net_cash = (CASH_STI_M - DEBT_PRINCIPAL_M) * 1_000_000
    capex_per = q2["capex_m"] * 1_000_000 / q2["deliveries"]
    yoy = (Q3["deliveries"] - QUARTERS[1]["deliveries"]) / QUARTERS[1]["deliveries"]
    floors_sum = sum(v for _, v in FLOORS)
    run_rate = q2["production"] * 4
    out = {
        "label": "Derived model math from SEC filing lines. No close. No per-share level.",
        "shares_cover_2026_07_16": SHARES_COVER,
        "cash_sti_m": CASH_STI_M,
        "debt_principal_m": DEBT_PRINCIPAL_M,
        "net_cash": net_cash,
        "units": units,
        "q2_gp_per_rounded": round(q2u["gp_per"]),
        "q2_capex_per_delivery": round(capex_per),
        "q2_sales_gp_m": round((q2["auto_sales_m"] - q2["auto_cogs_m"]), 3),
        "ttm": {"oi_m": ttm_oi, "ni_m": ttm_ni, "rev_m": ttm_rev, "window": "2025 Q3 to 2026 Q2"},
        "q3_vs_year_ago_deliveries": round(yoy, 4),
        "factory_floor_sum": floors_sum,
        "q2_production_annualized": run_rate,
        "floor_use": round(run_rate / floors_sum, 3),
    }
    if out["q2_gp_per_rounded"] != 6645:
        raise SystemExit(f"unit check failed: {out['q2_gp_per_rounded']}")
    if out["q2_capex_per_delivery"] != 12057:
        raise SystemExit(f"capex check failed: {out['q2_capex_per_delivery']}")
    return out


def svg_header(w: int, h: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img">',
        f"<title>{title}</title>",
        f'<rect width="{w}" height="{h}" fill="{BG}"/>',
        f'<text x="28" y="36" fill="{AMBER}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="18" font-weight="700">{title}</text>',
    ]


def svg_footer(lines: list[str], w: int, h: int, caption: str) -> str:
    lines.append(
        f'<text x="28" y="{h - 18}" fill="{MUTED}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="11">{caption}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def bar_chart(path: Path, title: str, labels: list[str], series: list[tuple[str, str, list[float]]], caption: str, ylabel: str) -> None:
    w, h = 920, 520
    left, right, top, bottom = 72, 24, 78, 78
    plot_w = w - left - right
    plot_h = h - top - bottom
    peak = max(max(vals) for _, _, vals in series) * 1.12
    lines = svg_header(w, h, title)
    lines.append(
        f'<text x="18" y="{top + plot_h / 2}" fill="{MUTED}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="11" transform="rotate(-90 18 {top + plot_h / 2})">{ylabel}</text>'
    )
    for frac in (0.25, 0.5, 0.75, 1.0):
        y = top + plot_h - plot_h * frac
        val = peak * frac
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="{GRID}"/>')
        lines.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" fill="{MUTED}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="11" text-anchor="end">{val:,.0f}</text>'
        )
    n = len(labels)
    group = plot_w / n
    bw = min(28, (group * 0.7) / max(1, len(series)))
    for i, label in enumerate(labels):
        cx = left + group * i + group / 2
        lines.append(
            f'<text x="{cx:.1f}" y="{top + plot_h + 22}" fill="{INK}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="12" text-anchor="middle">{label}</text>'
        )
        for s_i, (_, color, vals) in enumerate(series):
            x = cx - (len(series) * bw) / 2 + s_i * bw
            bh = plot_h * (vals[i] / peak)
            y = top + plot_h - bh
            lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw - 3:.1f}" height="{bh:.1f}" fill="{color}"/>')
    lx = left
    for name, color, _ in series:
        lines.append(f'<rect x="{lx}" y="50" width="12" height="12" fill="{color}"/>')
        lines.append(
            f'<text x="{lx + 18}" y="61" fill="{INK}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="12">{name}</text>'
        )
        lx += 18 + 8 * len(name) + 16
    path.write_text(svg_footer(lines, w, h, caption), encoding="utf-8")


def hbar(path: Path, title: str, rows: list[tuple[str, float, str]], caption: str) -> None:
    w, h = 920, 120 + 46 * len(rows)
    lines = svg_header(w, h, title)
    peak = max(v for _, v, _ in rows) * 1.08
    top = 72
    for i, (label, value, color) in enumerate(rows):
        y = top + i * 46
        bw = 480 * (value / peak)
        lines.append(
            f'<text x="28" y="{y + 18}" fill="{INK}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="14">{label}</text>'
        )
        lines.append(f'<rect x="300" y="{y}" width="{bw:.1f}" height="26" fill="{color}"/>')
        whole = abs(value - round(value)) < 0.05 or value >= 1000
        shown = f"{value:,.0f}" if whole else f"{value:,.1f}"
        lines.append(
            f'<text x="{308 + bw:.1f}" y="{y + 18}" fill="{INK}" font-family="ui-sans-serif, system-ui, sans-serif" font-size="13">{shown}</text>'
        )
    path.write_text(svg_footer(lines, w, h, caption), encoding="utf-8")


def draw(derived: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    units = derived["units"]
    labels = [u["q"].replace("20", "") for u in units]
    bar_chart(
        OUT / "01-unit.svg",
        "Sales gross profit per cash delivery",
        labels,
        [
            ("Gross profit per cash car", AMBER, [u["gp_per"] for u in units]),
            ("Cost per cash car", BLUE, [u["cogs_per"] for u in units]),
        ],
        "Q2 update exhibit. Sales and sales cost over cash deliveries. Not a price chart.",
        "Dollars per cash delivery",
    )
    q2 = derived["units"][-1]
    hbar(
        OUT / "02-cascade.svg",
        "Q2 2026: profit per cash car versus capex per delivery",
        [
            ("Gross profit per cash car", derived["q2_gp_per_rounded"], AMBER),
            ("Capex per delivery", derived["q2_capex_per_delivery"], RED),
        ],
        "Derived. Capex is company spend per delivery, not a vehicle bill of materials.",
    )
    # Share counts in millions, from the 10-Q rollforward and cover.
    hbar(
        OUT / "03-shares.svg",
        "Legal shares jumped. Basic EPS did not.",
        [
            ("Dec 31, 2025 outstanding", 3751, BLUE),
            ("Mar 31, 2026 outstanding", 3755, BLUE),
            ("Jun 30, 2026 outstanding", 3949, AMBER),
            ("Q2 basic weighted average", 3237, RED),
        ],
        "Millions of shares. 10-Q rollforward. Cover count 3,949,547,394 on July 16, 2026.",
    )
    ops = QUARTERS + [{"q": "2026 Q3", "production": Q3["production"], "deliveries": Q3["deliveries"]}]
    bar_chart(
        OUT / "04-deliveries.svg",
        "Production and deliveries, no prices",
        [r["q"].replace("20", "") for r in ops],
        [
            ("Production", BLUE, [r["production"] / 1000 for r in ops]),
            ("Deliveries", AMBER, [r["deliveries"] / 1000 for r in ops]),
        ],
        "Thousands of vehicles. Update exhibit through Q2 2026. Q3 from the Oct 2 8-K. No prices.",
        "Thousands of vehicles",
    )
    hbar(
        OUT / "06-floors.svg",
        "Stated factory floors versus the Q2 run rate",
        [(name, value / 1000, BLUE) for name, value in FLOORS]
        + [(f"Q2 production, annualized", derived["q2_production_annualized"] / 1000, AMBER)],
        "Thousands of vehicles a year. Floors are stated greater-than figures, not a rate.",
    )


def main() -> None:
    derived = build()
    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    DERIVED.write_text(json.dumps(derived, indent=2) + "\n", encoding="utf-8")
    draw(derived)
    print(json.dumps({
        "gp_per": derived["q2_gp_per_rounded"],
        "capex_per": derived["q2_capex_per_delivery"],
        "net_cash_b": round(derived["net_cash"] / 1e9, 3),
        "ttm_oi_m": derived["ttm"]["oi_m"],
        "ttm_ni_m": derived["ttm"]["ni_m"],
        "yoy": derived["q3_vs_year_ago_deliveries"],
        "units": derived["units"],
    }, indent=2))


if __name__ == "__main__":
    main()
