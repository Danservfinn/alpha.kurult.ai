# Terminal UX spec for alpha.kurult.ai: interactive price charts, optional command search, dense desk

Author: Arghun (market research). Requested by Danny, 2026-10-03 12:19 ET, with follow-ups at 12:22, 12:23, 12:24 and 12:26 ET.
Builder: Kublai via Hermes Kanban. Reviewer: Orda (exact sha). Deploy approval: Temujin.
Base: `main` at `976908a4534383de97e3dcf51ea56a63643f5883`.

Design rule from Danny: borrow the speed, density and chart feel of a professional terminal, not its learning curve. Every feature here must work by plain click and touch. The command bar is an optional accelerator. No logins, no modal tutorials, no required keyboard shortcuts, readable contrast, fast loads. Features that add friction without payoff are dropped or downgraded (section 4).

Scope of the first Kanban card: the P0 list in section 11 only (interactive price charts plus the minimal look and command bar they need). P1, P2 and Phase 2 (automatic chart-pattern flagging, section 10) are follow-on scope listed in the same card as follow-ons, not built under it.

## 0. Sources and how they are cited

| Key | Source | Cite style |
|-----|--------|-----------|
| G | "Getting started on the Bloomberg Terminal", student guide, Bloomberg L.P. 2017, 28 PDF pages. https://data.bloomberglp.com/professional/sites/10/Getting-Started-Guide-for-Students-English.pdf | G p.N [pdf M], printed page then PDF page |
| S | "Training Booklet", University of Scranton Alperin center, 2016, 69 PDF pages. https://www.scranton.edu/academics/ksom/alperin/Bloomberg%20Training%20Manual.pdf | S p.N [pdf M] |
| W1 | Oliver T. Woolf, "Bloomberg Technical Analysis: A Step by Step Guide", v2.2, 2011 (public copy on Scribd). https://www.scribd.com/document/715920909/Bloomberg-Technical-Analysis | W1, section |
| W2 | "Bloomberg Technical Analysis Handbook" (public copy on Scribd), section "Identifying price patterns LTEC, ATEC, CTEC", handbook p.117. https://www.scribd.com/document/344725294/Bloomberg-Technical-Analysis-Handbook-pdf | W2, page |
| W3 | Cranfield University library blog, "How do I create a share price graph in Bloomberg?" https://blogs.cranfield.ac.uk/library/price-graph-bloomberg/ | W3 |
| W4 | University of Michigan Kresge library, Bloomberg "Tozzi codes" (BTST, GP). https://kresgeguides.bus.umich.edu/bloomberg/TozziCodes | W4 |
| W5 | New York Public Library research guide, "Bloomberg Terminal: Comparative Returns" (COMP). https://libguides.nypl.org/c.php?g=1084166&p=8025762 | W5 |
| W6 | University of Florida business library function cheat sheet (GPO, IGPC, HS, COMP, BTST). https://businesslibrary.uflib.ufl.edu/ld.php?content_id=4006684 | W6 |
| W7 | Text transcription of a GP screen with an RSI study (toolbar labels and legend), bartleby. https://www.bartleby.com/questions-and-answers/the-bloomberg-screen-below-shows-the-nasdaq-index-price-over-the-last-year.-describe-the-technical-i/e5bf9ef3-1880-41ef-8c67-094ff890771c | W7 |
| W8 | Bloomberg Professional Services insight, "Technical indicators point to growth stocks beating value" (ATPR, BTST). https://www.bloomberg.com/professional/insights/markets/technical-indicators-point-to-growth-stocks-beating-value/ | W8 |
| W9 | Launchpad getting-started guides hosted by IIM Ahmedabad and Cornell libraries (Charts, Adding technical studies, Chart grid). https://library.iima.ac.in/public/download/bloomberg/launchpad.pdf , https://guides.library.cornell.edu/ld.php?content_id=18968885 | W9 |
| W10 | Masaryk University mirror, "Technical Analysis" function list (GPO, GPC, IGPO, CNDL, studies). https://www.math.muni.cz/~mrezac/Bloomberg/Technical-Analysis-Bloomberg.pdf | W10 |
| K | Kublai, Bloomberg primer video, 2026-10-03: video-research extraction relayed by the fleet (function priorities ECO, EVTS, command palette, CSV export, TOP digest, ANR, WEI, BTMM, funding tile, SPLC; skip list). Arghun did not view the raw extraction; claims about our site were verified against the repo (section 5.1) | K |
| W11 | Bloomberg "Terminal Essentials: Charting" video, transcript (GP line, GPO bar, GPC candle; GP as scratch pad; Add Data). https://www.youtube.com/watch?v=CoRvxW2eUqM | W11 |

Secondary sources (W1, W2, W7, W10) are third-party copies; they are used only to describe features and feel, never copied into the site.

## 1. Hard constraints (apply to every item)

1. Data licensing. No Yahoo, yfinance or OpenBB data anywhere. CoinGecko is allowed, with a visible credit line on every surface that shows a CoinGecko number. HF Data Library (CC BY 4.0) is a candidate for stocks only after a license check passes; until then every equity, equity index and commodity feature is **not buildable yet (pending the HF Data Library license check, or no licensed source)**. No invented, placeholder or sample numbers. Computed indicators (moving averages, rebased performance) are derived from licensed series and labelled as computed.
2. Sources already live and allowed (from `dist/index.html` on main): CoinGecko, U.S. Treasury daily par yields (via `functions/api/treasury.js`), NY Fed SOFR (with its Terms of Use sentence), ECB daily reference rate, alternative.me Fear and Greed, mempool.space with Blockstream fallback, public chain RPCs via `functions/api/chain.js`, pearlchain.live. This spec adds **no new data host**. CSP `connect-src` must not grow.
3. Static-site friendly. `python3 scripts/build.py` writes `dist/`. First-party JS only (`static/market.js` today). Cloudflare Pages Functions for Treasury and chain. No framework, no bundler at runtime. One vendored library is allowed for charts (section 6.4), served from `'self'`.
4. Low friction (Danny, 12:22 ET). Normal links and click navigation everywhere; works on phones; no login; no modal tutorial or onboarding overlay; no required shortcut; plain-English search with no codes needed; readable contrast; fast loads.
5. No em dashes in code, copy, comments or this spec. The builder rejects U+2014 in shipped files.
6. Homage, not copy. No Bloomberg name, logo, screenshots, keyboard photo, product names or verbatim help text in anything shipped (section 12).
7. No JavaScript still means a working site: notes, ledger, asset pages and sources are plain HTML links. Charts show a no-JS message with a link to the sources.

## 2. What the terminal does, from the two guides

