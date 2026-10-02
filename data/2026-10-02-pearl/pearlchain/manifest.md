# pearlchain.live and Pearl Blockbook raw pulls, 2026-10-02 (ET)

Keyless public endpoints, fetched read-only from the box. Bytes are saved exactly as returned; the two .jsonl files hold one JSON object per request
(`url`, `fetched_et`, `body` = the raw response text). Fetch scripts: scripts/fetch_pearlchain.py and scripts/fetch_pearlchain_addresses.py.
Figures: scripts/derive_pearlchain.py. Charts 03, 04, 05 (address panel), 07 (issuance) and 02 (anchor height): scripts/redraw_03_04_05_07.py, scripts/redraw_02_06_07.py.
Grains: 1 PRL = 1e8 grains. Times are ET (UTC-4). sha256 and byte counts verified against fetch.log.

| file | endpoint | fetched (ET) | bytes | sha256 |
|---|---|---|---|---|
| stats_20261002T193349-0400.json | https://pearlchain.live/api/explorer/stats | 2026-10-02 19:33:49.552138-04:00 | 716 | bdbe42117c3c127d741a0b578dd3a847fe436df9eeb515d83e3384b00393709e |
| charts_20261002T193349-0400.json | https://pearlchain.live/api/explorer/charts | 2026-10-02 19:33:49.720309-04:00 | 79310 | b43dbd88cec6d62aecfa33bc9c9ae57a4ef1aef34cbafc4c3afc7f5bab7b495b |
| addresses_page1_limit25_20261002T193350-0400.json | https://pearlchain.live/api/explorer/addresses?page=1&limit=25 | 2026-10-02 19:33:50.105526-04:00 | 6763 | 5333221e27bc151c4dfab927f66081d98de21a116079af4855bb5eeb8c081dea |
| pools_20261002T193350-0400.json | https://pearlchain.live/api/explorer/pools | 2026-10-02 19:33:50.264629-04:00 | 88661 | bd74410fda8785153efb598bdb4ddba076517fa177ba38fbc9fb79befc513d1b |
| blocks_latest_20261002T193350-0400.json | https://pearlchain.live/api/explorer/blocks | 2026-10-02 19:33:50.535394-04:00 | 2655 | 415bca15e0675e82cfdff466eb3202c161c0d121044bf2480b6402b0340ee3b3 |
| coinbase_crawl_122201-122400_20261002T193350-0400.jsonl | https://pearlchain.live/api/explorer/block/<h> + /tx/<coinbase> for h=122201..122400 | 2026-10-02 19:33:50.695115-04:00..2026-10-02 19:35:31.501002-04:00 | 801906 | cb0d689ed3ca2ae6b1e8604b113ddb89ff15ea051c2a1d2b0a9e64baa3458b03 |
| address_detail_top25_payees5_20261002T193610-0400.jsonl | https://pearlchain.live/api/explorer/address/<a> for 30 addresses | 2026-10-02 19:36:10.230823-04:00..2026-10-02 19:36:27.335407-04:00 | 4940845 | 917c0dd532bd3cd8ee8385372dc0837051500e90ec219a5151613e822685422e |
| blockbook_status_20261002T193657-0400.json | https://blockbook.internal-mainnet.pearlresearch.ai/api/ | 2026-10-02 19:36:57-04:00 | 780 | 7fe8a5b027bf19207db2a5daf22687e3f01bdbc8bf8b4fa898c9feac162d3345 |

Notes:
- The address ranking (addresses?page=1&limit=25) can lag the chain: its rank-1 address shows 8.17M PRL, while its address detail (19:36 ET) shows a zero balance after an outflow at 19:06 ET.
- pools: the explorer's own pool attribution; not matched to coinbase payout addresses in the note.
