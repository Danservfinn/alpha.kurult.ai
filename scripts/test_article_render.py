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


if __name__ == "__main__":
    unittest.main()