| # | Concept | What the guides say | Cite | Adopt? |
|---|---------|---------------------|------|--------|
| C1 | Color-coded keys | Red stop key (Esc/Cancel), green action keys (Help, Search, Menu, Enter/GO), yellow market sector keys F2 Govt to F11 Crncy, F12 Port | G p.2 [pdf 4]; S p.12 [pdf 13] lists F2 Government, F3 Corporate Bonds, F4 Mortgages, F5 Money Markets, F6 Municipal Bonds, F7 Preferred, F8 Equities, F9 Commodities, F10 Index, F11 Currency, F12 Portfolio | Colors yes, as a visual language for buttons. Physical keys no |
| C2 | Sector keys load securities and open sector menus | `IBM US <EQUITY> <GO>`, `<CORP> <GO>`; `F3<GO>` opens corporate bond menu; `F11<GO>` currency menu; `<F9>GO` commodity menu | G p.2 [pdf 4], p.11 [pdf 13]; S p.45 [pdf 46], p.60 [pdf 61], p.59 [pdf 60] | As optional filter chips (P1) |
| C3 | GO executes, Cancel exits | Enter or GO runs the command line; Esc/Cancel exits the function | G p.2 [pdf 4] | Enter submits search, Esc clears it |
| C4 | Panels | Up to four panels, each with toolbar, command line and function area | G p.4 to p.5 [pdf 6 to 7] | Desk grid of four panels |
| C5 | Mnemonics | `MNEMONIC <GO>`; security vs non-security functions | G p.6 [pdf 8] | As optional aliases only |
| C6 | Loaded security persists | Once a stock is input, only the function is needed; the amber box changes the security | G p.7 [pdf 9], p.15 [pdf 17]; S p.25 [pdf 26] | Light version: asset pages carry their ticker (P1) |
| C7 | Ticker, sector, function syntax | `AAPL<F8> DES` bypasses the menu | G p.6 [pdf 8], p.16 [pdf 18]; S p.26 [pdf 27] | Accepted, never required |
| C8 | Autocomplete and name search | Typing in the command line lists functions and securities; "Simply typing the name of the commodity will give a drop down with listed securities"; BI shows an autocomplete | G p.5 [pdf 7], p.8 to p.9 [pdf 10 to 11]; S p.58 [pdf 59], p.18 [pdf 19] | Yes, core of the search bar, plain-English first |
| C9 | Full search | HL groups results by category | G p.10 [pdf 12]; S p.12 [pdf 13] "Search any topic" | Merged into the one search bar |
| C10 | Menus, breadcrumbs, Menu goes back | Menu hierarchy; Menu key "Navigates back to previous page" | G p.11 to p.12 [pdf 13 to 14]; S p.12 [pdf 13] | Breadcrumb line only. Browser Back is our Menu key |
| C11 | Function screen elements | Red menu bar, title right, numbered actions; amber fields are editable ("Anything with a Yellow/Amber color can be changed"); numbered lines with Number GO | G p.13 [pdf 15]; S p.28 [pdf 29] | Amber means editable, yes. Numbered rows as optional quick-jump (P2) |
| C12 | Amber on black, dense numbered rows | `11) DOW JONES`, `12) S&P 500` with sparklines | G p.13 [pdf 15] | Yes |
| C13 | Security functions | DES, CN, HP, GP, GIP, DVD, ERN, FA, RG, RELS, G | G p.16 [pdf 18]; S p.25 to p.36 [pdf 26 to 37] | Chart and note functions yes; equity fundamentals blocked |
| C14 | Market-wide monitors | TOP news (S p.13 [pdf 14]), WEI (S p.19 [pdf 20]), MOST, MOV, LVI movers (S p.21 [pdf 22]), BTMM rates (S p.47 [pdf 48]), ECO (S p.51 [pdf 52]), FXC (S p.61 [pdf 62]), GLCO (S p.57 [pdf 58]) | G p.22 to p.24 [pdf 24 to 26] | Movers, rates, FX yes; equities, ECO, commodities blocked |
| C15 | Help | HELP <GO>; F1 on a screen opens that function's help; F1 twice for live help | G p.21 [pdf 23]; S p.66 to p.67 [pdf 67 to 68] | A plain help page; no live chat |
| C16 | Launchpad pop-up | First login shows a pop-up to open Launchpad; "You can click No" | S p.8 [pdf 9] | Counter-example: no first-visit pop-ups |
| C17 | Sign-up friction | 16 steps: login creation, work phone, SMS validation, password, default country | S p.2 to p.8 [pdf 3 to 9] | Counter-example: no login, ever |
| C18 | Favorites | FAVE bookmarks favorite functions | S p.68 [pdf 69] | Browser bookmarks plus shareable URLs cover it |
| C19 | DES as hub | "The DES screen is a great Launchpad to links to other Bloomberg functions" | S p.49 [pdf 50]; S p.26 [pdf 27] | Asset page is the hub |

## 3. How terminal price charts work (research summary)

### 3.1 Chart functions

| Function | What it is | Cite |
|----------|------------|------|
| GP | Historical price chart, the default line chart; also shows volume; ranges from 1 minute to yearly; works as a scratch pad that adapts to the loaded security; you can add data (benchmarks, peers, related metrics) from "Add Data" and a related-data box | G p.6 [pdf 8], p.16 [pdf 18], p.22 [pdf 24]; S p.36 [pdf 37]; W11 |
| GIP | Intraday price chart | G p.16 [pdf 18]; W10 lists intraday variants IGPO, IGPC |
| GPO | Bar chart (OHLC bars); GPC is the candlestick chart; IGPO, IGPC are the intraday versions | W6; W10; W11 ("GP for line charts, GPO for bar charts, GPC for candlestick charts") |
| G | Custom chart library: create graph, choose type (single security historical or intraday with studies and events; multi-security up to twenty series, spreads or ratios as line, bar, candle or HLC bands), add studies, set themes and colors, save as a numbered template (e.g. G53) | S p.37 to p.41 [pdf 38 to 42]; W1 section 3 |
| COMP | Compare returns of up to six securities or indexes over a chosen range and period; also a benchmark mode (security vs its index and peers) | W5; W6 |
| HS | Historical spread and ratio of two securities; HSN normalized spread | G p.22 [pdf 24]; W6 |
| HP | Historical price table, daily, weekly or monthly, with a date range | G p.16 [pdf 18]; S p.29 [pdf 30] |
| GF | Graph fundamentals, compare two companies | S p.29 [pdf 30] (equity, blocked here) |
| TECH | Browser of technical studies | S p.36 [pdf 37], p.41 [pdf 42] |
| BTST | Backtest of technical strategies on a security; shows when the strategy would have bought or sold and its P&L | W4; W6; W8 |

GPO and COMP do not appear in either PDF (G or S); their descriptions come from W4 to W6, W10 and W11.

### 3.2 Chart toolbar and feel

- Range buttons across the top left: **1D, 3D, 1M, 6M, YTD, 1Y, 5Y, Max**; custom fixed range by editing amber date boxes (W3; W7 transcribed toolbar "1D 3D 1M 6M YTD 1Y 5Y Max").
- Toolbar items transcribed from a GP screen: "Table", "Compare", "Add Data", "Track", "Annotate", "News", "Zoom", "Key Events", plus numbered menus "94) Suggested Charts", "96) Actions", "97) Edit" (W7).
- Legend at top left listing each series with its current value, e.g. "Last Price", "High on <date>", "Average", "Low on <date>", "SMAVG (50) on Close", "SMAVG (100) on Close", "SMAVG (200) on Close" (W7).
- Studies sit in panes below price, e.g. "RSI (14) on Close" with "Overbought 70, Oversold 30" (W7); studies are added through "Security/Study", via autocomplete or a study browser, and each is edited with a pencil icon, e.g. RSI period 14 to 21 (W1 section 3; W9).
- Typical custom chart: 50/100/200-day simple moving averages, RSI, MACD; colors changed per line (S p.39 to p.41 [pdf 40 to 42]).
- Volume pane under price by default (S p.36 [pdf 37]; W3 "The top panel displays share price and the lower panel indicates volume").
- Line is the default; one click switches to candlesticks (W3).
- Normalize: rebase all series to 100 to compare (W3, via Edit); multi-security charts can scale Y axes independently (W1 section 3).
- Events and news on the chart: "Key Events" tags; "News" click on a date shows that day's news; earnings flags (W3; W4; S p.43 [pdf 44]).
- Annotations: an "Annotate" button opens a palette of trend lines, Fibonacci, text, shapes and measurement tools; annotations save per security and toggle across timeframes (W1 section 4; S p.41 [pdf 42]).
- Templates: any GP, GPC or GPO chart can be saved with studies, annotations and events as a G template (W1 section 2).
- Most used periods: 5 minute, daily, weekly, monthly (S p.44 [pdf 45]).
- Proprietary studies exist (TrendStall, Trender) and alerts on technical criteria (W1 section 4). Not replicated.

### 3.3 Terminal pattern recognition (input for Phase 2)

