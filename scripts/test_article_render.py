"""Regression tests for article HTML the Tesla walk broke on."""

import unittest

import build


class ListRender(unittest.TestCase):
    def test_blank_line_does_not_restart_numbers(self):
        text = "1. The unit.\n\n2. The mile.\n\n3. The accounts.\n"
        html = build.render_markdown(text, "tesla")
        self.assertEqual(html.count("<ol>"), 1)
        self.assertEqual(html.count("<li>"), 3)
        self.assertNotIn("</ol>\n<ol>", html.replace(" ", ""))

    def test_blank_line_does_not_swallow_the_next_paragraph(self):
        text = "1. One item.\n\nNot a list.\n"
        html = build.render_markdown(text, "tesla")
        self.assertIn("<ol><li>One item.</li></ol>", html)
        self.assertIn("<p>Not a list.</p>", html)

    def test_different_marker_starts_a_new_list(self):
        text = "1. Numbered.\n\n- Bullet.\n"
        html = build.render_markdown(text, "tesla")
        self.assertIn("<ol><li>Numbered.</li></ol>", html)
        self.assertIn("<ul><li>Bullet.</li></ul>", html)


class FigureRender(unittest.TestCase):
    def test_tesla_charts_reserve_size_and_load_eager(self):
        src = "/assets/2026-10-04-tesla/04-deliveries.svg"
        text = f"![Deliveries]({src} \"caption\")\n"
        html = build.render_markdown(text, "tesla")
        self.assertIn('width="920"', html)
        self.assertIn('height="520"', html)
        self.assertIn('loading="eager"', html)
        self.assertNotIn('loading="lazy"', html)


class EmptyLatestNote(unittest.TestCase):
    def test_btc_and_eth_say_no_current_note_when_empty(self):
        import desk_html

        row = {
            "sym": "BTC",
            "name": "Bitcoin",
            "class": "Crypto",
            "credit": "Data provided by CoinGecko",
            "credit_url": "https://www.coingecko.com/",
            "chart": "none",
        }
        html = desk_html.render_asset_body(row, [], [], "")
        self.assertIn("<p>No current note</p>", html)
        self.assertNotIn("callstrip", html)
        eth = dict(row, sym="ETH", name="Ether")
        self.assertIn("<p>No current note</p>", desk_html.render_asset_body(eth, [], [], ""))

    def test_other_assets_stay_quiet_when_empty(self):
        import desk_html

        row = {
            "sym": "SOL",
            "name": "Solana",
            "class": "Crypto",
            "credit": "Data provided by CoinGecko",
            "credit_url": "https://www.coingecko.com/",
            "chart": "none",
        }
        html = desk_html.render_asset_body(row, [], [], "")
        self.assertNotIn("No current note", html)
        self.assertNotIn("Latest note", html)


class Receipt202Condition4(unittest.TestCase):
    def test_article_keeps_rating_weights_and_disclaimer(self):
        text = (build.ARTICLES_DIR / "2026-10-04-tesla.md").read_text(encoding="utf-8")
        self.assertIn('rating: "More downside than upside"', text)
        self.assertIn("we see more downside than upside", text)
        self.assertIn(build.EXACT_DISCLAIMER, text)
        self.assertIn("Weight 0.50 at three months and 0.45 at twelve months", text)
        self.assertIn("Weight 0.25 at three months and 0.30 at twelve months", text)
        self.assertIn("Weight 0.25 at both windows", text)
        self.assertIn("credits near zero", text)
        self.assertIn("energy margin still near 20%", text)
        self.assertIn("capex still above operating cash flow", text)
        self.assertNotIn("sits below it", text)
        self.assertNotIn("points below", text)
        self.assertNotIn("does not make any case an offer", text)
        self.assertNotIn("kill of a long view", text)
        self.assertNotIn("No position is taken", text)
        self.assertNotIn("\u2014", text)

    def test_hyphenated_compounds_are_not_rating_verbs(self):
        build._assert_no_rating_verb(
            "short-term investments and font-size=\"18\". " + build.EXACT_DISCLAIMER,
            "compound",
        )

    def test_removed_slug_fails(self):
        with self._tree("2026-10-06-akash") as dist:
            with self.assertRaises(build.BuildError):
                build.assert_receipt_202_condition_4(dist, articles_dir=dist)

    def test_banned_brand_fails(self):
        with self._tree("clean", brand=True) as dist:
            with self.assertRaises(build.BuildError):
                build.assert_receipt_202_condition_4(dist, articles_dir=dist)

    def test_rating_verb_outside_disclaimer_fails(self):
        with self._tree("clean", verb=True) as dist:
            with self.assertRaises(build.BuildError):
                build.assert_receipt_202_condition_4(dist, articles_dir=dist)

    def test_exact_disclaimer_is_allowed(self):
        with self._tree("clean") as dist:
            build.assert_receipt_202_condition_4(dist, articles_dir=dist)

    def _tree(self, marker, brand=False, verb=False):
        import tempfile
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            with tempfile.TemporaryDirectory() as tmp:
                root = build.Path(tmp)
                page = root / "articles" / "2026-10-04-tesla"
                page.mkdir(parents=True)
                extra = " do not add." if verb else ""
                brand_line = "Bloomberg" if brand else "Kurultai"
                body = (
                    f"<p>{marker} {brand_line}{extra}</p>\n"
                    f"<p>{build.EXACT_DISCLAIMER}</p>\n"
                    f"<p>{build.DISCLAIMER}</p>\n"
                )
                (page / "index.html").write_text(body, encoding="utf-8")
                (root / "note.txt").write_text(marker + "\n", encoding="utf-8")
                yield root

        return _cm()


if __name__ == "__main__":
    unittest.main()
