#!/usr/bin/env python3
"""Offline tests for the Pearl desk. No network."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pearl_desk as desk


class FalsifierTests(unittest.TestCase):
    def test_dated_falsifier_writes_a_draft_outside_articles(self):
        items = [
            {
                "id": "test-dated",
                "side": "bearish",
                "text": "TEST fixture only.",
                "due": "2026-10-01",
                "check": "manual",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drafts = root / "drafts"
            paths = desk.evaluate_falsifiers(items, dt.date(2026, 10, 3), drafts)
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].is_file())
            self.assertIn("drafts", paths[0].parts)
            self.assertNotIn("articles", paths[0].parts)
            text = paths[0].read_text(encoding="utf-8")
            self.assertIn("publish: false", text)
            self.assertIn("not_graded", text)
            self.assertIn("DRAFT", text)
            self.assertNotIn("\u2014", text)

    def test_future_date_writes_nothing(self):
        items = [{"id": "later", "side": "bullish", "text": "later", "due": "2026-12-31", "check": "manual"}]
        with tempfile.TemporaryDirectory() as tmp:
            paths = desk.evaluate_falsifiers(items, dt.date(2026, 10, 3), Path(tmp) / "drafts")
            self.assertEqual(paths, [])

    def test_refuses_articles_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            articles = Path(tmp) / "articles"
            articles.mkdir()
            with self.assertRaises(RuntimeError):
                desk.write_draft(
                    articles,
                    {
                        "id": "x",
                        "side": "bearish",
                        "text": "x",
                        "due": "2026-10-01",
                        "as_of": "2026-10-03",
                        "grade": "not_graded",
                        "reason": "x",
                        "publish": False,
                    },
                )


class AlertTests(unittest.TestCase):
    def test_short_crawl_does_not_fire(self):
        result = desk.payee_alert({"a": 105, "b": 95}, window=1000)
        self.assertEqual(result["status"], "not_evaluated")
        self.assertFalse(result["draft"])

    def test_thousand_block_share_fires(self):
        result = desk.payee_alert({"a": 501, "b": 499}, window=1000)
        self.assertEqual(result["status"], "fired")
        self.assertTrue(result["draft"])

    def test_thousand_block_under_threshold_is_clear(self):
        result = desk.payee_alert({"a": 500, "b": 500}, window=1000)
        self.assertEqual(result["status"], "clear")
        self.assertFalse(result["draft"])

    def test_funding_flip_needs_two_prints(self):
        self.assertFalse(desk.funding_flip(None, 0.001)["draft"])
        self.assertTrue(desk.funding_flip(0.001, -0.002)["draft"])
        self.assertFalse(desk.funding_flip(0.001, 0.002)["draft"])

    def test_price_threshold(self):
        quiet = desk.price_move(1.11, 1.20, threshold_pct=10)
        loud = desk.price_move(1.11, 1.23, threshold_pct=10)
        self.assertFalse(quiet["draft"])
        self.assertTrue(loud["draft"])
        self.assertEqual(loud["credit"], "Data provided by CoinGecko")


class PeerTests(unittest.TestCase):
    def test_forbidden_columns_rejected(self):
        with self.assertRaises(RuntimeError):
            desk.assert_peer_columns(("ticker", "tvl"))
        desk.assert_peer_columns(desk.PEER_COLUMNS)
        self.assertNotIn("defillama", desk.PEER_COLUMNS)
        self.assertFalse(desk.DISPLAY_COINGLASS)
        self.assertFalse(desk.DISPLAY_HYPERLIQUID)
        self.assertFalse(desk.DISPLAY_LIGHTER)


class PeerFallbackTests(unittest.TestCase):
    """CoinGecko raws are not committed. A rerun must keep the committed peer rows."""

    def test_missing_raws_keep_committed_rows(self):
        import pearl_nightly as nightly

        committed = nightly.committed_peer_rows()
        self.assertEqual(sorted(committed), sorted(t for t, _ in nightly.PEERS))
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp)
            for ticker, coin_id in nightly.PEERS:
                row = nightly.peer_row_from_chart(ticker, coin_id, note_data=empty, committed=committed)
                self.assertEqual(row, committed[ticker])
                self.assertIsNotNone(row["price_usd"], ticker)
            self.assertEqual(list(empty.rglob("*")), [], "fallback must not write raws")

    def test_default_committed_rows_are_read_from_peers_json(self):
        import pearl_nightly as nightly

        with tempfile.TemporaryDirectory() as tmp:
            row = nightly.peer_row_from_chart("BTC", "bitcoin", note_data=Path(tmp))
        self.assertIsNotNone(row["price_usd"])
        self.assertEqual(row["credit"], desk.CREDIT)

    def test_no_raws_and_no_committed_row_is_labeled(self):
        import pearl_nightly as nightly

        with tempfile.TemporaryDirectory() as tmp:
            row = nightly.peer_row_from_chart("ZEC", "zcash", note_data=Path(tmp), committed={})
        self.assertIsNone(row["price_usd"])
        self.assertEqual(row["gap"], "No CoinGecko price on hand.")

    def test_gap_text_names_no_archive_or_file(self):
        import pearl_nightly as nightly

        peers = json.loads((nightly.DESK / "peers.json").read_text(encoding="utf-8"))
        texts = [nightly.NO_HISTORY_GAP] + [r.get("gap") or "" for r in peers["rows"]]
        for text in texts:
            self.assertNotIn("archive", text.lower())
            self.assertNotIn("file", text.lower())
        self.assertEqual(sum(1 for r in peers["rows"] if r.get("gap") == nightly.NO_HISTORY_GAP), 2)


class CronExcludeTests(unittest.TestCase):
    def test_is_excluded_drafts_test(self):
        import pearl_cron

        self.assertTrue(pearl_cron.is_excluded("drafts/test"))
        self.assertTrue(pearl_cron.is_excluded("drafts/test/2026-10-01-test-dated.md"))
        self.assertTrue(pearl_cron.is_excluded("./drafts/test/x.md"))
        self.assertTrue(pearl_cron.is_excluded("data/pearl-kpi/stamp/coingecko/pearl-2_coin.json"))
        self.assertFalse(pearl_cron.is_excluded("drafts/2026-10-03-payee-50.md"))
        self.assertFalse(pearl_cron.is_excluded("drafts/testing.md"))
        self.assertFalse(pearl_cron.is_excluded("data/pearl-kpi/stamp/pearlchain/stats.json"))


class SeriesTests(unittest.TestCase):
    def test_delta_is_versus_the_note_not_the_prior_print(self):
        one = [{"id": "2026-10-02-note", "kpis": {"price_usd": 1.11}}]
        three = [
            {"id": "2026-10-02-note", "kpis": {"price_usd": 1.11}},
            {"id": "mid", "kpis": {"price_usd": 2.00}},
            {"id": "latest", "kpis": {"price_usd": 1.00}},
        ]
        self.assertEqual(desk.since_last_note(one, ("kpis", "price_usd"))["status"], "no_second_print")
        delta = desk.since_last_note(three, ("kpis", "price_usd"))
        self.assertEqual(delta["status"], "ok")
        self.assertEqual(delta["prior"], 1.11)
        self.assertEqual(delta["latest"], 1.00)
        self.assertNotEqual(delta["prior"], 2.00)
        self.assertAlmostEqual(delta["delta_pct"], -9.9099, places=3)
        self.assertEqual(delta["label"], "since 2026-10-02 note")

    def test_sparkline_has_no_em_dash(self):
        svg = desk.sparkline_svg([1.0, 1.2, 0.9])
        self.assertIn("<polyline", svg)
        self.assertNotIn("\u2014", svg)


class PayeeCrawlTests(unittest.TestCase):
    def test_first_output_rule_ignores_later_outputs(self):
        line = json.dumps(
            {
                "url": "https://pearlchain.live/api/explorer/tx/abc",
                "body": json.dumps(
                    {
                        "blockHeight": 1,
                        "vout": [
                            {"address": "first", "value": 1},
                            {"address": "second", "value": 99},
                        ],
                    }
                ),
            }
        )
        block = json.dumps({"url": "https://pearlchain.live/api/explorer/block/1", "body": json.dumps({"height": 1})})
        counts = desk.count_first_output_payees([block, line])
        self.assertEqual(counts, {"first": 1})

    def test_short_crawl_does_not_replace_a_measured_fire(self):
        fresh = desk.payee_alert({"a": 105, "b": 95}, window=1000)
        prior = desk.payee_alert({"a": 508, "b": 492}, window=1000)
        kept = desk.keep_measured_payee(fresh, prior)
        self.assertEqual(fresh["status"], "not_evaluated")
        self.assertEqual(kept["status"], "fired")
        self.assertEqual(kept["share"], 0.508)
        self.assertTrue(kept["preserved"])
        again = desk.keep_measured_payee(prior, fresh)
        self.assertEqual(again["status"], "fired")
        self.assertNotIn("preserved", again)

    def test_saved_crawl_is_the_alert(self):
        root = Path(__file__).resolve().parent.parent
        import pearl_nightly as nightly

        item = nightly.payee_from_disk(root)
        self.assertEqual(item["status"], "fired")
        self.assertEqual(item["blocks"], 1000)
        self.assertEqual(item["share"], 0.508)
        self.assertIn("payee-1000-20261003", item["crawl"])
        self.assertFalse(item.get("preserved"))
        counts = desk.count_first_output_payees((root / item["crawl"]).read_text(encoding="utf-8").splitlines())
        self.assertEqual(item["reason"], desk.payee_alert(counts)["reason"])
        self.assertNotIn("200-block", item["reason"])


class RunnerGateTests(unittest.TestCase):
    def test_pull_asks_for_1000_blocks(self):
        import pearl_nightly as nightly

        argv = nightly.pearlchain_argv(Path("/tmp/out"))
        self.assertEqual(argv[-1], "1000")
        self.assertNotEqual(argv[-1], "200")

    def test_ingest_does_not_overwrite_a_measured_reason(self):
        text = Path(__file__).resolve().parent.joinpath("pearl_nightly.py").read_text(encoding="utf-8")
        self.assertNotIn("This pull uses the 200-block script", text)
        self.assertIn("payee_from_disk()", text)
        self.assertIn("keep_measured_payee", text)

    def test_lighter_helpers_are_gone(self):
        import pearl_nightly as nightly

        self.assertFalse(hasattr(nightly, "strip_funding_file"))
        self.assertFalse(hasattr(nightly, "lighter_funding"))
        text = Path(__file__).resolve().parent.joinpath("pearl_nightly.py").read_text(encoding="utf-8")
        self.assertNotIn("def strip_funding_file", text)
        self.assertNotIn("def lighter_funding", text)
        self.assertNotIn("zklighter", text)

    def test_build_does_not_emit_draft_pages(self):
        import desk_panels

        text = Path(__file__).resolve().parent.joinpath("build.py").read_text(encoding="utf-8")
        self.assertNotIn("draft_pages", text)
        self.assertNotIn('DIST / "drafts"', text)
        self.assertEqual(desk_panels.draft_pages(Path("/tmp")), [])

    def test_cron_plan_commits_raws_and_does_not_push(self):
        import pearl_cron

        joined = " ".join(" ".join(step) for step in pearl_cron.plan())
        self.assertIn("--self-test", joined)
        self.assertIn("--pull", joined)
        self.assertIn("--grade", joined)
        self.assertNotIn("push", joined)
        self.assertNotIn("wrangler", joined)
        self.assertEqual(pearl_cron.ALLOWED_BRANCH, "kublai/pearl-always-on")
        self.assertIn("data/pearl-kpi", pearl_cron.COMMIT_PATHS)
        self.assertNotIn("data/pearl-kpi/*/coingecko", pearl_cron.COMMIT_PATHS)
        self.assertTrue(pearl_cron.is_coingecko_raw("data/pearl-kpi/stamp/coingecko/pearl-2_coin.json"))
        self.assertTrue(pearl_cron.is_coingecko_raw("data/pearl-kpi/stamp/coingecko/bitcoin_coin.json.error"))
        self.assertFalse(pearl_cron.is_coingecko_raw("data/pearl-kpi/stamp/pearlchain/stats.json"))
        self.assertFalse(pearl_cron.is_coingecko_raw("data/2026-10-02-pearl/coingecko/pearl-2_coin.json"))
        script = Path.home() / ".hermes/profiles/kublai/scripts/pearl_desk_nightly.py"
        body = script.read_text(encoding="utf-8")
        self.assertIn("pearl_cron", body)
        self.assertNotIn("git push", body)
        self.assertNotIn("wrangler", body)

    def test_commit_skips_coingecko_raws(self):
        import pearl_cron

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-b", "kublai/pearl-always-on"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "desk@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "desk"], cwd=root, check=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=root, check=True)
            kpi = root / "data/pearl-kpi/stamp/pearlchain"
            cg = root / "data/pearl-kpi/stamp/coingecko"
            desk_dir = root / "data/pearl-desk"
            drafts = root / "drafts"
            for directory in (kpi, cg, desk_dir, drafts):
                directory.mkdir(parents=True)
            (kpi / "stats.json").write_text("{}\n", encoding="utf-8")
            (cg / "pearl-2_coin.json").write_text("{}\n", encoding="utf-8")
            (cg / "bitcoin_coin.json.error").write_text("err\n", encoding="utf-8")
            (desk_dir / "alerts.json").write_text("{}\n", encoding="utf-8")
            (drafts / "x.md").write_text("draft\n", encoding="utf-8")
            (root / ".gitignore").write_text("data/pearl-kpi/*/coingecko/\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
            self.assertEqual(pearl_cron.commit_raws(root), 0)
            listed = subprocess.run(
                ["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True
            ).stdout
            self.assertIn("data/pearl-kpi/stamp/pearlchain/stats.json", listed)
            self.assertIn("data/pearl-desk/alerts.json", listed)
            self.assertIn("drafts/x.md", listed)
            self.assertNotIn("pearl-2_coin.json", listed)
            self.assertNotIn("bitcoin_coin.json.error", listed)

    def test_commit_refuses_other_branch(self):
        import pearl_cron

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-b", "other"], cwd=root, check=True, capture_output=True)
            self.assertEqual(pearl_cron.commit_raws(root), 3)


class ArchiveTests(unittest.TestCase):
    def test_lighter_raws_and_funding_flip_are_gone(self):
        root = Path(__file__).resolve().parent.parent
        listed = subprocess.run(
            ["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.splitlines()
        for rel in listed:
            name = Path(rel).name
            self.assertFalse(name.startswith("lighter_"), rel)
            if rel.startswith("data/pearl-kpi/") and "/coingecko/" in rel:
                self.assertFalse(name.endswith("_coin.json") or name.endswith(".error"), rel)
        self.assertNotIn("data/terms/lighter.md", listed)
        self.assertFalse(any(rel.startswith("data/2026-10-02-pearl/coingecko/") for rel in listed))
        self.assertNotIn("drafts/test/2026-10-03-test-dated.md", listed)
        article = (root / "articles/2026-10-02-pearl.md").read_text(encoding="utf-8")
        self.assertNotIn("Lighter", article)
        self.assertNotIn("zklighter", article)
        self.assertNotIn("market 4097", article)
        self.assertNotIn("up to 3x", article)
        alerts = json.loads((root / "data/pearl-desk/alerts.json").read_text(encoding="utf-8"))
        ids = [item["id"] for item in alerts["items"]]
        self.assertNotIn("funding-flip", ids)
        self.assertIn("payee-50", ids)
        self.assertIn("price-move", ids)
        series = json.loads((root / "data/pearl-desk/series.json").read_text(encoding="utf-8"))
        latest = series["prints"][-1]["kpis"]
        self.assertEqual(latest["price_usd"], 1.031)
        self.assertIn("price_pulled_et", latest)
        self.assertIn("Data provided by CoinGecko", latest["price_as_of"])
        for item in series["prints"]:
            self.assertNotIn("derivatives", item)

    def test_public_panels_have_the_nits_fixed(self):
        import desk_panels

        root = Path(__file__).resolve().parent.parent
        alerts = desk_panels.render_alerts(root)
        peers = desk_panels.render_peers(root)
        score = desk_panels.render_scorecard(
            [{"id": "x", "side": "bearish", "due": "2026-10-01", "check": "manual", "text": "t"}]
        )
        joined = alerts + peers + score + desk_panels.render_derivatives(root)
        self.assertNotIn("DRAFT. Not published.", joined)
        self.assertNotIn("DefiLlama", joined)
        self.assertNotIn("Token Terminal", joined)
        self.assertNotIn("defillama", joined.lower())
        self.assertIn("Data provided by CoinGecko", alerts)
        self.assertIn("https://www.coingecko.com/", alerts)
        self.assertEqual(desk_panels.render_derivatives(root), "")
        self.assertNotIn("funding-flip", alerts)
        self.assertNotIn("Lighter", alerts)
        self.assertNotIn("payee-50", alerts)
        self.assertNotIn("1000 blocks", alerts)
        self.assertNotIn("1,000 blocks", alerts)
        self.assertNotIn("50.8%", alerts)
        self.assertIn("price-move", alerts)
        kpis = desk_panels.render_kpis(root)
        self.assertNotIn("raw JSON backs every print", kpis)
        self.assertIn("Raw JSON does not back every print", kpis)
        self.assertNotIn("\u2014", kpis)

    def test_manifests_match_and_draft_uses_runner_reason(self):
        root = Path(__file__).resolve().parent.parent
        for directory in (root / "data/pearl-desk", root / "data/pearl-kpi/20261003T133223-0400"):
            manifest = (directory / "MANIFEST.sha256").read_text(encoding="utf-8")
            self.assertTrue(manifest.strip())
            for line in manifest.splitlines():
                digest, rel = line.split("  ", 1)
                got = hashlib.sha256((directory / rel).read_bytes()).hexdigest()
                self.assertEqual(got, digest, rel)
        alerts = json.loads((root / "data/pearl-desk/alerts.json").read_text(encoding="utf-8"))
        payee = next(item for item in alerts["items"] if item["id"] == "payee-50")
        counts = desk.count_first_output_payees((root / payee["crawl"]).read_text(encoding="utf-8").splitlines())
        expected = desk.payee_alert(counts)["reason"]
        self.assertEqual(payee["reason"], expected)
        drafts = sorted((root / "drafts").glob("*-payee-50.md"))
        self.assertTrue(drafts)
        self.assertIn(expected, drafts[-1].read_text(encoding="utf-8"))
        self.assertNotIn("\u2014", drafts[-1].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