- CTEC (pattern history for one security), ATEC (patterns across about 50 exchanges), LTEC (patterns for a chosen list); powered by Recognia; each result explains the pattern and links to it on a chart; on a G chart, "Events" can toggle "Chart Patterns" to show historical pattern markers (W2, handbook p.117).
- CNDL marks candlestick patterns (doji, hammer, engulfing) on the price chart (W10; W2).
- BI ATPR: an automated technical pattern library updated daily by 5:30 p.m. New York, covering equities, ETFs, indexes, sovereign bonds, currencies, commodities and ratios (W8).

## 4. Friction filter: what we keep, downgrade or drop

| Terminal feature | Payoff for our visitors | Decision |
|------------------|------------------------|----------|
| Interactive price chart with ranges, candles, volume, crosshair, MAs, compare | High; this is what people come for | **P0 headline** |
| Search bar with plain-English autocomplete | High; one box finds any note or asset | **P0**, codes optional |
| Dense amber-on-black tables | High; more on one screen | **P0** on chart and asset pages; desk grid layout P1 |
| Function codes (DES, GP, TOP, and so on) | Medium for repeat users, zero for newcomers | Optional aliases in search; never shown as the only way |
| Sector keys | Low to medium; we have mostly crypto | P1 as small filter chips on the help and asset index |
| Loaded-security persistence across pages | Low; asset pages already carry context | P1, subtle, no surprises |
| Numbered rows with Number GO | Low for newcomers | P2, numbers shown as decoration plus optional jump |
| MENU overlay with breadcrumbs | Low; browser Back does it | Drop overlay; keep a breadcrumb text line (P1) |
| HL as a separate search | None; merged into one bar | Dropped |
| Red function bar | Cosmetic | P2 |
| Command history on Up arrow | Low | P2 |
| Required keyboard shortcuts, F-key bindings | Negative (conflicts with browser) | Dropped. `/` to focus search is a bonus only |
| Login, onboarding pop-up, tutorial modal (C16, C17) | Negative | Never |
| Custom chart templates (G) | Medium; replaced by shareable URLs that encode chart state | URL state P0, named saved charts P2 |
| Annotations palette | Medium for power users | P1 (trend line, horizontal line, text only) |
| BTST backtest | Low for a research site, risk of reading as advice | P2, research framing only |

## 5. Current site audit (main `976908a`; live https://alpha.kurult.ai fetched 2026-10-03 12:25 ET, matches main)

- Static build: `scripts/build.py` (about 1,500 lines, Python stdlib) validates frontmatter (`title`, `date`, `summary`, non-empty `sources`), renders markdown, writes `dist/` (index, `articles/<slug>/`, 404, sitemap, robots, llms.txt). CSS is the `STYLES` string inside `build.py`.
- `static/market.js` (about 960 lines): CoinGecko ticker; chart panel with BTC, ETH, SOL, PRL and 1H, 4H, 1D buttons drawn as static hand-built SVG (1H is a line from `market_chart?days=2`; 4H draws candles from `ohlc?days=14`; 1D is a line from `market_chart?days=180`); markets table (top 250, gainers, losers, volume, breadth); macro chips; on-chain panel. localStorage cache with a 5-minute chart TTL and per-host backoff. Uses the keyless public CoinGecko API.
- Pages Functions: Treasury XML and chain RPC caching. Strict CSP meta: `script-src 'self'`, fixed `connect-src`, `font-src 'self'`.
- Already terminal-like: black field, amber `#f1bd59` labels, white `#ffffff` data, yellow `#f8c800` highlight, key yellow `#c89830`, blue `#001060` bars, green `#39d441` up, red `#dc5d5e` down (contrast notes in the CSS header); monospace body; uppercase letter-spaced labels; scanline overlay; one yellow key `F1 LEDGER`; decorative `>_` prompt; dense right-aligned market tables; article tear sheet (call strip, position box, key grid); numbered sources.
- Missing: an interactive chart (no crosshair, zoom, volume, MAs, compare, log scale, line/candle toggle, ranges beyond 180 days; candles exist only as a static 4H SVG); any search; asset pages; help page; desk grid; shareable chart URLs.
- Symbol list is duplicated (`HOME_SYMBOLS`, `ASSET_BY_SLUG` in `build.py`; `IDS`, `NAMES` in `market.js`).

### 5.1 Verification of Kublai's "already on the site" list (source K) against main `976908a`

| Claim | Verdict | Evidence in repo |
|-------|---------|------------------|
| Rates strip | True | Macro chips: UST10Y and UST2Y via `/api/treasury` (`functions/api/treasury.js`), SOFR from `markets.newyorkfed.org`, EURUSD from `data-api.ecb.europa.eu` (`static/market.js` `pullTreasury`, `pullSofr`, `pullEcb`) |
| OHLC | Partly true | Only the 4H timeframe uses CoinGecko `ohlc?days=14`, drawn as static SVG candles; 1H and 1D are lines. No interactive OHLC, no volume |
| BTC on-chain | True | On-chain panel, mempool.space with Blockstream fallback (credit line in `build.py` `chain_mount`) |
| Fear and Greed | True | `F&G` chip from `api.alternative.me/fng` |
| Pearl stats | True, conditional | `functions/api/chain.js` `pearlStats()` reads `pearlchain.live/api/explorer/stats`; shown "when shown", with a non-affiliation credit |
| Research ledger | True | Ledger panel on `/` rendered by `render_index` |

## 6. P0 headline: interactive price chart component

### 6.1 What it replicates

