import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
R = [
# sources
('''  - label: "pearlchain.live explorer API, address rankings"
    url: https://pearlchain.live/api/explorer/addresses?page=1&limit=25
''','''  - label: "pearlchain.live explorer API, address rankings"
    url: https://pearlchain.live/api/explorer/addresses?page=1&limit=25
  - label: "pearlchain.live explorer API, block, coinbase-tx and address detail (blocks 122,201 to 122,400; pulled 2026-10-02 19:33 to 19:36 ET)"
    url: https://pearlchain.live/api/explorer/block/122400
  - label: "pearlchain.live explorer API, pool attribution"
    url: https://pearlchain.live/api/explorer/pools
'''),
('''  - label: "DexScreener API, PRL ticker search"''','''  - label: "Lighter API, orderBooks and orderBookDetails for the PRL perp (market 4097, pulled 2026-10-02 19:33 ET)"
    url: https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails?market_id=4097
  - label: "DexScreener API, PRL ticker search"'''),
# line 80
('''**Charts and diagrams:** every chart is built only from the raw pulls saved for this note, and each caption names its source and fetch time (ET). Diagrams are simplified schematics.''',
 '''**Charts and diagrams:** charts 01 to 07 are drawn only from raw API pulls saved with this note: CoinGecko (pulled 18:44 to 19:23 ET) and the pearlchain.live explorer (pulled 19:33 to 19:36 ET). Each caption names its source and fetch time (ET). Diagrams are simplified schematics; their CoinGecko and pearlchain.live figures come from the same saved pulls.'''),
# call paragraph
(''' On our read, attention peaked around Sep 27.''', ''),
# 08 caption
('''pearlchain.live stats (block reward, 2026-10-02 11:45 ET)''', '''pearlchain.live stats (block reward, 2026-10-02 19:33 ET)'''),
('''(page re-saved 16:07 ET)''', '''(page read 16:07 ET)'''),
('''(re-saved 16:07 ET)''', '''(read 16:07 ET)'''),
('''both saved 2026-10-02 16:07 ET; pearlchain.live stats (11:45 ET)''', '''both read 2026-10-02 16:07 ET; pearlchain.live stats (19:33 ET)'''),
# derivatives
('''Lighter listed a PRL perp around Sep 29, at up to 3x.''',
 '''Lighter lists an active PRL perp (market 4097, created Sep 29 08:33 ET) with a 33.33% minimum initial margin, so up to 3x (Lighter API orderBooks and orderBookDetails, 19:33 ET).'''),
(''' Margin.Trade has offered 3x PRL perps since June.''', ''),
# on-chain
('''Sources: the pearlchain.live keyless API, fetched 11:45 ET. The official Blockbook reported the same height, 122,270.''',
 '''Sources: the pearlchain.live keyless API, fetched 19:33 to 19:36 ET (stats, charts, address rankings and detail, pools, and a crawl of the last 200 blocks). The official Blockbook (19:36 ET) reported the same height, 122,400.'''),
('''about 43.7 EH/s (unconfirmed). It comes from pearlchain.live at 11:45 ET, which labels it "difficulty-derived ... not measured computation".''',
 '''about 42.2 EH/s (unconfirmed). It comes from pearlchain.live stats at 19:33 ET, which calls it a "Difficulty-derived consensus estimate" that is "not measured computation".'''),
('''15.83% minted, about 332.4M PRL (unconfirmed; explorer and CoinGecko, matching the emission formula). The block reward is 2,288 PRL. The explorer's address total of 342.9M''',
 '''15.84% minted, about 332.7M PRL (unconfirmed; explorer stats at 19:33 ET, and CoinGecko's 332.6M circulating supply at 18:41 ET, matching the emission formula). The block reward is 2,287 PRL. The explorer's address total of 343.1M'''),
('''about 1.02M to 1.07M PRL per day (unconfirmed). Oct 1 was 1,065,348 PRL.''',
 '''about 1.04M to 1.07M PRL per UTC day over Sep 29 to Oct 1 (unconfirmed; explorer blocksDaily). Oct 1 was 1,065,348 PRL.'''),
('''about 421M PRL around Jan 2 to 5, 2027, about 500M around Apr 2 to 8, 2027, and about 640M around Oct 2 to 16, 2027.''',
 '''about 422M PRL around Jan 2, 2027, about 500M around Apr 2, 2027 and about 640M around Oct 2, 2027, at the 194 s target pace from height 122,400. Blocks have recently come faster than target (489 a day over the 30 UTC days to Oct 1, explorer blocksDaily), which would bring these dates forward by about one to five weeks.'''),
('''price would be about $0.88 at 421M supply''', '''price would be about $0.88 at 422M supply'''),
('''"Issuance vs reported volume. Sources: PRL mined per UTC day, pearlchain.live charts (2026-10-02 11:45 ET); CoinGecko market_chart days=365 daily points (pulled 18:51 ET); Now = Oct 1 issuance at $1.11 vs $4.80M 24h volume (CoinGecko coins/pearl-2, 18:41 ET). Unconfirmed."''',
 '''"Issuance vs reported volume, labeled by 00:00 UTC stamp; each pair covers the UTC day ending at that stamp. Sources: PRL mined per UTC day, pearlchain.live charts (2026-10-02 19:33 ET); CoinGecko market_chart days=365 daily points (pulled 18:51 ET); Now = Oct 1 issuance at $1.11 vs $4.80M 24h volume (CoinGecko coins/pearl-2, 18:41 ET). Unconfirmed."'''),
('''anchored at height 122,270 (pearlchain.live stats, 2026-10-02 11:45 ET)''', '''anchored at height 122,400 at the 194 s target pace (pearlchain.live stats, 2026-10-02 19:33 ET)'''),
('''Forty-two addresses with at least 1M PRL each hold 33.6%.''', '''Forty-two addresses with at least 1M PRL each hold 33.6% (address rankings, 19:33 ET).'''),
('''of the top 25 wallets, 17 (60.2M PRL, unconfirmed) have never sent a coin.''', '''of the top 25 ranked wallets, 15 (50.2M PRL, unconfirmed) have never sent a coin (address detail, 19:36 ET).'''),
('''The largest address (8.18M PRL) was created by a consolidation of hundreds of inputs at 04:22 ET on Oct 2. Its owner is unknown.''',
 '''The ranking's top address (8.17M PRL) first received coins at 14:14 ET on Oct 2 and had sent all of them onward by 19:06 ET, so the ranking lags the chain. Its owner is unknown.'''),
('''was mined Apr 27 to May 3. That was before the public miner shipped on May 15, while hashrate was under about 1 EH/s.''',
 '''was mined Apr 27 to May 3 (UTC days, explorer blocksDaily). That was before the public miner shipped on May 15, while explorer hashrate samples stayed at or below about 1.25 EH/s.'''),
('''"Holder concentration. Source: pearlchain.live address rankings (2026-10-02 11:45 ET), as a share of the explorer total of 342.9M PRL (unconfirmed). Address level, not owner level."''',
 '''"Holder concentration. Source: pearlchain.live address rankings (2026-10-02 19:33 ET), as a share of the explorer total of 343.1M PRL (unconfirmed). Address level, not owner level."'''),
('''over the last 200 blocks (Oct 1 23:41 ET to Oct 2 11:34 ET), one payout address found 51% of blocks, and the top three found 84%. Both of the largest payees forward nearly everything they mine, which is typical of pools. Pool names could not be mapped.''',
 '''over the last 200 blocks (Oct 2 07:37 to 19:32 ET), one payout address found 52.5% of blocks, and the top three found 86.5%. Both of the largest payees have sent onward 99.7% to 99.8% of everything they mined (address detail, 19:36 ET), which is typical of pools. Separately, the explorer's own pool attribution puts Kryptex at 205 of the last 392 blocks (52.3%) over 24 hours (pools, 19:33 ET); we did not match pools to payout addresses.'''),
('''"Pool share of the last 200 blocks (Oct 1 23:41 ET to Oct 2 11:34 ET). Source: pearlchain.live coinbase crawl, 2026-10-02 11:45 to 11:50 ET. Four split-coinbase blocks counted to their first output."''',
 '''"Payout-address share of the last 200 blocks (122,201 to 122,400, Oct 2 07:37 to 19:32 ET). Source: pearlchain.live block and coinbase-tx detail, crawled 2026-10-02 19:33 to 19:35 ET. Six split-coinbase blocks counted to their first output."'''),
('''**Hashrate history** (explorer samples, unconfirmed):''', '''**Hashrate history** (explorer 6-hourly samples in the charts pull, 19:33 ET; 08:00 ET readings unless noted; unconfirmed):'''),
('''59.2 on Sep 27, 43.6 on Oct 2.''', '''59.2 on Sep 27, 43.7 on Oct 2.'''),
('''The all-time high was 40,375 active addresses on May 29. In the last 200 blocks, 60% were coinbase-only,''',
 '''The all-time high was 40,375 active addresses on May 29 (explorer charts, UTC days). In the last 200 blocks, 57% (114) were coinbase-only,'''),
('''about 7,187 PRL all time, roughly 0.002% of issuance.''', '''about 7,193 PRL all time (explorer stats, 19:33 ET), roughly 0.002% of issuance.'''),
('''at $1.11, issuance is about $1.13M to $1.19M per day (unconfirmed issuance).''', '''at $1.11, issuance is about $1.15M to $1.18M per day (unconfirmed issuance, Sep 29 to Oct 1).'''),
('''scaling the prlstats figures to the unconfirmed 43.7 EH/s gives roughly $1.66, $0.50 and $0.97 (derived).''', '''scaling the prlstats figures to the unconfirmed 42.2 EH/s gives roughly $1.60, $0.49 and $0.94 (derived).'''),
('''pearlchain.live stats, charts, addresses and coinbase crawl (2026-10-02 11:45 to 11:50 ET)''', '''pearlchain.live stats, charts, addresses, address detail and coinbase crawl (2026-10-02 19:33 to 19:36 ET)'''),
# hype
('''Method: we drew a day-by-day sample of X posts mentioning Pearl, Apr 20 to Oct 2, collected 11:57 to 12:12 ET. It yielded 5,622 posts, of which 2,475 were Pearl-specific. On top of that we read about 75 posts in full. Counts are a sample, not a census.''',
 '''Method: we read about 75 posts in full and cite the ones we rely on by status link. This version reports no post counts: our day-by-day count sample was not saved at the post level, so it is left out until it can be rebuilt reproducibly.'''),
('''mining guides, and peaked May 28. Active addresses peaked the next day.''', '''mining guides. Active addresses peaked on May 29 (40,375, explorer charts).'''),
(''' Post counts and price both peaked on Sep 27.''', ''' Price peaked at the end of Sep 27 (UTC).'''),
('''- **Late-cycle signals.** Median views per Pearl post fell from 850 to 2,461 on most days of Sep 14 to 23 to 50 to 186 since Sep 25. The bullish share of views fell from 27% (Sep 16 to 30) to 5% on Oct 1 and 2 (small sample). Price is down''',
 '''- **Since the peak.** Price is down'''),
('''- **Who drives reach.** Since Sep 1, @brezshares (disclosed holder) and @degennQuant (no disclosure in post text) account for about 25% of Pearl-post views. @margin_trade, a venue promoting its own PRL perps, ran #LongPRL posts. We found no evidence of a bot or copy-paste campaign.''',
 '''- **Who drives reach.** The most visible wave 2 voices in the posts we cite are @brezshares (disclosed holder) and @degennQuant (no disclosure in post text). @margin_trade, a venue promoting its own PRL perps, ran #LongPRL posts.'''),
('''From the Aug 24 week to the Sep 21 week, Pearl posts rose 22x and price rose 5.7x (CoinGecko daily prices at 00:00 UTC Aug 31 and Sep 28, the ends of the two weeks). Active addresses rose 1.9x and transactions 2.3x.''',
 '''From the Aug 24 week to the Sep 21 week, price rose 5.7x (CoinGecko daily prices at 00:00 UTC Aug 31 and Sep 28, the ends of the two weeks). Active addresses rose 1.9x and transactions 2.3x (explorer charts, UTC days Aug 24 to 30 vs Sep 21 to 27).'''),
('''![Three stacked charts of daily Pearl posts on X, PRL price and active addresses, Apr 27 to Oct 1](/assets/2026-10-02-pearl/05-hype-vs-use.svg "Hype vs use. Sources: X post sample collected 2026-10-02 11:57 to 12:12 ET (a sample, not a census); CoinGecko market_chart daily prices at 00:00 UTC (pulled 18:51 ET); pearlchain.live active addresses (11:45 ET). Oct 2 excluded.")''',
 '''![Two stacked charts of PRL daily price and daily active addresses, Apr 27 to Oct 1](/assets/2026-10-02-pearl/05-hype-vs-use.svg "Hype vs use. Sources: CoinGecko market_chart daily prices at 00:00 UTC (pulled 2026-10-02 18:51 ET); pearlchain.live active addresses per UTC day (charts, 19:33 ET). Oct 2 excluded.")'''),
('''- Pool concentration: one payee found 51% of recent blocks.''', '''- Pool concentration: one payee found 52.5% of the last 200 blocks.'''),
('''These scenarios use supply of about 421M at 3 months''', '''These scenarios use supply of about 422M at 3 months'''),
('''- CoinMarketCap (not checked).''', '''- CoinMarketCap (not checked).
- A post-level archive of X post counts (dropped from this version).'''),
# line 232
('''Raw pulls and scripts are archived with the research notes. Data provided by CoinGecko.''',
 '''Saved with this note, each with its ET fetch time and a sha256 manifest: raw CoinGecko pulls (market_chart, coins/pearl-2 and tickers), raw pearlchain.live explorer pulls (stats, charts, address rankings and detail, pools, and a 200-block coinbase crawl), the Pearl Blockbook status, the Lighter order-book pulls, and the scripts that derive the figures and draw the charts. Other sources (X posts, GitHub, Together AI, CoinPaprika, GeckoTerminal, Ethplorer, DexScreener, papers) are cited by link with their read time and are not archived here. Data provided by CoinGecko.'''),
]
for a, b in R:
    n = s.count(a)
    if n != 1: raise SystemExit(f"count {n}: {a[:90]}")
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("applied", len(R))
