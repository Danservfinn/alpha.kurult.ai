#!/usr/bin/env python3
"""Offline checks for /markets/ (P1): top movers, sector baskets, BTC and ETH dominance.

Runs the real build into dist/ and reads the output. No network.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import desk_html  # noqa: E402

DIST = ROOT / "dist"
CREDIT = '<a href="https://www.coingecko.com/" rel="noopener">Data provided by CoinGecko</a>'


def built() -> str:
    page = DIST / "markets" / "index.html"
    if not page.is_file():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True, capture_output=True)
    return page.read_text(encoding="utf-8")


class MarketsPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], capture_output=True, text=True)
        assert "BUILD_OK" in out.stdout, out.stdout + out.stderr
        cls.html = built()

    def test_three_panels_each_carry_the_linked_credit(self):
        sections = re.findall(r"<section class=\"panel[^\"]*\" id=\"(\w+)\".*?</section>", self.html, re.S)
        self.assertEqual(sections, ["movers", "dominance", "sectors"])
        for block in re.findall(r"<section class=\"panel.*?</section>", self.html, re.S):
            self.assertIn(CREDIT, block)
        self.assertIn('class="colophon-credit"><a href="https://www.coingecko.com/" rel="noopener">Data provided by CoinGecko</a>', self.html)

    def test_movers_offer_24h_and_7d(self):
        self.assertIn('data-window="24h" aria-pressed="true"', self.html)
        self.assertIn('data-window="7d" aria-pressed="false"', self.html)

    def test_sector_allowlist_ships_and_has_no_portfolio_categories(self):
        match = re.search(r'<script type="application/json" id="alpha-baskets">(.*?)</script>', self.html)
        self.assertIsNotNone(match)
        baskets = json.loads(match.group(1))
        self.assertEqual(baskets, desk_html.sector_baskets())
        self.assertGreaterEqual(len(baskets), 15)
        for row in baskets:
            self.assertNotIn("portfolio", row["id"])

    def test_basket_file_rejects_portfolio_and_duplicates(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "b.json"
            bad.write_text(json.dumps([{"id": "world-liberty-financial-portfolio", "label": "X"}]), encoding="utf-8")
            with self.assertRaises(ValueError):
                desk_html.sector_baskets(bad)
            bad.write_text(json.dumps([{"id": "meme-token", "label": "A"}, {"id": "meme-token", "label": "B"}]), encoding="utf-8")
            with self.assertRaises(ValueError):
                desk_html.sector_baskets(bad)

    def test_scripts_and_no_ticker_on_markets(self):
        self.assertIn('<script src="/market.js" defer></script>', self.html)
        self.assertIn('<script src="/markets.js" defer></script>', self.html)
        self.assertNotIn('id="ticker"', self.html, "ticker would push movers below the 375x667 fold")
        self.assertTrue((DIST / "markets.js").is_file())

    def test_house_rules(self):
        for path in [DIST / "markets" / "index.html", DIST / "markets.js", DIST / "index.html", DIST / "market.js", DIST / "desk-logic.js"]:
            text = path.read_text(encoding="utf-8")
            self.assertFalse("\u2014" in text, f"em dash in {path.name}")
            self.assertIsNone(re.search(r"bloomberg|&lt;GO&gt;|<GO>", text, re.I), f"Bloomberg naming in {path.name}")
            self.assertFalse("Chart unavailable" in text or "Markets unavailable" in text, f"'unavailable' copy in {path.name}")
        for path in [DIST / "markets" / "index.html", DIST / "markets.js"]:
            self.assertIsNone(re.search(r"\bcsv\b|download", path.read_text(encoding="utf-8"), re.I), f"export path in {path.name}")

    def test_only_coingecko_is_fetched_by_the_new_page(self):
        js = (ROOT / "static" / "markets.js").read_text(encoding="utf-8")
        hosts = set(re.findall(r"https?://([^/\"' ]+)", js))
        self.assertEqual(hosts, set(), "markets.js builds URLs from AlphaDesk.CG only")
        self.assertIn("desk().CG", js)
        for banned in ("yahoo", "openbb", "defillama", "llama.fi", "lighter", "tokenterminal", "token terminal"):
            self.assertNotIn(banned, js.lower())

    def test_markets_is_findable(self):
        index = json.loads((DIST / "search.json").read_text(encoding="utf-8"))
        paths = {p["path"] for p in index["pages"]}
        self.assertTrue({"/markets/#movers", "/markets/#sectors", "/markets/#dominance"} <= paths)
        sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://alpha.kurult.ai/markets/", sitemap)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/markets/#movers"', home)
        self.assertIn('<a class="fnkey" href="/markets/">MARKETS</a>', home)

    def test_no_coingecko_raws_tracked(self):
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        raws = [p for p in out if "/coingecko/" in p or re.search(r"cg_|coins_markets|categories.*\.json$", p)]
        self.assertEqual(raws, [])


if __name__ == "__main__":
    unittest.main()