| Terminal behaviour (cite) | Our chart |
|---------------------------|-----------|
| GP line chart default, volume pane (S p.36 [pdf 37]; W3) | Line by default, volume pane below |
| GPO bars, GPC candles, one-click switch (W3; W6; W11) | Toggle: Line, Candles, Bars (OHLC) |
| GIP intraday (G p.16 [pdf 18]) | 1D range at 5-minute points is our intraday view |
| Range buttons 1D 3D 1M 6M YTD 1Y 5Y Max (W3; W7) | 1D, 5D, 1M, 3M, 6M, YTD, 1Y, 5Y, Max (Danny's set) |
| Track crosshair with legend values (W7) | Crosshair with OHLCV readout in the legend |
| Zoom (W7) | Wheel, pinch and drag zoom and pan; double-click or a Reset button restores |
| SMAVG 50/100/200 on close (W7; S p.39 to p.41 [pdf 40 to 42]) | MA 50 and MA 200 toggles (MA 100 P1) |
| Compare, Add Data, normalize to 100, COMP up to six (W3; W5; W11) | Compare vs BTC or peers, rebased to 100, up to 4 extra series |
| Independent or log axes (W1 section 3) | Log or linear toggle; percent mode in compare |
| Key Events, News on chart (W3; W4) | Markers where we published a note on that asset, linking to it (P1) |
| Annotate (W1 section 4) | Trend line, horizontal line, text (P1), saved per asset in localStorage |
| Table (W7), HP (S p.29 [pdf 30]) | Table toggle shows the visible series as a dense table (P1) |
| Save as template (W1 section 2) | Chart state in the URL (`?r=1Y&t=candle&ma=50,200&cmp=ETH,SOL&log=1`), so bookmarks and links are the templates |

### 6.2 Data: licensed sources only, fetched client-side

- **Crypto: CoinGecko, fetched in the browser at view time**, the way `market.js` already does, through the existing `getJson` with per-host backoff and a localStorage cache with a TTL of at most 5 minutes (existing `CHART_TTL`).
- **Why client-side, not committed JSON**: CoinGecko's API terms say "We do not encourage caching or storage of Data. However, if you must cache or store Data: You should refresh the cache at least every 24 hours" (https://www.coingecko.com/en/api_terms, section "Data Caching and Storage"). Committed JSON in the repo would be stored data that goes stale and is republished on every deploy. Client fetch keeps the site static, fresh and within the terms, and needs no new host (api.coingecko.com is already in `connect-src`). No Pages Function proxy for chart data.
- **Credit**: every chart shows "Data provided by CoinGecko" linked to https://www.coingecko.com/ under the plot (fleet rule). Note for Temujin: the CoinGecko API terms ask for "Powered by CoinGecko" in a legible font of at least 10px and point to their attribution guide (https://brand.coingecko.com/resources/attribution-guide). Open question whether to show that wording in addition; the builder should make the credit text a single constant so it is a one-line change.
- **Endpoints and honest granularity**:

| Range | Price series | OHLC series (candles, bars) | Volume |
|-------|--------------|-----------------------------|--------|
| 1D | `market_chart?days=1` (5-minute points) | `ohlc?days=1` (30-minute bars) | `total_volumes` from `market_chart` |
| 5D | `market_chart?days=5` (hourly) | `ohlc?days=7` trimmed to 5D (4-hour bars) | same |
| 1M | `market_chart?days=30` (hourly) | `ohlc?days=30` (4-hour bars) | same |
| 3M | `market_chart?days=90` (hourly) | `ohlc?days=90` (4-day bars) | same |
| 6M | `market_chart?days=180` (daily) | `ohlc?days=180` (4-day bars) | same |
| YTD | `market_chart?days=<days since Jan 1 ET>` | `ohlc` with the nearest allowed `days` value, trimmed | same |
| 1Y | `market_chart?days=365` (daily) | `ohlc?days=365` (4-day bars) | same |
| 5Y, Max | **Not available**: the keyless and Demo CoinGecko API restrict history to the past 365 days (CoinGecko docs for `market_chart` and `ohlc`). Buttons render disabled with the text "Needs more than 1 year of licensed history". They enable only if a licensed longer-history source is approved in a later spec revision | | |

  Granularity source: CoinGecko docs, `market_chart` auto granularity (1 day 5-minutely, 2 to 90 days hourly, over 90 days daily) and `ohlc` candle body (1 to 2 days 30 minutes, 3 to 30 days 4 hours, 31 days and beyond 4 days). The legend always states the bar size ("Bars: 4 hours").
- **Volume honesty**: CoinGecko `total_volumes` is a rolling 24-hour volume sampled at each timestamp, not per-bar volume. Label the pane "24h volume (rolling)". Do not sum it into bars.
- **Moving averages**: computed in the browser on daily closes from `market_chart?days=365`, labelled "MA 50 (computed)" and "MA 200 (computed)". With 365 days of history, MA 200 exists only for the most recent 165 days; it is drawn where defined and the legend says so. Not offered on ranges with sub-daily bars unless computed on daily closes.
- **Compare**: each extra series is its own `market_chart` fetch (sequential, backoff respected), rebased to 100 at the first visible point. Max 4 extra series to stay inside public rate limits. Default compare preset: vs BTC.
- **Stocks and indices**: not buildable yet, pending the HF Data Library license check. Commodities: no licensed source, not buildable yet.
- **Non-crypto series already licensed** (UST2Y, UST10Y from Treasury; EURUSD from ECB): line chart only, daily, through the existing Treasury function and ECB host, with their existing source lines (P1).

### 6.3 Component spec

Layout (top to bottom, one panel):
1. Header row: asset name and ticker, last price and 24h change from the same CoinGecko response, "as of" time in ET.
2. Toolbar row (wraps on phones, every control is a normal button with a visible label, minimum 40px tap target):
   - Range: `1D 5D 1M 3M 6M YTD 1Y 5Y Max` (segmented, `aria-pressed`).
   - Type: `Line | Candles | Bars`.
   - Studies: `MA 50`, `MA 200` toggles.
   - Scale: `Log` toggle.
   - `Compare` opens an inline (not modal) picker row with chips: BTC and the other site assets; tap to add or remove; shows "+ add" search reusing the search component.
   - `Reset` restores zoom.
3. Legend (top left inside the plot, like W7): crosshair date and time in ET, O H L C (or price on line mode), 24h volume, each MA value, each compare series value and percent since start, in series colors. When the crosshair is not active it shows the last values.
4. Price pane (about 72 percent of height) with right price axis, last-price label.
5. Volume pane (about 28 percent), bars colored by up or down close.
6. Footer: "Data provided by CoinGecko" link, bar size, "Aggregated price, not one exchange", and the chart library attribution (section 6.4).

Interaction:
- Mouse: hover shows crosshair and readout; wheel zooms around the cursor; drag pans; double-click resets.
- Touch: tap or press-and-drag shows the crosshair; pinch zooms; one-finger horizontal drag pans; the page still scrolls vertically when the gesture is vertical (no scroll trap).
- Keyboard (optional, never required): toolbar buttons are tabbable; when the plot is focused, Left and Right move the crosshair by one bar, `+` and `-` zoom, `0` resets.
- State is mirrored to the URL query (`r`, `t`, `ma`, `cmp`, `log`) with `history.replaceState`, so reload, share and bookmark reproduce the chart. No state in cookies.
- Empty and error states: "No licensed data for this range." or "Price source busy, showing data from HH:MM ET." using the existing stale-stamp logic. Never draw fake points.
- Reduced motion: no animated transitions.

Palette (dark, terminal-like; non-text graphics at least 3:1 on black):

| Element | Color |
|---------|-------|
| Background | `#000000` |
| Grid | `#1a2a55` hairlines |
| Axis text, legend labels | `#f1bd59` (12.16:1) |
| Legend values | `#ffffff` |
| Primary line | `#f1bd59` 2px |
| Up candle or bar, up volume | `#39d441` (10.67:1) |
| Down candle or bar, down volume | `#dc5d5e` (5.77:1) |
| Volume bars | same hues at 50 percent opacity |
| MA 50 | `#ffffff` 1px |
| MA 200 | `#5fa8ff` 1px (8.53:1) |
| Compare series | `#ffffff`, `#5fa8ff`, `#39d441`, `#f8c800` (primary stays amber) |
| Crosshair | `#507098` dashed, axis labels black on `#f8c800` |
| Last price label | black on `#f1bd59` |

Performance:
- The chart library loads only on pages that contain a chart, with `defer`, and on the home page only when the chart panel is within one viewport of the screen (IntersectionObserver).
- Budget: home page HTML plus CSS plus first-party JS at most 80 KB gzipped, excluding the chart library (62 KB gzipped, measured below). First chart paint within 1.5 s of the CoinGecko response on a mid-range phone.

### 6.4 Library recommendation: TradingView Lightweight Charts

- Package `lightweight-charts`, latest `5.2.1` (npm registry, checked 2026-10-03). License **Apache-2.0** (repo LICENSE file and npm metadata). One dependency, `fancy-canvas` 2.1.0, license **MIT**, already bundled in the standalone build.
- Standalone production build `dist/lightweight-charts.standalone.production.js` measured at 197,922 bytes, 62,279 bytes gzipped. No network calls, no telemetry, canvas-based, works with `script-src 'self'`.
- Built-in support for what we need: line, candlestick and bar (OHLC) series; histogram series for volume in its own pane; crosshair with subscription for a custom legend; mouse wheel and pinch zoom, drag pan, kinetic scroll on touch; price scale modes Normal, Logarithmic, Percentage and IndexedTo100 (the last one is our compare mode).
- Attribution obligations (repo README, "License and attribution"): keep the Apache-2.0 license; add the attribution notice from the NOTICE file ("TradingView Lightweight Charts™, Copyright (c) 2025 TradingView, Inc. https://www.tradingview.com/") **and** a link to https://www.tradingview.com/ on a page available to users. The `attributionLogo` chart option satisfies the link requirement on the chart itself. Plan: set `attributionLogo: true` explicitly, add the NOTICE text and link to `/help/#credits`, and ship `static/vendor/LICENSE-lightweight-charts` and `static/vendor/NOTICE-lightweight-charts` next to the vendored file.
- Vendoring: copy the standalone file into `static/vendor/lightweight-charts-5.2.1.js` with its LICENSE and NOTICE; `build.py` copies it into `dist/vendor/`. Pin the version; record the sha256 in `PUBLISH.md`. No CDN.
- Alternatives considered: uPlot (MIT, smaller, but candles, panes and touch zoom need more custom code); Apache ECharts (Apache-2.0, much heavier); keeping the hand-built SVG (no zoom, crosshair, candles). Lightweight Charts is the best fit for terminal feel at low cost.

## 7. P0: minimal search and command bar (plain English first)

P0 ships only what charts and the friction check need: one input, plain-English autosuggest over notes and assets, and the chart codes. The richer Cmd-K palette with related functions is P1 (section 9A.3).

- One input under the masthead on every page, `<form role="search" action="/search/" method="get">` so it works without JS (static `/search/` page lists everything with in-page filtering when JS is on, and a full plain list when JS is off).
- Placeholder: "Search notes and assets, e.g. pearl". No code knowledge needed.
- Autocomplete opens after 1 character, max 8 rows, grouped **Notes**, **Assets**, **Pages**, **Codes** (codes last). Match order: asset ticker or name prefix, note title words, note summary and tags, body keywords from a build-time index, then function codes.
- Examples that must work: `pearl` and `prl` show the Pearl note and the PRL asset; `bitcoin`, `btc` show BTC; `rates` jumps to the rates chips on `/`; `chart btc` opens the BTC chart; `spacex` shows any note that mentions SpaceX, and if none, the honest row "No notes or licensed data for spacex" plus a link to the ledger. No remote lookup ever; the index is `dist/search.json`, built by `build.py` from article frontmatter and body text.
- Optional codes, accepted when typed: `PRL DES` (asset note), `BTC GP` (chart, 1Y line), `BTC GIP` (chart, 1D), `BTC GPO` (chart, bars), `BTC GPC` (chart, candles), `COMP BTC ETH SOL` (compare), `TOP` (ledger), `HELP` (help page), `GMM` or `MOST` (Markets panel on `/`), `BTMM` (rates chips on `/`). Sector words are accepted but optional (`PRL CRYPTO DES`).
- Enter opens the highlighted row (or the first). Esc clears, then closes the list. Arrow keys move. Clicking or tapping a row works the same. `/` focuses the bar as a bonus, never required, and is ignored while typing in a field.
- Messages are inline under the bar in an `aria-live` region; never a modal. Unknown code: "No match for XYZ. Showing search results instead."
- ARIA combobox pattern: `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant`; list is `role="listbox"`.

## 8. P0: asset pages and help (desk grid is P1)

### 8.1 Asset pages (the hub, after C19)
- Prebuilt `/s/<sym>/` for every row in the securities table (BTC, ETH, SOL, PRL at launch): the full interactive chart, the latest note on that asset (title, call strip, link), all notes on it, and its on-chain card where one exists. Breadcrumb line `Home > Crypto > PRL` as plain links.
- One securities table in `build.py` replaces the duplicated symbol lists and is emitted into `search.json`.

| Sym | Name | Class | Data | Credit |
|-----|------|-------|------|--------|
| BTC | Bitcoin | Crypto | CoinGecko `bitcoin` | Data provided by CoinGecko |
| ETH | Ether | Crypto | CoinGecko `ethereum` | same |
| SOL | Solana | Crypto | CoinGecko `solana` | same |
| PRL | Pearl | Crypto | CoinGecko `pearl-2` | same |
| BTC.D, TOTAL | Dominance, total cap | Index (crypto) | CoinGecko global | same |
| EURUSD | Euro reference rate | Crncy | ECB | Source: ECB statistics |
| UST2Y, UST10Y | Treasury par yields | Govt | U.S. Treasury | U.S. Department of the Treasury |
| SOFR | SOFR | M-Mkt | NY Fed | existing NY Fed Terms of Use sentence |

Equity, Index (equity), Cmdty rows: none until a licensed source passes review.

### 8.2 Home desk grid (P1; after C4; not named after any product)
```
+------------------------------+------------------------------+
| Chart (BTC, 1Y, interactive) | Movers (existing Markets)    |
+------------------------------+------------------------------+
| On-chain (existing)          | Rates and FX (UST2Y, UST10Y, |
|                              | SOFR, EURUSD, BTC.D, TOTAL,  |
|                              | F&G chips with sources)      |
+------------------------------+------------------------------+
| Research ledger (full width, newest first, every row a link)|
+-------------------------------------------------------------+
```
- Two columns at 64rem and up; one column below 48rem; no horizontal scroll at 360px. Panel heads are links to the full page for that panel. The ledger is visible without scrolling on a 1280x800 desktop window.
- Existing source lines stay in the panel they describe; nothing is dropped.

### 8.3 Help page (P0, minimal: codes, sources, credits)
- Static `/help/`: a short plain-English intro (3 lines), "Ways to get around" (click, search, optional codes), the code list as a dense table (code, what it does, example, status), data sources and credits (CoinGecko, Treasury, NY Fed, ECB, alternative.me, mempool.space, Blockstream, pearlchain.live, TradingView Lightweight Charts NOTICE and link). Not-buildable codes are listed with the reason. No tutorial, no video, no pop-up.

### 8.4 Visual tokens and type

Keep every existing token in `build.py` `STYLES`. Add: `--go #39d441` (black text, 10.67:1) for primary action buttons; `--stop #c0132a` only with white text (6.24:1), used sparingly (clear buttons, error bars); `--field #f1bd59` amber fill with black text (12.16:1) for editable fields (search input focus state, date inputs). Rule: amber fill means editable (S p.28 [pdf 29]; G p.13 [pdf 15]).

Type: `--mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace;` everywhere; `font-variant-numeric: tabular-nums` on tables, legends and chips. Dense tables: `.78rem`, line height 1.25, cell padding `.15rem .35rem`, numbers right-aligned. Body text in notes stays at least 15px with 1.65 line height for readability. No third-party fonts.

## 9. Gap table

| # | Terminal feature (cite) | Current state | Proposed change | Priority |
|---|------------------------|---------------|-----------------|----------|
| G1 | GP interactive chart (S p.36 [pdf 37]; W3; W7) | Static SVG, 3 timeframes | Lightweight Charts component, section 6 | P0 |
| G2 | Range buttons (W3; W7) | 1H, 4H, 1D | 1D 5D 1M 3M 6M YTD 1Y live; 5Y, Max disabled with reason | P0 |
| G3 | GPO bars, GPC candles (W6; W11) | Static 4H candles only | Line, Candles, Bars toggle | P0 |
| G4 | Volume pane (S p.36 [pdf 37]) | None | 24h rolling volume pane, labelled | P0 |
| G5 | Track crosshair and legend (W7) | None | Crosshair with OHLCV legend | P0 |
| G6 | Zoom (W7) | None | Wheel, pinch, drag, reset | P0 |
| G7 | SMAVG 50/200 (W7; S p.39 [pdf 40]) | None | MA 50, MA 200 computed, labelled | P0 |
| G8 | COMP, Compare, normalize (W3; W5) | None | Compare vs BTC or peers, rebased to 100 | P0 |
| G9 | Log scale (W1) | None | Log toggle | P0 |
| G10 | Templates (W1 section 2) | None | Chart state in URL | P0 |
| G11 | Autocomplete, name search (G p.9 [pdf 11]; S p.58 [pdf 59]) | None | Minimal plain-English search bar, chart codes optional (section 7) | P0 |
| G12 | DES hub (S p.49 [pdf 50]) | Article pages only | `/s/<sym>/` asset pages hosting the chart | P0 |
| G14 | HELP (G p.21 [pdf 23]) | None | Minimal static `/help/` with codes, sources and the chart library credit | P0 |
| G35 | Minimal look | Terminal palette exists | Tokens and type in 8.4 applied to chart, search and asset pages | P0 |
| G13 | Panels (G p.5 [pdf 7]) | Vertical stack | Desk grid, 8.2 | P1 |
| G36 | ECO economic calendar (S p.51 [pdf 52]; K) | None | 9A.1 | P1 |
| G37 | EVTS events calendar (S p.15 [pdf 16]; K) | None | 9A.2, crypto events, curated with sources | P1 |
| G38 | Command palette (G p.9 [pdf 11]; K) | None | Cmd-K palette, 9A.3 | P1 |
| G39 | CSV export (G p.17 to p.19 [pdf 19 to 21]; K) | None | 9A.4 | P1 |
| G40 | TOP digest (G p.24 [pdf 26]; S p.13 [pdf 14]; K) | Ledger | 9A.5, 9am and 9pm ET | P1 |
| G15 | Key Events, News on chart (W3; W4) | None | Note markers on chart linking to notes | P1 |
| G16 | Annotate (W1 section 4) | None | Trend line, horizontal line, text; localStorage per asset | P1 |
| G17 | Table, HP (W7; S p.29 [pdf 30]) | None | Table toggle under the chart (CSV per 9A.4) | P1 |
| G18 | TECH studies: RSI 14, MACD (W7; S p.39 [pdf 40]) | None | RSI and MACD panes, computed | P1 |
| G21 | Sector keys (G p.2 [pdf 4]; S p.12 [pdf 13]) | One yellow key | Optional filter chips | P1 |
| G41 | Site-side alerts | None | 9A.11 | P1 |
| G42 | ANR plus ledger backtest plus calibration log (G p.22 [pdf 24]; K) | None | ONE artifact, 9A.6 | P2 |
| G43 | WEI as a sector heatmap (S p.19 [pdf 20]; K) | None | CoinGecko categories heatmap, 9A.7 | P2 |
| G44 | BTMM money-market panel (S p.47 [pdf 48]; K) | Chips | 9A.8 | P2 |
| G45 | Funding and borrow-rate tile (K) | None | 9A.9 | P2 |
| G46 | SPLC dependency map (S p.34 [pdf 35]; K) | None | 9A.10, DefiLlama permission needed | P2, license gated |
| G22 | Number GO (G p.13 [pdf 15]) | None | Optional numbered quick-jump | P2 |
| G25 | FXC matrix (S p.61 [pdf 62]) | EURUSD chip | ECB reference-rate cross matrix via the allowed ECB host | P2 |
| G26 | Multi-chart grid (W9) | None | `/grid/` with 4 small charts | P2 |
| G27 | Named saved charts (W1) | None | localStorage list of saved URLs | P2 |
| G29 | Red function bar (G p.13 [pdf 15]) | Blue heads | Cosmetic variant | P2 |
| G31 | Equity WEI, equity DES/FA/ERN/DVD, GF, Cmdty (S p.19 [pdf 20], p.25 to p.30 [pdf 26 to 31], p.57 [pdf 58]) | None | **Not buildable yet** (HF Data Library license check pending, or no licensed source) | blocked |
| G32 | 5Y and Max ranges | None | **Not buildable yet**: CoinGecko keyless/Demo history is 365 days | blocked |
| G33 | Login, Launchpad pop-up, F1 live help (S p.2 to p.8 [pdf 3 to 9], p.67 [pdf 68]) | None | Never | dropped |
| G47 | BMAP (S p.59 [pdf 60]), FLY, restaurants, classifieds, chat (MSG, G p.24 [pdf 26]) | None | Skip list (K): not built | dropped |
| G34 | Pattern recognition (W2; W8) | None | Phase 2, section 10 | Phase 2 |

## 9A. Follow-on specs (P1 and P2, not in the first card)

### 9A.1 ECO economic calendar (P1)
- Events: CPI, nonfarm payrolls (Employment Situation), FOMC decisions and minutes, weekly initial jobless claims, plus PCE, GDP and retail sales as stretch. Columns: date and time ET, event, period, our impact rating 1 to 4, prior and actual when licensed, source link.
- Impact rating 1 to 4 is our editorial judgement, labelled "Our impact rating (1 low, 4 high)", set in a committed `data/eco-impact.yaml`; default CPI 4, NFP 4, FOMC 4, claims 2.
- Source options, in order of preference:
  1. Primary U.S. government schedules (public domain works of the U.S. government): BLS release schedule (CPI, Employment Situation), U.S. Department of Labor weekly claims schedule, Federal Reserve FOMC meeting calendar. Fetched at build time and committed as dated JSON with source URLs. No key.
  2. FRED release calendar (`fred/releases/dates`). FRED API Terms of Use checked 2026-10-03 (https://fred.stlouisfed.org/docs/api/terms_of_use.html): requires an API key (so server-side only, a Pages Function secret or build-time fetch, never in browser JS), requires the notice "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis." placed prominently, requires showing users a link to the FRED API Terms of Use and stating users agree to them, forbids using FRED or Federal Reserve marks or implying endorsement, forbids apps that replicate the essential FRED experience, and says series may be owned by third parties with their own copyright (check each series' notes for "Copyright" before showing values). Release dates are FRED metadata; actual values come only from public-domain series or after the owner check.
- Recommendation: option 1 for P1; FRED only if Temujin accepts the notice and terms-link requirements.
- Static: rebuilt at least daily by the builder; page `/eco/`; alias `ECO`.

### 9A.2 EVTS crypto events calendar (P1)
- Event types: token unlocks, network upgrades and hard forks, halvings, governance votes, and COIN and MSTR earnings dates.
- Every entry needs a licensed or primary source; entries live in committed `data/events.yaml` with `date`, `type`, `asset`, `title`, `source_url`, `confidence` (scheduled, estimated). The builder rejects an entry without a source.
- Per type:
  - Halvings: computed estimate from current block height (mempool.space, already allowed) and the 210,000-block schedule; labelled "Estimated from block height, mempool.space".
  - Upgrades and forks: curated from primary project announcements (e.g. official foundation or client release notes), linked per entry.
  - COIN and MSTR earnings dates: from each company's investor-relations press release or SEC EDGAR 8-K, linked per entry (dates only; no equity price data, which stays pending the HF license check).
  - Token unlocks: **source needed** (commercial unlock datasets require a license; DefiLlama unlocks are Pro-only and its terms restrict commercial use).
  - Governance votes: **source needed** (no licensed feed reviewed yet); manual entries with a link to the official proposal page are allowed.
- Page `/evts/`, alias `EVTS`; events also appear as markers on that asset's chart (ties to G15).

### 9A.3 Cmd-K command palette (P1)
- Opens on Cmd+K or Ctrl+K and also from a visible "Search" button in the masthead (keyboard never required). It is a user-invoked overlay, never shown automatically; Esc or a tap outside closes it.
- One input, autosuggest after one character: plain words first ("pearl", "bitcoin chart", "rates", "calendar"), then assets, notes, pages, and codes. Each asset or note row shows related functions as small chips (Chart, Candles, Compare vs BTC, Notes, Events, Export CSV), the way loading a security shows its function menu (G p.7 [pdf 9]; S p.49 [pdf 50]).
- Recent items stored in localStorage only. Same `search.json` index as the P0 bar; no remote lookups.

### 9A.4 CSV export on every table (P1)
- Every table (markets, ledger, events, ECO, chart Table view, digest) gets a small "CSV" button that downloads the visible rows client-side via a Blob, no server.
- First lines of each file: `# Source: <credit line>`, `# Retrieved: <timestamp ET>`, `# alpha.kurult.ai research only, not advice`.
- Licensing gate: our own tables (ledger, events, ECO dates from U.S. government schedules) ship first. Tables of CoinGecko data get CSV only after Temujin confirms CoinGecko's terms allow end-user download of displayed data (their API terms discourage storage and require attribution); until then the button is hidden on those tables. This mirrors the terminal's export model, which keeps data on a licensed workstation (G p.17 [pdf 19]).

### 9A.5 TOP digest at 9am and 9pm ET (P1)
- Formalizes the Ledger into a twice-daily digest, after TOP (G p.24 [pdf 26]; S p.13 [pdf 14]).
- Arghun files `articles/YYYY-MM-DD-top-am.md` and `-top-pm.md` by 09:00 and 21:00 ET with frontmatter `type: digest`, a 5 to 8 bullet summary, each bullet linking a ledger note or a sourced figure; normal `sources` rules apply; no invented numbers.
- The builder renders `/top/` (latest digest first, archive below) and keeps the ledger as the index of full notes. Alias `TOP` opens `/top/`; the ledger stays one click away.
- A missed slot shows "No digest filed for 09:00 ET" rather than an empty or stale page.

### 9A.6 ANR-style track record, ledger backtest and calibration log as ONE artifact (P2)
- One artifact, `/record/` built from committed `data/record.jsonl`, replaces three overlapping ideas: an ANR-style table of our ledger calls (G p.22 [pdf 24]), a ledger backtest, and the calibration log from card t_968f4c34. Dedupe note: the calibration log from t_968f4c34 is merged here, not kept as a second file or page; one row per call keyed by note slug, so no call is counted twice.
- Per call: date, ticker, rating, conviction, entry price as published (with its source), price at 7, 30 and 90 days from CoinGecko (client-side fetch at view time per 6.2, or from the record file only if refreshed within CoinGecko's 24-hour guidance), outcome versus the call, falsifiers hit.
- Calibration: hit rate by conviction bucket with counts; shown only once a bucket has at least 10 calls, otherwise "Too few calls to score".
- Research only; no forward-looking claims.

### 9A.7 WEI-style sector heatmap from CoinGecko categories (P2)
- CoinGecko `coins/categories` (market cap and 24h change per category), drawn as a treemap or grid heatmap colored by 24h change, credit line under it. Client-side fetch per 6.2. Equity WEI stays blocked.

### 9A.8 BTMM money-market panel (P2)
- Rows: SOFR, EFFR and OBFR (NY Fed reference rates, same Terms of Use sentence as SOFR today), Treasury bill rates and the par curve (U.S. Treasury daily rates, already fetched by `functions/api/treasury.js`). No Yahoo. Commercial paper rates only if a Federal Reserve Board public source is confirmed. Each row has its source line.

### 9A.9 Funding and borrow-rate tile (P2)
- Perpetual funding: CoinGecko `derivatives` endpoint (funding rate per derivatives ticker), already covered by the CoinGecko credit; show BTC, ETH, SOL median funding across listed venues with venue count.
- Borrow rates: on-chain read of lending pool rates (e.g. Aave reserve data) through the existing chain Pages Function and public RPCs is allowed (our own read of public chain state). Any third-party yield API: **source needed** until its terms are checked (DefiLlama yields fall under the DefiLlama terms below).

### 9A.10 SPLC-style dependency map from DefiLlama (P2, license gated)
- Idea: map protocol dependencies (chains, oracles, bridges, stablecoin exposure) after SPLC (S p.34 [pdf 35]).
- DefiLlama terms checked 2026-10-03 (https://defillama.com/terms): a revocable personal, non-commercial licence; users agree not to "copy, scrape, harvest or otherwise exploit the Content & Data for commercial purposes without prior written consent" and not to use the information for competitive purposes; their FAQ calls the API open and free and asks for citation. Status: **not buildable yet** until Temujin decides whether alpha.kurult.ai counts as commercial or obtains written consent. If cleared: credit "Data from DefiLlama", client-side fetch from `api.llama.fi` (a new CSP host, which needs its own approval).

### 9A.11 Alerts (P1, site-side only)
- In-page only: a user sets a price level on a chart; while the page is open the level is drawn and the chart header highlights when crossed; settings live in localStorage. No email, push, SMS, Slack, browser notification permission prompts or server-side alerting. External alert channels are out of scope unless Temujin assigns them.

### 9A.12 Skip list (K)
BMAP, FLY, restaurant guides, classifieds, chat and messaging: not built.

## 10. Phase 2 (follow-on scope, not in the first card): automatic chart-pattern flagging

Precedent: the terminal flags patterns through CTEC, ATEC and LTEC (Recognia), a "Chart Patterns" toggle under Events on G charts, CNDL candlestick patterns, and the BI ATPR daily pattern library (W2 p.117; W8; W10). Ours is a transparent, open method on licensed CoinGecko series, shown as research only.

### 10.1 Patterns
Rising wedge; falling wedge; ascending triangle; descending triangle; symmetric triangle; head and shoulders; inverse head and shoulders; double top; double bottom; ascending, descending and horizontal channels; bull and bear flags; pennants; support break and resistance break.

### 10.2 Detection method
1. Series: daily closes plus CoinGecko OHLC highs and lows where available (1Y, 4-day bars) and hourly closes for 1M and 3M. Run in the browser on the same data the chart already has; no new fetches.
2. Pivots: swing highs and lows with a fractal window k (a bar is a swing high if its high is the max of the 2k+1 bars around it); k scales with range (k = 3 on daily, 5 on hourly). Optional ZigZag filter: discard swings smaller than max(ATR(14) x 1.5, 3 percent).
3. Trendlines: fit upper line through swing highs and lower line through swing lows by least squares on log price, using the last N pivots (N from 2 to 5), and accept a line only with at least 2 touches for triangles and wedges and 3 total touches on the pair (minimum touches: 2 on one side, 3 combined). A touch is a pivot within tolerance = max(0.5 x ATR(14), 1 percent of price) of the line. No close may violate the line by more than tolerance inside the pattern window.
4. Classification by slopes (per bar, log price) and convergence:
   - Rising wedge: both slopes positive, lower slope greater than upper slope, lines converge (gap shrinks at least 30 percent over the window), apex within 1.5 window lengths ahead.
   - Falling wedge: both negative, upper slope more negative than lower, converging.
   - Ascending triangle: upper slope flat (absolute slope under a flatness threshold epsilon), lower positive. Descending: lower flat, upper negative. Symmetric: upper negative, lower positive, converging.
   - Channels: slopes within 10 percent of each other, gap stable within 20 percent.
   - Head and shoulders: three swing highs where the middle exceeds both shoulders by at least 1 x ATR, shoulders within 1.5 x tolerance of each other, a neckline through the two intervening lows with absolute slope below a cap; inverse is mirrored. Confirmed only on a close beyond the neckline.
   - Double top or bottom: two swing extremes within tolerance, separated by at least 10 bars, with a trough or peak between them at least 2 x ATR away; confirmed on a close through that trough or peak.
   - Flag: a pole (move of at least 3 x ATR within 10 bars) followed by a short counter-sloped channel of 5 to 20 bars; pennant: same pole followed by a small symmetric triangle.
   - Support or resistance break: a level touched at least 3 times within tolerance, then a close beyond it by more than tolerance; optional confirmation on the next close.
5. Scoring: confidence from touches, fit residual, convergence quality and pattern length; show only patterns at or above a threshold, at most 2 per chart, newest first; mark each "forming" or "confirmed".

### 10.3 Display
- Overlay the trendlines (dashed, amber for the pattern, white for neckline or level) on the price pane and a small label at the pattern's right edge, e.g. "Rising wedge (forming)".
- Tap or hover the label for a plain-English tooltip: what the shape is, the typical textbook implication (e.g. "Rising wedges are often read as bearish when price closes below the lower line"), the detection inputs (window, touches, tolerance) and the caveat "Automated pattern detection. Research only, not advice. Patterns fail often."
- A `Patterns` toggle in the toolbar, off by default on first load (low friction, low noise); state in the URL (`pat=1`).

### 10.4 Validation plan
1. Backtest on all CoinGecko series the site carries, using 365-day daily and 90-day hourly windows, walk-forward month by month, recording every detection with its parameters.
2. Hand-label a stratified sample of at least 200 windows (balanced across patterns and no-pattern windows), labelled by two people blind to the detector, with disagreements resolved by a third.
3. Report precision per pattern (and recall on the labelled set) with confidence intervals; ship only patterns with precision at or above 0.7 on the sample; the rest stay hidden behind a debug flag.
4. Tune k, tolerance, flatness epsilon, convergence and minimum touches on a training split; report final numbers on a held-out split to avoid overfitting.
5. Report the post-pattern move distribution (e.g. 10-bar forward return) as descriptive context only, never as a forecast, and never shown as a trade signal.
6. Noise guard: no more than 2 labels per chart; suppress patterns shorter than 10 bars; rerun the validation when thresholds change.

Phase 2 acceptance criteria will be written in its own spec revision after P0 ships.

## 11. Priority list

**P0 (the first Kanban card): interactive price charts plus the minimal look and command bar they need.** G1 to G12, G14 and G35: the chart component with all of section 6 (ranges, line, candles and bars, volume pane, crosshair with OHLCV legend, zoom and pan by mouse and touch, MA 50 and MA 200, compare vs BTC or peers rebased to 100, log toggle, URL state, CoinGecko credit, library attribution); `/s/<sym>/` asset pages that host it; the minimal plain-English search bar with optional chart codes (section 7); a minimal `/help/` with codes, sources and credits; the visual tokens in 8.4; and the friction, licensing, trademark, em-dash and performance gates in section 13.

**P1 (follow-on):** desk grid (G13); ECO calendar (G36); EVTS crypto events (G37); Cmd-K palette (G38); CSV export (G39); TOP digest 9am and 9pm ET (G40); chart events, annotations, table, RSI and MACD (G15 to G18); sector chips (G21); site-side alerts (G41).

**P2 (follow-on):** one record artifact merging ANR, ledger backtest and the t_968f4c34 calibration log (G42); WEI sector heatmap (G43); BTMM money-market panel (G44); funding and borrow tile (G45); SPLC map, license gated (G46); number quick-jump, FXC, multi-chart grid, saved charts, red bar (G22, G25 to G27, G29).

**Blocked:** G31, G32. **Dropped:** G33, G47. **Phase 2:** G34 (section 10).

## 12. Trademark and style caution

- "Bloomberg", "Bloomberg Terminal", "Launchpad", "Bloomberg Intelligence", "Bloomberg Market Concepts", their logos and keyboard design are marks or trade dress of Bloomberg Finance L.P. or affiliates. None of them appear in shipped HTML, CSS comments, meta tags, `llms.txt`, alt text, page titles, or copy. Do not say "Bloomberg-style" on the site. No implied affiliation, endorsement or data from Bloomberg.
- No screenshots, keyboard photos, icons or help text copied from any source. Our labels are generic chart words (Range, Candles, Bars, Compare, Log, Reset).
- Function codes are optional homage aliases with our own descriptions. If Temujin or Danny prefers zero overlap, remove them from `search.json`; nothing else depends on them.
- "TradingView" and "Lightweight Charts" appear only in the required attribution. CoinGecko brand use follows their attribution guide and must not suggest endorsement.
- Internal artifacts (this spec, branch names) may name the reference for traceability.

## 13. Acceptance criteria (Orda tests these on the exact sha)

Build and gates
1. `python3 scripts/build.py` ends with `BUILD_OK`. `dist/help/index.html`, `dist/search/index.html`, `dist/search.json`, `dist/s/btc/index.html`, `dist/s/prl/index.html` and `dist/vendor/lightweight-charts-5.2.1.js` exist, and `dist/vendor/` contains the library LICENSE and NOTICE.
2. `rg -n "\x{2014}" dist scripts static` returns nothing. The builder fails on an em dash in shipped HTML, CSS or JS.
3. `rg -n -i "bloomberg|launchpad" dist static scripts/build.py` returns nothing.
4. `rg -n -i "yahoo|yfinance|openbb" dist static scripts functions` returns nothing. Every page's CSP `connect-src` equals main's; `script-src` is `'self'`; no external `<script src>` or font host.
5. The vendored file's sha256 matches the value recorded in `PUBLISH.md` and the npm `lightweight-charts@5.2.1` standalone production build.

Friction check (first-time visitor, no codes known, fresh browser profile, no login prompt anywhere)
6. From `/`, every listed article is reachable in at most two clicks (ledger row, or asset page then note), and by one search: typing `pearl` and pressing Enter (or tapping the first suggestion) opens the Pearl note or the PRL asset page with the note linked at the top.
7. Typing `spacex` shows matching notes if any mention it; otherwise the honest "No notes or licensed data for spacex" row and a ledger link. No error, no modal.
8. No modal, pop-up, tutorial, cookie banner or overlay appears on first load of any page. No feature requires a keyboard shortcut; every action has a visible clickable control.
9. On a 375px-wide phone viewport (touch emulation): the search bar, ledger links, chart toolbar and asset pages all work by tap; tap targets are at least 40px; no horizontal scroll at 360px; vertical page scroll works when swiping over the chart.
10. With JavaScript disabled: all pages render; notes, ledger, help, search page (full list) and asset pages are plain links; the chart area shows a short no-JS message.
11. Lighthouse (mobile) on the preview: Performance at least 90 and Accessibility at least 95 on `/` and `/s/btc/`. Home transfer excluding the chart library is at most 80 KB gzipped, and the library is not requested until the chart panel is near the viewport.
12. Every text color pair in new UI is at least 4.5:1; chart lines and candles are at least 3:1 on black (palette table in 6.3). Focus ring visible on every control.

Charts
13. `/s/btc/` shows an interactive chart with range buttons 1D, 5D, 1M, 3M, 6M, YTD, 1Y, 5Y, Max. 1D through 1Y load data; 5Y and Max are disabled and show "Needs more than 1 year of licensed history".
14. Line, Candles and Bars toggles switch series type; the legend shows the bar size (e.g. "Bars: 4 hours" on 1M).
15. A volume pane renders under price, labelled "24h volume (rolling)".
16. Hovering (mouse) or press-dragging (touch) shows a crosshair; the legend shows date and time in ET plus O, H, L, C and 24h volume for the bar under the crosshair (price only in Line mode).
17. Mouse wheel and pinch zoom; drag pans; double-click or Reset restores the default view.
18. MA 50 and MA 200 toggles draw computed lines labelled "(computed)"; on 1Y, MA 200 starts about 200 days into the series and the legend notes partial coverage.
19. Compare: adding ETH and SOL to BTC draws three series rebased to 100 at the first visible bar, with legend percent changes; max 4 extra series.
20. Log toggle switches the price scale to logarithmic and back.
21. The URL reflects state, e.g. `/s/btc/?r=1Y&t=candle&ma=50,200&cmp=ETH&log=1`; opening that URL in a new tab reproduces the chart.
22. Every chart shows "Data provided by CoinGecko" linked to coingecko.com, and the TradingView attribution link (logo on chart and NOTICE text on `/help/#credits`).
23. In the network panel, chart data requests go only to `api.coingecko.com`; repeat views within 5 minutes are served from the localStorage cache; on a 429 the chart shows the stale stamp and never draws invented points.
24. Optional codes work but are not needed: `BTC GP` opens the BTC chart at 1Y line; `BTC GIP` at 1D; `BTC GPO` with Bars; `BTC GPC` with Candles; `COMP BTC ETH` opens a compare view. `AAPL GP` shows "No licensed data for AAPL" with no network request.
25. Keyboard (optional): with the plot focused, Left and Right move the crosshair, `+` and `-` zoom, `0` resets. Tab reaches every toolbar button.

Search and pages
26. Search suggestions appear after one character, grouped Notes, Assets, Pages, Codes; arrow keys plus Enter and tap both work; Esc clears then closes; ARIA combobox and listbox roles are present.
27. Home keeps every existing panel and source line, and the home chart panel uses the new interactive component (the desk-grid layout itself is P1).
28. `/help/` lists every code with plain-English description, example and status; not-buildable items state the reason; the credits section lists every data source and the chart library notice.
29. No placeholder or sample number appears anywhere; every figure on a new page sits next to its source line.
