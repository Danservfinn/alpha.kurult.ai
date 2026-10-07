---
title: "Constellation (DAG): the snapshot fee is $2.93 a day"
date: 2026-10-06
summary: "Deep dive on Constellation (DAG). The scarce unit is one inclusion in a Hypergraph snapshot. Measured fees are $2.93 a day against a $30.6 million cap on the Oct 4 price box. Research view: avoid. Research only."
ticker: DAG
rating: "Avoid"
conviction: "Medium"
price: "$0.00777823 (CoinGecko price box, last_updated 15:31:50 ET Oct 4). Publish pull $0.0084973 at 20:44 ET Oct 6 is labeled and is not used in the ratios."
call: "Our research view at the Oct 4 price box of $0.00777823 is avoid. Horizon 12 months. Conviction medium. There is no entry."
position: "Research only. Not financial advice. No position. No compensation from Constellation Network, Inc., from a validator, or from a token holder. No token was acquired or disposed of for this research. Conflict: none known."
keys:
  - label: "Fees a day"
    value: "$2.93"
    note: "Snapshot $2.63 plus transfer $0.30. Dagscan 90 days ending 2026-10-05, at the Oct 4 price box. Formula: ($236.46 / 90) + $0.30."
  - label: "Fee per snapshot"
    value: "$0.000053"
    note: "30,400.13 DAG of snapshot fees over 4,424,056 snapshots in 90 days, at the price box."
  - label: "Issuance a day"
    value: "489,964 DAG"
    note: "Construction A. 13.9% under the CoinGecko median circulating change of 558,245 DAG a day."
  - label: "Drawdown"
    value: "98.3%"
    note: "ATH $0.451761 on 2021-08-25 to the Oct 4 price box. Not recomputed on the publish pull."
sources:
  - label: "CoinGecko public API, coins/constellation-labs price box (fetched 2026-10-04 15:33:47 ET, last_updated 15:31:50 ET). Research ratios use this print."
    url: https://api.coingecko.com/api/v3/coins/constellation-labs
  - label: "CoinGecko public API, coins/constellation-labs publish pull (fetched 2026-10-06 20:44 ET, last_updated 2026-10-06 20:44:40 ET). Labeled later tape. Not used in the fee gap, scenarios, or call."
    url: https://api.coingecko.com/api/v3/coins/constellation-labs
  - label: "CoinGecko public API, simple/price peers (fetched 2026-10-04 15:39:42 ET). Peer comparisons only."
    url: https://api.coingecko.com/api/v3/simple/price?ids=constellation-labs,iota,hedera-hashgraph,sonic-3,fantom&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true
  - label: "CoinGecko public API, market_chart days=365 constellation-labs (fetched 2026-10-04 15:39:28 ET)."
    url: https://api.coingecko.com/api/v3/coins/constellation-labs/market_chart?vs_currency=usd&days=365&interval=daily
  - label: "CoinGecko. Credit for every market chart and panel."
    url: https://www.coingecko.com
  - label: "Constellation docs, What is DAG (snapshot fees burned)."
    url: https://docs.constellationnetwork.io/network-intro/what-is-dag.md
  - label: "Constellation docs, Metanomics (emission split)."
    url: https://docs.constellationnetwork.io/network-intro/white-papers/metanomics.md
  - label: "Constellation docs, Network fees whitepaper."
    url: https://docs.constellationnetwork.io/network-intro/white-papers/network-fees-on-the-hypergraph.md
  - label: "Constellation docs, node specifications."
    url: https://docs.constellationnetwork.io/run-a-node/validator-node-guides/build-your-node/node-specifications.md
  - label: "Constellation docs, Hetzner build guide."
    url: https://docs.constellationnetwork.io/run-a-node/validator-node-guides/build-your-node/cloud-provider-specific/build-hetzner-server.md
  - label: "Constellation docs, delegation rewards (3%, 45%, 21-day unwind)."
    url: https://docs.constellationnetwork.io/network-intro/dag-delegation/managing-delegated-positions/delegation-rewards.md
  - label: "Ben Jorgensen, Focusing everything on AI, 2026-09-29."
    url: https://constellationnetwork.io/blog/focusing-everything-on-ai
  - label: "Alex Brandes, Streamlining Constellation Network, 2026-09-29."
    url: https://constellationnetwork.io/blog/streamlining-constellation-network
  - label: "L0 cluster info (123 listed, 119 Ready, fetched 2026-10-04 15:39:27 ET)."
    url: https://l0-lb-mainnet.constellationnetwork.io/cluster/info
  - label: "L0 total supply (fetched 2026-10-04 15:39:26 ET)."
    url: https://l0-lb-mainnet.constellationnetwork.io/dag/total-supply
  - label: "Dagscan staking stats (fetched 2026-10-04 15:39:13 ET)."
    url: https://api.dagscan.io/stats/staking
  - label: "Dagscan nodes uptime (fetched 2026-10-04 15:39:16 ET)."
    url: https://api.dagscan.io/nodes/uptime?sort=stake&limit=200
  - label: "Block explorer transfer sample (fetched 2026-10-04 15:39:24 ET)."
    url: https://be-mainnet.constellationnetwork.io/transactions?limit=20
  - label: "cloud-mercato, Hetzner CPX51 list price (fetched 2026-10-04 about 17:03 ET)."
    url: https://pcr.cloud-mercato.com/providers/hetzner/flavors/cpx51
  - label: "cloud-mercato, Hetzner CPX41 list price (fetched 2026-10-04 about 17:03 ET)."
    url: https://pcr.cloud-mercato.com/providers/hetzner/flavors/cpx41
  - label: "Frankfurter EURUSD, rate date 2026-10-02, 1.1225."
    url: https://api.frankfurter.app/latest?from=EUR&to=USD
  - label: "USAspending award FA864921P1550 (fetched 2026-10-04 15:49:37 ET)."
    url: https://api.usaspending.gov/api/v2/awards/CONT_AWD_FA864921P1550_9700_-NONE-_-NONE-/
  - label: "USAspending award W912CH24CL012 (fetched 2026-10-04 15:46:46 ET)."
    url: https://api.usaspending.gov/api/v2/awards/CONT_AWD_W912CH24CL012_9700_-NONE-_-NONE-/
  - label: "USAspending spending_by_award search that returned the three UEI awards, including W911S222P1470 (fetched 2026-10-04 15:46:44 ET)."
    url: https://api.usaspending.gov/api/v2/search/spending_by_award/
  - label: "Justia docket, Morgan et al. v. Constellation Network, Inc. et al., N.D. Cal. 4:21-cv-08869. curl 403 at 21:14:17 ET. Disposition read from the saved page extract 21:16 to 21:21 ET. Status and allegations only. No amount."
    url: https://dockets.justia.com/docket/california/candce/4:2021cv08869/387981
  - label: "Complaint PDF, Morgan et al. v. Constellation Network, Inc. et al., HTTP 200 at 21:14 ET, 55 pages. Allegations and a prayer for restitution, not findings. No amount is used from this file."
    url: https://scott-scott.com/wp-content/uploads/2022/08/2021-11-16-1-COMPLAINT-against-Altif-Brown-Constellation-Network-Inc-Benjamin-Diggles-Mathias-Goldmann-Main-Document.pdf
  - label: "IOTA system state and closed epochs (fetched 2026-10-04 18:51:34 to 18:51:37 ET)."
    url: https://api.stardust-mainnet.iotaledger.net/api/core/v2/info
  - label: "Hedera mirror node, fees endpoint inspected and not used as the dollar figure (2026-10-04 18:51:33 ET)."
    url: https://mainnet-public.mirrornode.hedera.com/api/v1/network/fees
  - label: "Sonic explorer chart pages (transactions 18:51:52 ET, fees 18:56:03 ET). The deprecated V1 daily-tx API returned NOTOK and was not the figure."
    url: https://sonicscan.org/chart/tx
  - label: "GitHub, Constellation-Labs/constellation, repo created 2017-12-05. A repo timestamp, not a shipping record."
    url: https://github.com/Constellation-Labs/constellation
  - label: "PacaSwap sheet linked by the venue. HTML view had no table rows. Blocker, not a reconciled payout."
    url: https://docs.google.com/spreadsheets/d/17bJ6Ip7vJLgBDqhe52GQRMc6y0yqaLmdnHhrJqSCLG8/
  - label: "ip-api.com legal terms. Country counts in this note come from the graded Oct 4 batch. Orda should read this page before ship. Not a clearance."
    url: https://ip-api.com/docs/legal
---

Research only. Not financial advice. All times are ET (UTC-4). **Labeling rule for this note:** every fee, issuance, node, and cap figure in the research body is the graded Oct 4 bundle. The price box is CoinGecko coins/constellation-labs, last_updated 15:31:50 ET on 2026-10-04, fetched 15:33:47 ET. A later peer pull at 15:39:42 ET is used only for peer comparisons and is labeled when used. The Oct 6 publish pull is a later tape. It is not mixed into the fee gap, the scenarios, or the call. **Charts:** market charts use the Oct 4 CoinGecko series. Operating charts use Dagscan, the L0 cluster, and the peer explorers named in the captions. Chart 17 from the bundle is internal and is not published. No CoinGecko raw JSON and no CSV is committed with this note. Morgan et al. v. Constellation Network is allegations and docket status only. No amount from that case is stated.

**Price line (research box, the print the call uses):** DAG $0.00777823. Market cap $30,588,422. 24h volume $512,900. Circulating supply 3,932,917,287. Max supply null, so fully diluted value is not defined. All-time high $0.451761 on 2021-08-25, drawdown 98.3%. All-time low $0.00110189 on 2019-03-08. Rank on that search pull: 708. [Data provided by CoinGecko](https://www.coingecko.com).

**Publish pull (not used in the ratios):** CoinGecko coins/constellation-labs, fetched 2026-10-06 20:44 ET, last_updated 2026-10-06 20:44:40 ET. Price $0.0084973. Market cap $33,429,679. 24h volume $652,332. Circulating supply field 3,934,151,121.8136578. Max supply null. Rank 659. CoinGecko percentage fields: 24h +10.55169%, 7d +15.97924%, 30d +24.02094%, 1y -69.30946%. ATH and ATL dates match the research box. These prints are not substituted into the $2.93 fee day, the 1,145x gap, or the scenario paths. [Data provided by CoinGecko](https://www.coingecko.com).

## The call in one paragraph

Constellation charges applications, not end users, to record data in a global snapshot. That is a real product shape. The tape does not show the product earning. Measured fees are $2.93 a day, $1,068 a year, against a $30.6 million cap on the Oct 4 price box. A bottom-up reading of the published emission split plus the saved 90-day delegator yield implies about 489,964 new DAG a day. The observed CoinGecko circulating change has a median of 558,245 DAG a day. Those two prints are 13.9% apart, inside the 15% band. Fees do not pay the servers. New coins do. The October 15 cut to 30 validators, chosen each quarter by delegation ranking, shrinks the set that shares the validator slice. It does not create a fee stream. Conviction is medium because the fee gap is measured and does not depend on the dilution estimate. It is not high because an unratified emission vote can cut issuance, and because a fee step-up is a dated possibility, not a measured one. No entry price. There is no entry. Our research view is **avoid**.

## What Constellation is

Constellation records one scarce thing: a slot in the global snapshot that records other applications' data. People sending the token to each other usually pay nothing. Applications pay the token to be recorded. The network is about to shrink who may write those snapshots and rewrite who receives newly minted tokens.

Metaphor: a toll booth on a road where most cars pass free. The booth burns the coins it collects. The market is pricing the road like a bridge. The metaphor breaks where the operator's pay comes from new coins, not from the toll.

Memorable number, before any other figure: $2.93 a day of measured fees, $1,068 a year, against a $30.6 million market cap.

The native asset is CoinGecko id constellation-labs, symbol DAG, name Constellation. The platforms object on the Oct 4 coin pull is empty. No contract address on the native coin. wrapped-dag (WDAG), Ethereum contract 0x2e3cfe45e3ee7c017277f22e35d2f29edc99d570, also has a Base address. That listing is separate. Its cap is not added to the native cap. Its price was $0.00780055 at its fetch. Search hits that are not this asset, and are not used: blockdag (BDAG), dagger (XDAG), hoodagent, dagora (DADA), kdag, dagama-world, and several Constellation Energy stock tokens. Anagram's "Constellation" SIMD note is a Solana proposal, not this network.

![Diagram of a snapshot slot, a burned toll, and new coins paying the operator](/assets/2026-10-06-constellation/07-how-it-works.svg "How the snapshot slot works. Sources: Constellation docs, what-is-dag and metanomics, saved 2026-10-04. Simplified schematic from the graded bundle. Not a market chart.")

![Diagram of fees burned and new coins paying operators](/assets/2026-10-06-constellation/08-money-cascade.svg "Money cascade. Snapshot fees are burned. Operators are paid in new DAG. Sources: Dagscan 90-day fees, 2026-10-04 15:39 ET; Metanomics split; CoinGecko price box. [Data provided by CoinGecko](https://www.coingecko.com/).")

## First principles: the snapshot slot

The scarce unit is one inclusion in a Hypergraph snapshot. The metric that values it is the DAG fee paid per snapshot, which is $0.000053 at the price box (30,400.13 DAG of snapshot fees over 4,424,056 snapshots in 90 days). A validator seat is not the unit being sold. It is the right to write snapshots. That right is capped by a rule, not by physics. Every later section comes back to fee per snapshot, or to the daily sum of those fees.

Unit line: one snapshot inclusion is worth $0.000053 today.

### What one unit earns

Snapshot fees, 90 days ending 2026-10-05, Dagscan, fetched 15:39 ET: 30,400.13 DAG. At the price box that is $236.46, or $2.63 a day. Docs say snapshot fees are burned. Burn is a supply reduction, not cash to a validator.

Transfer fees, same window: 3,463.75 DAG, $0.30 a day. A sample of 20 recent explorer transfers (15:39 ET) is not uniformly free: 10 fees are 0, 5 are 1 datum, 5 are 1,000,000 datum (0.01 DAG). Destination of transfer fees is not documented as a burn. Combined measured fees: $2.93 a day, $1,068.24 a year.

Revenue, profit, and cash are different things here. Fee revenue to operators is about zero if snapshot fees are burned. Profit for a node is emission received minus hosting. Cash is that profit only if the operator converts the new coins to cash. Lifetime emission is not lifetime profit, and it is not external revenue.

### What one node costs

Node spec: 8 vCPU, 16 GB RAM, 320 GB SSD. The operator guide names Hetzner CPX51 as recommended and says CPX41 may suffice but can run out of disk.

Saved prices, cloud-mercato public catalog, fetched 2026-10-04 about 17:10 ET, "Pricing in EUR":

- CPX41 (8 vCPU, 16 GB), Falkenstein and Helsinki: EUR 32 a month. Disk on that SKU is short of the 320 GB spec, so this is the low end, not the base.
- CPX51 (the recommended SKU), Falkenstein, Helsinki, and Nuremberg: EUR 71 a month. Ashburn and Hillsboro: EUR 238 a month.

EURUSD 1.1225, Frankfurter, rate date 2026-10-02. Not a token price.

- Base hosting: EUR 71 x 1.1225 = $79.70 a month, $956 a year. This is the Germany and Finland price. 74 of 78 Hetzner nodes sit in those two countries.
- Low: EUR 32 x 1.1225 = $35.92 a month.
- High: EUR 238 x 1.1225 = $267.16 a month.

$79.70 is the saved price, not a round number picked first.

Bill for 119 Ready nodes at the base price: $113,808 a year. Bill for the announced set of 30: $28,691 a year. Fees of $1,068 cover 0.9% of the 119-node bill and 3.7% of the 30-node bill. Fees would have to rise 26.9x to cover 30 nodes, or 106.5x to cover 119. That is hosting cover, not a valuation.

### What one node and one delegator are paid

Published split, Metanomics: of variable emissions, Protocol 30%, Stardust Collective (the Foundation) 5%, Validators 20%, Delegators 45%. Separately, delegators receive a fixed 3% a year on delegated DAG. Operational docs say the same 3% and the same 45%, and a 21-day unbonding. Metanomics text says 30 days to unwind. The live rule used here is 21 days. The 30-day line is the design page, and the two sources disagree.

Saved Dagscan print, fetched 15:39 ET:

- Delegated: 941,247,501 DAG
- Locked: 1,005,466,395 DAG
- Accrued rewards, not yet in the spendable balance: 116,690,942 DAG
- Delegator APY: 11.36% over 7 days, 9.06% over 30, 10.2% over 90, 11.13% over 180, 11.8% over 365

Construction A, the one used below. Treat the 10.2% 90-day APY as the sum of the fixed 3% and the variable delegator share, which is what the docs say a delegator receives.

- Fixed 3% on delegated DAG: 77,363 DAG a day
- Delegator rewards at 10.2%: 263,034 DAG a day
- Variable emissions implied by the delegator slice (45%): 412,602 DAG a day
- Total issuance: 489,964 DAG a day

Of that variable bucket, per day: Protocol 123,781 DAG ($963), Foundation 20,630 DAG ($160), Validators 82,520 DAG ($642), with the delegator total already stated. The protocol's emission take is about 329 times daily fees.

How the 20% validator bucket is split across nodes is not in the saved docs. Two labeled assumptions:

- Even split across 119 Ready nodes: $1,969 a year per node, $5.39 a day. Hosting is $2.62 a day at the base price, so the even split covers the server and leaves about $2.77 a day. Fees add about $0.025 a day. ASSUMPTION, range is the delegation-weighted case below.
- Even split across the announced 30: $7,809 a year per node.

Delegation-weighted is the more honest reading if validator pay follows stake. The cutoff to be inside a 30-seat ranking is 1,958,920 delegated DAG. A node at that bar is 0.21% of delegated stake. Its share of the $642 a day validator pool is about $1.34 a day, which does not cover $2.62 of hosting. The largest named node (DOR Node 1, about 141.5 million delegated, 15% of the pool) would take about $96 a day if the same rule holds. Small nodes lose cash. Large nodes collect the emission. Fees change neither result.

A delegator of 1,000,000 DAG at 10.2% receives 102,000 DAG a year, $793 at the price box, before the validator commission of 5% to 10% (docs). That is yield, not a claim on fees. Unbonding to spend it is 21 days, and rewards are not separately claimable.

### Reconciliation

Observed CoinGecko circulating change, median of the last 100 daily steps: 558,245 DAG a day. Construction A is 13.9% below that. Inside the 15% band. Dropping the single +839 million step does not move the median (558,165). Construction B, which treats the 10.2% as variable-only and stacks the fixed 3% on top, implies 661,882 DAG a day, 15.7% above the median, just outside the band. B is reported and not used. A is used because the docs say the quoted yield includes both pieces.

The accrued-reward stock (116.7 million DAG, 12.4% of delegated) is a balance, not a daily rate. It is consistent with rewards that have not been undelegated. It is not a second emission print.

### Cost to attack

There is no hash contest. The announced rule ranks qualifying nodes by delegated DAG and seats the top 30. To match the current cutoff on one seat costs 1,958,920 DAG, $15,237 at the price box. A majority of 16 seats at that bar costs 31.3 million DAG, $243,791. Add 16 million DAG of wallet-hold qualification if the 1,000,000 DAG wallet rule is extra rather than part of the delegation, and the bill is about $368,000. ASSUMPTION on whether the wallet hold counts twice. Either figure is under 1.3% of the cap. The fee security budget is $1,068 a year. The emission security budget is the issuance itself, about $3,811 a day, paid by holders.

### Metagraph launch and run

The saved docs do not state one DAG figure as the cost to launch a metagraph. Hypergraph collateral in the docs is still 250,000 DAG a node ($1,945). The October 15 announcement raises the qualifying wallet hold to 1,000,000 DAG ($7,778). A three-node metagraph on the recommended SKU costs about $239 a month in hosting before collateral. Measured run cost on the global layer is the snapshot fee: $0.000053 per snapshot, $2.63 a day across every metagraph the indexer tracks. DAGDaily's 750,000 DAG table-stakes line is not the live rule.

### Sensitivity

The two inputs that move validator cash the most are the delegator APY (it sets the emission total) and the hosting price. The base cell is the only one used in the call. Fees are not in the grid because they do not move the result inside any cell.

| APY (saved window) | Hosting a month | Cash per Ready node, even split | Cash per node in a set of 30 |
|---|---|---|---|
| 9.06% (30-day) | $35.92 | positive, smaller than base | positive |
| 10.2% (90-day, base) | $79.70 | about $1,012 a year | about $6,853 a year |
| 11.8% (365-day) | $267.16 | negative at the US price | near flat to negative |

Unit line: $2.93 a day of fees does not pay a $79.70 server, and the coins that do are new supply.

![Cost per day against hosting](/assets/2026-10-06-constellation/09-cost-per-day.svg "Cost per day. Legend above the axes. Fees $2.93. Base hosting $79.70 a month. Sources: Dagscan fees 15:39 ET; cloud-mercato CPX51; Frankfurter EURUSD 1.1225, rate date 2026-10-02; CoinGecko price box. [Data provided by CoinGecko](https://www.coingecko.com/).")

![Cost per snapshot on a log scale](/assets/2026-10-06-constellation/18-cost-per-snapshot.svg "Cost per snapshot. The hollow bar is the price-implied fee, an unproven level, not a result. Measured fee $0.000053. Sources: Dagscan 90-day snapshot fees; CoinGecko price box, fetched 15:33 to 15:39 ET. [Data provided by CoinGecko](https://www.coingecko.com/).")

![Fees against the issuance proxy](/assets/2026-10-06-constellation/04-fees-vs-issuance-proxy.svg "Fees against the issuance proxy. $2.93 a day of fees versus construction A at 489,964 DAG a day. Sources: Dagscan; CoinGecko circulating series. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Why the pivot does not show on the tape

FACT. Ben Jorgensen, CEO, 2026-09-29: "We are focusing the entire network on AI, and on the work our infrastructure was built to do: AI auditability, governance, and crowdsourced compute and inference."

FACT. Alex Brandes, CTO, same day: "The network records each unit of work and pays each operator in DAG. Gate is the first customer, and every request it sends to an operator is paid for by a Gate user." The post names no DAG rate, no dollar rate, and no start date.

FACT. Emission recipients, Metanomics split applied to construction A: the protocol receives about $963 a day of new coins, against $2.93 a day of measured fees. The foundation receives about $160 a day. Validators and delegators receive the rest. The September 29 post says a new schedule will be ratified with the Stardust Collective, with reduced inflation as a goal. Holders are not named as the voters.

INFERENCE. Token holders do not vote on the emission rules. The cited mechanism is the Stardust Collective, which Metanomics calls the Foundation. That is a reading of who is in the room, not a statute that says holders may not vote.

Where the quote and the recipients disagree: the stated objective is fees for real inference work. The recipients show that today the protocol is paid by issuance, about 329 times the fee tape. They are doing the inference pivot because it is supposed to raise fee per snapshot by replacing emission with customer payments. The tape does not show that yet.

Less flattering explanation: the government-partnership story and the AI story are narrative support for a token whose measured demand is $2.93 a day. Closing the exchange, the testnets, and the consumer frontend cuts cost and cuts a surface that was exploited on September 9. That can be operational discipline. It can also be a retreat from products that did not produce fees, told as a focus. Both can be true. The fee tape does not distinguish them.

Unit line: the pivot raises fee per snapshot only if Gate payments land on the snapshot tape. They have not.

## Flywheel

| Arrow | Mechanism in five words | Metric | Latest value | Trend |
|---|---|---|---|---|
| Apps pay to be recorded | Metagraphs pay snapshot fees | Snapshot fees a day | $2.63, Dagscan 90-day, 15:39 ET | Flat. 30-day week is 2,065 DAG, close to the 90-day week of 2,364 DAG |
| Fees reduce supply | Snapshot fees are burned | Burned snapshot fees, 90 days | $236 | Too small to offset issuance |
| New coins pay operators | Emission split, construction A | Issuance a day | 489,964 DAG, $3,811 | Median circulating change 558,245, same direction |
| Stake picks the writers | Quarterly delegation ranking | Top 5 share of delegated | 50.05% | Concentrated. Cut to 30 not live |
| Recorded work attracts more apps | More metagraphs, more fees | Metagraphs submitting | 12 in 90 days, 7 in 30, 17 tracked | Not rising on the fee tape |

Binding link: snapshot fees a day. It is not turning. Evidence: $2.63 a day, no step-up in the saved 90-day file, and the company post names Gate without a rate.

What someone outside can squeeze:

- Hetzner. 78 of 123 listed nodes, 63.4%, geolocated via ip-api.com. A host policy or a price change hits most of the live set. Germany and Finland hold 74 of those 78. Country counts are flagged for an Orda terms read before ship. See the gaps section.
- Exchanges. KuCoin is 39.2% of the Oct 4 coin-object volume. No Binance or Coinbase ticker in the saved object. A halt at Kraken ($88,543 of the $512,900) is the US-regulated venue risk.
- Gate. Named as the first inference customer. No fee series. A single named customer is a squeeze, not a moat.
- Government customers. Three DoD awards to the San Francisco UEI, none paying in DAG. A procurement officer can end the relationship. It is not token demand today.

Unit line: the loop stops at $2.93 a day, and the host, the venues, and the named customer sit outside the loop.

![Flywheel with the fee link not turning](/assets/2026-10-06-constellation/10-flywheel.svg "Flywheel. Binding link is snapshot fees a day, $2.63, not turning. Sources: Dagscan 15:39 ET; company posts 2026-09-29. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Market structure

All market figures in this section are the Oct 4 CoinGecko pulls unless the sentence says publish pull. [Data provided by CoinGecko](https://www.coingecko.com).

From the saved 365-day daily series, aligned with Bitcoin:

- DAG annualized volatility: 180%
- Correlation of daily log returns with Bitcoin: 0.15
- DAG return over the saved year: -71.8%
- Bitcoin return over the same dates: -29.9%
- Fully diluted value: not defined. Max supply is null
- Depth: not in the coin object. Bid-ask spreads are present (KuCoin 0.98%, Kraken USD 3.36%, CoinW 24.8%). Spreads are not depth. Blocker for a book

Venue concentration, Oct 4 coin-object tickers, which sum to about the $512,900 volume: KuCoin $201,257 (39.2%), Kraken USD $88,543, MEXC $62,980, Gate $44,950. No Binance. No Coinbase.

Publish-pull tickers, 2026-10-06 20:44 ET, converted volume, not rolled into the 39.2% figure: KuCoin USDT $305,893, Kraken USD $67,783, Gate USDT $60,881, MEXC USDT $60,593, CoinW USDT $41,928, Biconomy.com USDT $32,123, Ourbit USDT $30,500, BingX USDT $26,062, XT.COM USDT $25,226, Kraken EUR $1,343.06. Same venue names. No Binance. No Coinbase. Trust scores on that pull were null. Spreads on that pull: KuCoin 0.831771%, Kraken USD 1.477088%, Gate 0.930774%, MEXC 0.329451%, CoinW 0.622285%, Biconomy.com 0.106132%, Ourbit 0.641774%, BingX 0.193285%, XT.COM 43.49073%, Kraken EUR 5.157775%. Spreads are not depth.

A later peer pull at 15:39:42 ET on Oct 4 prints DAG at $0.00751124 and a $29.56 million cap. That pull is used only for peer comparisons.

Unit line: the market that prices $2.93 a day of fees at $30.6 million traded $512,900 in a day, and it did not track Bitcoin closely.

![Indexed price versus peers](/assets/2026-10-06-constellation/01-price-vs-peers.svg "Price versus peers, indexed, Oct 4 CoinGecko daily series. Research drawing, not the Oct 6 publish pull. [Data provided by CoinGecko](https://www.coingecko.com/).")

![Price versus use](/assets/2026-10-06-constellation/05-price-vs-use.svg "Price versus use. Correlation of daily transfer counts with price over 90 days is 0.03. Sources: Dagscan transfers; CoinGecko price. [Data provided by CoinGecko](https://www.coingecko.com/).")

## On-chain picture and supply

Denominator stated each time. Dagscan is one indexer. Cluster and supply endpoints are the network's own.

- L0 total supply: 3,932,958,977 DAG (15:39:26 ET). CoinGecko circulating is 41,690 DAG lower.
- Dagscan wallet total 4,020.8 million is not a second supply and is not wrapped balances. The file's own fields add up: balance 2,898.7 million + locked 1,005.5 million + accrued 116.7 million. Accrued rewards are unminted or unpaid, depending on the indexer. They are not coins in addition to L0 supply.
- Top 10 wallets: 29.1% of the Dagscan total. Top 100: 40.9%. Largest: 524,084,295 DAG, unlabeled, 13.3% of L0 supply.
- Delegation: 941 million, 23.9% of L0. Locked: 1,005 million, 25.6%. Five nodes hold 50.05% of delegated. One is labeled CEO Ben Jorgensen.
- Nodes: 123 listed, 119 Ready, 2 SessionStarted, 1 WaitingForDownload, 1 DownloadInProgress. Directory 287, staked 151, indexer-eligible 125, minHoldingsEnforced false.
- Transfers a day: 301 (27,115 over 90 days). Fees as in the unit section. Active addresses: not in the saved stats files. Blocker, not a guess.
- Exchange-labeled wallet in the top set: MEXC, 105 million DAG. A treasury label of 21.9 million exists in the wallet file. The 524 million wallet is unlabeled.

The +839 million step. In the saved 365-day CoinGecko series the daily circulating series (cap divided by price) jumps by 839,185,032 DAG on the point dated 2025-10-28 ET, which is 2025-10-29 UTC. From about 2.87 billion to 3.71 billion in one day. A 10% yield is about 0.027% a day. A one-day 29% jump is a restatement, not a mint. The full saved year goes from 2.87 billion to 3.94 billion, +37%. About 79% of that year-increase is the one step. The median daily change, which ignores the step by construction, is the usable issuance proxy: 558,245 DAG a day.

Forward, using construction A at 489,964 DAG a day, from the L0 print:

- 3 months (91 days): 3.978 billion DAG. At a constant $30,588,422 cap, implied price $0.00769.
- 12 months: 4.112 billion DAG. Implied price $0.00744.

Daily issuance in dollars: 489,964 x $0.00777823 = $3,811, which is 0.74% of the $512,900 daily volume. Fees are about 6 millionths of that volume. Dilution is visible on the tape. It is not a volume event.

No unlock calendar was found. The supply chart is the circulating path, not a vest schedule. Max supply null means there is no cap to unlock into.

Unit line: even if issuance matches construction A, constant-cap dilution over 12 months is about 4% of the price. The fee gap is the other 1,145x. Do not confuse them.

![Holder concentration](/assets/2026-10-06-constellation/02-holder-concentration.svg "Holder concentration. Top 10 are 29.1% of the Dagscan total. Largest wallet 524,084,295 DAG, unlabeled. Source: Dagscan wallets, 2026-10-04 15:39 ET.")

![Delegation concentration](/assets/2026-10-06-constellation/03-delegation-concentration.svg "Delegation concentration. Top 5 nodes hold 50.05% of 941,247,501 delegated DAG. Source: Dagscan, 2026-10-04 15:39 ET.")

![Circulating path, not a vest schedule](/assets/2026-10-06-constellation/16-supply-calendar.svg "Circulating path. The +839,185,032 step on 2025-10-28 ET is a restatement, not a mint. Forward path uses construction A. Source: CoinGecko daily series, fetched 2026-10-04. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Competitive gap

Demonstrated for DAG, fetched 15:39 ET unless noted: 301 transfers a day, $2.93 of fees a day, 119 Ready nodes of 123 listed. DAG has no saved 12-month operating series. The 90-day fee file has no step-up, so DAG's demonstrated growth is not distinguishable from zero. Years for DAG to reach a peer at its own rate is not a finite number: gap divided by about zero.

Peers are from their own explorers. Cap multiples from the 15:39 pull are not this table. They remain below as price-path context only. [Data provided by CoinGecko](https://www.coingecko.com).

| Name | Transactions a day | Fees a day | Nodes | 12-month growth | Years arithmetic |
|---|---|---|---|---|---|
| DAG | 301 | $2.93 | 119 Ready of 123 | not in a 12-month series | not finite |
| IOTA | 1,993,800 | $11.51 | 63 listed, 62 with voting power, cap 150 | transactions +6.10%, gas fees +209.6% in IOTA | widening. 17.35 years, which rounds to 17.4, to add another gap of this size |
| Sonic | 89,952 on Sat 2026-10-03, a labelled point, not the mean | $19.91 that day | 37 active of 55 IDs | 30-day mean transactions -37.42%, fees in S +2.48%. 7-day sensitivity: transactions -57.51%, fees -46.88% | 1.67 years on the 30-day mean. The 0.50 year figure used the Saturday point and is withdrawn |
| Hedera | 477,279 including duplicates; 328,332 like-for-like | $409.63. Duplicate rows charged 0 | 30, none deleted | like-for-like transactions -43.3%. Inclusive count -17.57%. Fee dollars -46.84%, unchanged by the zero-fee duplicates | 1.31 years on the like-for-like count. 4.69 years if the duplicates are counted |

IOTA. Last closed epoch is 516. Epoch length is 86,400,000 ms, so one epoch is one day. Epoch 517 was open and its totals were null, so it is not used. Epoch 516: 1,993,800 transactions and 193.568 IOTA of gas. Epoch 152 is 364 epochs earlier (516 minus 152), not 365: 1,879,247 transactions and 62.513 IOTA. Dollar fees use the saved CoinGecko IOTA price $0.059458 at 15:39:42 ET: $11.51 now, $3.72 a year earlier at the same price. Validators: 63 in activeValidators, 62 with voting power above zero, maxValidatorCount 150. Fetched 18:51:34 to 18:51:37 ET.

Growth arithmetic: (1,993,800 - 1,879,247) / 1,879,247 = 6.10%. Increase in the daily rate: 114,553 / 364 = 314.7 transactions a day, per day. Gap above DAG: 1,993,800 - 301 = 1,993,499. Time for IOTA to add another gap of that size: 1,993,499 / (114,553 / 364) / 365 = 17.35 years, which rounds to 17.4. That is not a catch-up time. IOTA is moving away. Multiple: 6,624x on transactions, 3.93x on fee dollars.

Sonic. Official explorer chart, 671 daily points. Transactions page fetched 18:51:52 ET. Fee page fetched 18:56:03 ET. Last complete day is Saturday, October 3, 2026, a labelled point, not the growth line: 89,952 transactions and 490.315 S. That Saturday is the lowest of the last 10 transaction points, about half of Friday's 183,612. The point 365 rows earlier, Friday, October 3, 2025: 269,242 transactions and 1,009.05 S. The fee unit is S. The saved page meta description says the chart shows the historical total number of S paid as transaction fee. The last 30 points sum to 44,577.06 S. That sum is not cited as a figure the explorer prints. Dollar conversion of the Saturday point uses the saved CoinGecko Sonic price $0.04060592: $19.91. The year-earlier point is $40.97 at the same price.

Growth uses 30-day means from the same saved chart, ending 2026-10-03 and 2025-10-03. Transaction means: 178,980 versus 286,008, which is -37.42%. Fee means: 1,485.90 S versus 1,449.88 S, which is +2.48%. Fees are not shrinking on this line. Decline in the transaction mean: 107,028 over 365 days, 293.23 a day. Days for the mean to reach 301: (178,980 - 301) / 293.23 = 609.4 days, 1.67 years. Because the fee mean rose, there is no fee decline to extend. If the fee mean keeps the same daily change, the fee on that day is 1,546 S, $62.78, which is 21.4x DAG's $2.93 (62.78 / 2.93). Meeting on transaction count would not be a fee collapse. Seven-day means are a sensitivity, not the line: transactions -57.51% (132,099 versus 310,893) and fees -46.88% (651.36 S versus 1,226.23 S). This is arithmetic on a saved line, not a forecast. Validators: 37 of 55 active.

Hedera. The mirror node has no daily total. Live window, pages starting 18:56:35 ET: 1,772 transactions in 320.78 seconds from 18:51:14 ET, which is 477,279 a day. Of those 1,772 rows, 553 (31.2%) have result DUPLICATE_TRANSACTION and charged fee 0. Excluding them, the rate is 328,332 a day. The year-ago window has 2 of 4,000 such rows, not zero. Charged fees in the live window, 1,472,940,989 tinybars, at the network exchange rate of $0.103251 per HBAR (cent_equivalent 309,753 / hbar_equivalent 30,000 / 100, fetched 18:51:32 ET), are $409.63 a day. CoinGecko's saved HBAR price was $0.103993, 0.72% higher, and is not used in this dollar figure. Year-ago inclusive rate: 579,016 a day. Same today's exchange rate: $770.54 a day. Like-for-like: (328,332 - 579,016) / 579,016 = -43.3%. Years for that count to reach 301 if the straight line continues: 1.31. The two windows are about 5 minutes and 10 minutes, not a 365-day fit. The arithmetic is real. The trend is not as solid as Sonic's chart or IOTA's closed epochs. Multiple on the inclusive count: 1,586x on transactions, 140x on fee dollars. On the like-for-like count the transaction multiple is 1,091x (328,332 / 301). Nodes: 30, none deleted.

Substitutes. A cloud database and a private ledger do the job of "record this and show it later" without a token. Their unit price was not in a saved price list, so it is unobservable here. The comparison that is observed: DAG charges $0.000053 per snapshot and burns it. IOTA's last closed day took in $11.51 of gas. Sonic took in $19.91 on the Saturday point. Hedera took in $409.63 on the short census. A substitute still does not need the DAG token to clear.

What would close it fastest: snapshot fees rising to the 30-node hosting bill, $28,691 a year, which is 26.9x, and then toward the price-implied fee in the section below. Early sign: a 7-day snapshot-fee print above 50,000 DAG on the indexer, confirmed on the official explorer. That signpost is 21 times the 90-day average week of 2,364 DAG, not 12 times and not 5 times. The older 12x line is withdrawn.

Unit line: peers process more. Sonic's transaction count is down on the 30-day mean and its fees are not. Hedera's like-for-like count is down. DAG's fee day is still $2.93.

![Operating gap versus IOTA, Sonic, and Hedera](/assets/2026-10-06-constellation/11-competitive-gap.svg "Competitive gap on operating points, not market cap. DAG $2.93 a day. IOTA $11.51. Sonic Saturday point $19.91, fees not shrinking on the 30-day mean. Hedera $409.63. Sources: peer explorers, 2026-10-04 18:51 to 18:57 ET; CoinGecko peer prices at 15:39:42 ET for IOTA and Sonic dollar legs. Hedera dollars use the mirror-node exchange rate. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Geopolitics, venues, and the 2021 case

| Item | Fact | Rating |
|---|---|---|
| Company jurisdiction | Constellation Network, Inc., San Francisco, UEI HH64FJ1EB5S7, on the USAspending awards | Headwind. A US company with a token and a permissioned-style seat rule faces securities and sanctions questions it has not cleared in any saved record |
| Foundation | Stardust Collective, called the Foundation in Metanomics. Jurisdiction not in the saved docs | Headwind. The body that votes the emission schedule is not located in the saved files |
| Validator geography | All 123 listed: Germany 52, United States 33, Finland 32, and 6 elsewhere. ip-api.com, 15:39 ET | Headwind. Two countries and one host dominate. Not a seizure-proof set. Terms flag in the gaps section |
| Hetzner scope | Of 78 Hetzner nodes: Germany 43, Finland 31, United States 5 | Headwind. EU hosting concentration, separate from the all-node country totals |
| Exchange access | Tickers in the Oct 4 coin object: KuCoin, Kraken, MEXC, Gate, CoinW, BingX, Biconomy, Ourbit, XT. No Binance, no Coinbase | Headwind. US access is Kraken in this list. Delisting risk is real and unmeasured beyond the ticker list |
| Securities status | No SEC or CFTC order was fetched. The 1,000,000 DAG qualification and the allowlist history are the facts a regulator would read | Headwind, unadjudicated. Not a finding that it is a security |
| Sanctions | No OFAC designation fetched for the company or the token | Not rated. Absence of a search hit is not a clearance |
| Government as customer | Three DoD awards, below. None pay in DAG. The blockchain-described one ended in 2022 | Neutral to mild tailwind for the company, not for the token. A past purchase order is not token demand |
| ICO-era lawsuit | Morgan et al. v. Constellation Network, Inc. et al., N.D. Cal. No. 4:21-cv-08869, filed Nov 16, 2021. ERC-20 DAG holders alleging exclusion from the swap to mainnet DAG. Tentative settlement noticed Jan 9, 2023. Dismissed by stipulation Jul 14, 2023. Terminated Jul 17, 2023. Settlement terms not on the docket text. No class certified | Resolved legacy headwind. A governance and disclosure signal. Not a live case, and not token demand |

SAM.gov entity API returned 404. The SAM search HTML did not contain the UEI. SBIR.gov keyword search for "Constellation Network" returned unrelated balloon awards, not this company. AFWERX search HTML contained the query and no award body. Those three are recorded blockers, not evidence of no award. The awards themselves are on USAspending. A highergov reprint of FA864921P1550 calls it an SBIR Phase II (topic AF211-DCSO1). That classification is from the reprint, not from a sbir.gov award page.

Morgan et al. v. Constellation Network, Inc. et al., N.D. Cal. No. 4:21-cv-08869, filed Nov 16, 2021. ERC-20 DAG holders alleging exclusion from the swap to mainnet DAG. Tentative settlement noticed Jan 9, 2023. Dismissed by stipulation Jul 14, 2023. Terminated Jul 17, 2023. Settlement terms not public. No class certified. Docket: https://dockets.justia.com/docket/california/candce/4:2021cv08869/387981. Complaint: the plaintiffs' counsel PDF, fetched 21:14 ET (HTTP 200, 55 pages). curl of the Justia URL at 21:14:17 ET was HTTP 403. The live docket text was read through a page extract at 21:16 to 21:21 ET. An archive.org copy of the same URL, snapshot 20230319233210, was fetched 21:17 ET. Justia says that docket text was last retrieved July 17, 2023, and that a later listing may be on PACER. PACER was not fetched. No dollar amount appears in the saved docket rows or in this note. The complaint's running header prints Case 3:21-cv-08869. That is the same matter. A CourtListener search of 3:21-cv-08869 without a district filter returned a D.N.J. case, not this one. classaction.org remains a derivative news page and is not the disposition. Rating: resolved legacy headwind, and a governance and disclosure signal. It does not change the fee metric.

The complaint alleges a Token Swap from ERC-20 DAG tokens to mainnet DAG tokens on a single day in April 2020, and alleges that holders were excluded. Those sentences are allegations, not findings. The PDF caption prints Case 3:21-cv-08869, Document 1, filed 11/16/21. The one-for-one language in that PDF is a prayer for restitution (paragraph 187), not a finding that the 2020 swap was 1:1. No amount from the complaint is used here.

Awards to UEI HH64FJ1EB5S7. None pay in DAG.

- FA864921P1550, Air Force, "END-TO-END DATA SECURITY USING BLOCKCHAIN ENCRYPTION AND HOSTING DECENTRALIZATION," $749,202, performance 2021-08-06 to 2022-09-06, completed. Fetch time 15:49:37 ET.
- W911S222P1470, Army, $243,080, visitation counters, completed.
- W912CH24CL012, Army, $514,800, F21 sensor API licenses, NAICS museums, potential end 2027-09-15. Not a Hypergraph award.

Similar names (Constellation Software Engineering, Constellation Networks Corp, Muon Space) were excluded and stay excluded.

PacaSwap. The company post promised a table on the PacaSwap site by October 1. The site, fetched in the research run, says distributions complete and links a Google Sheet titled "Pacaswap - Token transfers." The HTML view returned a Drive shell and no table rows. Blocker: row-level reconciliation was not done. A reply on the PacaSwap status claims a missing pool share. That claim is unverified.

Unit line: geography and venue access are headwinds for a token whose fee metric is $2.93 a day. Government work does not change the metric. The closed 2021 lawsuit does not change it either.

## Analogies and layered TAM

| Analogy | What matches | What does not | Business outcome | Investor outcome | Loss? |
|---|---|---|---|---|---|
| IOTA, feeless data ledger | Users are not the fee payer. Both are priced as infrastructure | Saved last closed epoch: 1,993,800 transactions and $11.51 of gas. Different consensus. Years below peak and council stay unsourced and unused | Saved 365-day indexed path 31.9, so the business's token fell over the saved year | A position opened on the first saved day is down about 68% by the last saved day | Yes |
| Hedera | Larger cap in the same pull, 154.7x | Council-run and fee-disclosed stay removed as labels. Saved census: 477,279 transactions a day including 553 duplicate rows, and $409.63 of fees. Like-for-like count is 328,332. A large cap is still not the evidence | Indexed path 47.9 | Down about 52% over the saved year | Yes |
| Sonic | Rebranded chain in the peer set, cap 5.3x | Retained a fee market stays removed as a slogan. Saturday point: 89,952 transactions and $19.91. 30-day means: transactions -37.42%, fees in S +2.48%. Fees are not shrinking on that mean | Indexed path 14.6 | Down about 85% over the saved year | Yes |
| This token's own high | A fee-light network token with a large prior print | Not an outside analogy. Included so the base rate is the asset itself | ATH $0.451761 on 2021-08-25 | Drawdown 98.3% to the price box | Yes |

Removed as uncited: continuous shipping since 2018, metagraphs have been coming for years, and 2018 ICO as a fact. The public GitHub repo Constellation-Labs/constellation was created 2017-12-05. That is a repo timestamp, not a shipping record. The 2018 offering claim was not confirmed against a primary document.

Where the toll-booth metaphor breaks: the operator is paid in new coins, the toll is burned, and most transfers pay nothing. A real toll booth that collected $2.93 a day would not be valued at $30.6 million.

| Layer | Gating variable | Earliest year | Unit volume | Unit price | Revenue range | Probability |
|---|---|---|---|---|---|---|
| Core | Metagraphs already submitting snapshots | 2026, measured | 49,156 snapshots a day | $0.000053 | $1,068 a year | 100% measured |
| Adjacent | October 15 cut lands and fees rise to cover 30 servers | 2027 | same snapshot volume, ASSUMPTION | about $0.0016 if fees equal $28,691 | $0 to $28,691 | 15%, range 5% to 30%, ASSUMPTION |
| Option | A published DAG fee rate for Gate, and a start date | Not dated | Unknown | Unknown | $0 to $5 million, ASSUMPTION ceiling | 5%, range 1% to 15%, ASSUMPTION |

Company claim, Ben Jorgensen, 2026-09-29, same saved page: "The market for AI compute and inference is projected at roughly $109 billion today, scaling toward $500 billion within four years." No source is named in the sentence. Our core is $1,068. We do not adopt $109 billion.

Second-order effects. If home GPUs actually clear Gate requests, a slice of cloud GPU rental loses that work. Unproven. If snapshot fees stay near zero, holders of other feeless-ledger tokens learn nothing new: a large narrative and a small tape can coexist, which is the base rate already in the saved-year paths.

Unit line: the only layer with a unit price and a volume is $1,068 a year. The loss analogies are the saved-year paths. None of them rescue a $2.93 fee day.

![Analogy panel](/assets/2026-10-06-constellation/14-analogy-panel.svg "Saved-year paths. IOTA indexed 31.9, Hedera 47.9, Sonic 14.6. DAG drawdown 98.3% from the 2021 high to the price box. [Data provided by CoinGecko](https://www.coingecko.com/).")

![TAM stack, core measured, option unproven](/assets/2026-10-06-constellation/12-tam-stack.svg "TAM stack. Only the core bar, $1,068 a year, is measured. The option bar is an unproven level, not a result. CoinGecko price box only. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Scarce rights

The limit is a rule. Snapshot inclusion is not physically scarce at the measured volume (49,156 snapshots a day against a network the company says is oversized at 200 operators). The tight rule is the announced active set of 30, ranked each quarter by delegation, with a 1,000,000 DAG wallet hold. Room in the directory is abundant (287 nodes). The moat, if any, is regulatory in the loose sense: the company wrote the seat count.

| Resource | Total capacity | Share, with denominator | Demonstrated claim rate | Use it or lose it | Who can reallocate | Deed or lease |
|---|---|---|---|---|---|---|
| Active validator seats | 30 from October 15, announced. Directory 287. Ready now 119 of 123 listed | Top 5 nodes hold 50.05% of 941 million delegated. Cutoff for a top-30 rank: 1,958,920 DAG | Not yet live. Current Ready set is 119, so the claim rate into the 30 is zero until the ranking | Quarterly re-rank. Wallet hold of 1,000,000 DAG. Indexer field minHoldingsEnforced is false, so the 1M rule is not live | Company set the count and the hold in the September 29 post. Ranking is by delegation. Stardust Collective votes the emission schedule, not the seat list | Lease. Re-ranked every quarter. The count was just cut from over 200 to 30 by announcement |
| Snapshot inclusion | Not capped in the saved docs | 12 metagraphs submitted in 90 days | 7 submitted in the last 30 | Pay the fee or the snapshot is not the product | Fee formula is in the docs. Company can change it | Lease, paid per use, $0.000053 |
| Exchange listings | 10 tickers in the coin object | KuCoin 39.2% of $512,900 | Not a 12-month listing rate | Venue rules, unobserved | The venue | Lease |
| Government contract position | No slot cap | One blockchain-described PO, ended 2022. Two Army awards, one still inside a potential end date of 2027-09-15 | No new blockchain award in the saved search | Option years and closeout | The contracting officer | Lease |
| Emission vote | One body named | Stardust Collective. Holder share of that vote: not stated | Vote not yet published | Not stated | The Collective, per the company post | Not a holder deed |

Bear angles. Abundance: directory seats are plentiful, and the 30-cap is a rewriteable rule. Revocability: the company already cut the set by announcement. Sovereignty: 63.4% of listed nodes on one German host. Concentration: five nodes, 50% of delegation, one labeled CEO. The 1M rule is not enforced yet, so the occupancy chart's eligible bar is an indexer flag (125), not a live filter.

Verdict. Seats explain little of the moat independent of the competitive gap. ASSUMPTION: 5% to 15% of any moat, and that share is a consequence of a company rule, not a deed. The fee gap would remain if the set were 300. Scenarios do not add a seat-scarcity premium.

Unit line: a seat is a lease on a toll booth that collects $2.93 a day.

![Occupancy: Ready 119, 1M rule not enforced](/assets/2026-10-06-constellation/15-occupancy.svg "Occupancy. Ready 119 of 123 listed. Directory 287. Indexer-eligible 125. minHoldingsEnforced false. Source: L0 cluster and Dagscan, 2026-10-04 15:39 ET.")

## Author grades

These are the author's grades from the graded bundle, not a reviewer's. A to F, on the token as an investment, after the cite fixes. They do not change the call. The call is the fee gap.

| Grade | Letter | Why |
|---|---|---|
| Problem and design fit | A- | The problem is real. The design charges the application. Held back by 12 submitting metagraphs and a fee of $0.000053 per snapshot. The whitepaper says each layer can scale horizontally. |
| Team | C+ | Names are public. The September 29 posts are specific and dated. Against that: the PacaSwap exploit on September 9, a payout table promised by October 1, and a Google Sheet whose HTML view did not render rows. Military work is one blockchain-described purchase order plus two Army awards, not one purchase order. |
| Backers | C | No named institutional holder in the saved primary set. The 2018 offering claim is unverified and is not used. |
| Tokenomics | D | Endpoint supply is uncapped. Construction A issuance is 489,964 DAG a day, 13.9% from the observed median. Snapshot burn is $236 over 90 days. The emission vote is not a holder vote (INFERENCE). |
| Traction | D | 301 transfers a day. Correlation of daily transfer counts with price over the 90-day window is 0.03. Lattice closes October 15. |
| Competition | C- | Differentiation is real. IOTA moves 6,624x the transactions and takes in 3.93x the fee dollars. Sonic transactions are down on the 30-day mean. Sonic fees are not. Hedera's like-for-like count is down. The grade stays C- because DAG's own fee day did not change. |
| Narrative | C+ | The sentence "users free, applications pay" is honest. The fee tape contradicts the scale of the AI claim. |
| Moat | D | Snapshot fees of $2.63 a day, not the combined $2.93, are the lock-in evidence. Combined fees are $2.93 and include transfer fees that are not documented as burned. Government work is not a moat. |
| Decentralization | D+ | 119 Ready of 123 listed. 63.4% Hetzner. Top 5 nodes, 50% of delegated DAG. The October 15 set of 30 is chosen each quarter by delegation ranking, not chosen by the company as a description of the ranking. INFERENCE, separate: the company wrote the rule that creates the set, and five nodes already hold half the stake that will do the ranking. |
| Security | C- | Exploit on September 9. Company says funds were restored. Payout sheet not row-reconciled. 21-day unbonding. No saved base-layer exploit. |
| Composite | D+ | The design is interesting. The unit metric is $2.93 a day. |

## What has to be true

Mature multiple: 25x, ASSUMPTION, range 15x to 40x. Hurdle rate: 20% a year, ASSUMPTION, range 10% to 30%. Neither is a market fact.

At 25x, the cap implies annual fees of $30,588,422 / 25 = $1,223,537. Today: $1,068. Gap: 1,145x. At 15x the implied fees are $2,039,228 (1,909x). At 40x, $764,711 (716x). A 20% hurdle on the cap, treated as a perpetuity, implies $6.12 million a year of fees, about 5,730x. The hurdle framing is stricter than the multiple framing. Both are assumptions.

| Requirement | Implied by the price | Value today | Gap | Precedent in the saved files | Probability |
|---|---|---|---|---|---|
| Annual fees at 25x | $1,223,537 | $1,068 | 1,145x | None. No saved fee step of this size | 5%, range 1% to 15%, ASSUMPTION |
| Fees cover 30 servers | $28,691 | $1,068 | 26.9x | Not demonstrated | 15%, range 5% to 30%, ASSUMPTION |
| Issuance falls to the fee burn | Burn $236 per 90 days | Issuance about $3,811 a day | Burn is 0.2% of a day of issuance | Vote not published | Not used in the price |
| Seats become a deed | A transferable cap that fees cannot bypass | Lease, re-ranked quarterly | The price does not need more seats than exist. It needs more fees | Company just cut the cap | Does not close this section |

Operations translation of the 25x row, at today's snapshot volume of 49,156 a day: the fee per snapshot would have to be $0.068, versus $0.000053 now. That is a price change for the same unit, or a volume change of the same multiple if the unit price stays. Neither is in the tape. The servers already exist and are paid by issuance. The missing input is a customer.

| Case | 15x | 25x | 40x |
|---|---|---|---|
| Multiple only | $2,039,228 | $1,223,537 | $764,711 |
| Hurdle 10% | $3.06 million | same hurdle, multiple does not change it | perpetuity, not a multiple |
| Hurdle 20% | $6.12 million | perpetuity, not a multiple | perpetuity, not a multiple |
| Hurdle 30% | $9.18 million | perpetuity, not a multiple | perpetuity, not a multiple |

The hurdle column does not depend on the multiple. It is the other assumption. Both say the same thing: today's $1,068 is not in the grid.

Steelman, in the company's words. The network is being aimed at AI inference. Operators with their own hardware get paid in DAG for work a Gate user has already paid for. Emissions get tighter. Snapshot fees start to reflect work. If that happens, the unit metric stops being a rounding error, the burn starts to matter, and a 30-node set is cheaper to run than 119. The strongest version is not "the cap is cheap versus $109 billion." The strongest version is "a measured fee step-up is coming, and the token is the meter."

Price the steelman as an option. Value if the option layer fully hits the $5 million ASSUMPTION ceiling, at the 25x assumption: a $125 million cap, about 4 times today. Probability 5%. Time to cash: not dated, so no discount is applied beyond the probability. Expected cap from the option: about $6.3 million. Core business at 25x on measured fees: $26,700. The cap is $30.6 million. The unexplained remainder is the option, and the option's expected value as priced here is below that remainder. The steelman does not cover the price on these assumptions. Change the probability to 25% and it still does not cover, because 25% of a 4x is not 1,145x fees.

Bear, same standard. Fees stay near $1,068. Issuance continues near construction A. The October 15 set is the same concentrated delegators. The unlabeled wallet meets a thin book. Price path: the scenario bear, $0.0035 in 12 months. That is a 55% decline from the price box, which is less severe than the saved year's 72% decline. It is not a crash case. It is the fee tape persisting.

The price discounts the steelman, not the core. A core-only price at 25x on measured fees is about $0.0000068 per DAG, not $0.0078. Almost the entire price is the option. The call says the option is not worth that.

Unit line: the price needs $1.22 million a year of fees. The unit delivers $1,068. The price is a bet that $2.93 a day becomes $1.22 million a year. The steelman does not show the path in the saved files.

![What has to be true](/assets/2026-10-06-constellation/13-what-has-to-be-true.svg "What has to be true. 1,145x from $1,068 to the 25x implied fee of $1,223,537. ASSUMPTION multiple, range 15x to 40x. CoinGecko price box. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Scenarios

Paths are assumptions, not forecasts. Weights sum to 100%. Geometric and arithmetic expected values are both stated. v1 prices and weights are unchanged from the graded bundle. What changed in that bundle is the driver, which now names a row above. Nothing here is an order.

12-month:

| Path | Price | Weight | Row | Driver |
|---|---|---|---|---|
| Bear | $0.0035 | 35% | Fee row stays at today | Cutover seats the concentrated delegators, issuance near construction A, no fee step |
| Base | $0.0080 | 45% | Fee row stays immaterial | Cutover lands, a few metagraphs continue, token tracks the saved peer path |
| Bull | $0.0180 | 20% | Fee row moves toward hosting cover, not toward 25x | Gate fees appear on the snapshot tape and a named customer is in a primary record |

Geometric expected value: $0.00704. Arithmetic: $0.00843. Geometric is below the price box. That is the research view: the weighted midpoint does not pay for a position.

3-month:

| Path | Price | Weight | Row | Driver |
|---|---|---|---|---|
| Bear | $0.0045 | 30% | Fee row stays at today | Ranking on October 9 and the cut on October 15 read as concentration, volume stays thin |
| Base | $0.0075 | 50% | Fee row stays immaterial | Cutover lands, no fee step, price stays near the box |
| Bull | $0.0120 | 20% | Hosting-cover row starts, does not arrive | A fee week above the signpost, or a published Gate rate |

Geometric: $0.00707. Arithmetic: $0.00750.

Opinion, labeled as the research view: avoid. The bull path is the only one that touches an improvement on the fee row, and it is still far from the 25x row. Nothing in the weights depends on a seat shortage.

Unit line: the weighted 12-month price is under the box because $2.93 a day is the base, not the bull.

![Scenario fan](/assets/2026-10-06-constellation/06-scenario-fan.svg "Scenario fan. 12-month geometric expected value $0.00704, below the Oct 4 price box of $0.00777823. Paths are assumptions, not forecasts. [Data provided by CoinGecko](https://www.coingecko.com/).")

## Catalysts, risks, and what would change the view

Variant perception: the market is paying for an inference fee stream that is not on the tape, while issuance to the protocol alone is about $963 a day. The variant is that the fee gap, not the narrative, is the asset.

Catalysts, dated:

- October 9, 2026: first delegation ranking announced. Not yet observed in the graded file. If this note is read after that date, check the cluster. This publish does not add a later observation.
- October 15, 2026: active set of 30, Lattice frontend closes, testnets retire.
- Emission vote with the Stardust Collective: "over the coming weeks" from September 29. No published schedule in the saved post.

Hypothetical expression, not an order: none. If someone were forced to keep a position, size it as a full loss against the fee gap, and do not add until the signpost prints. Liquidity for a $30.6 million cap with $512,900 of daily volume does not support a large exit. No stop is stated because there is no entry.

Risk register:

- Emission vote cuts or raises issuance. Cuts would weaken the dilution leg and would not close the fee gap.
- October 15 seats the same five nodes that hold half of delegated DAG.
- Hetzner policy or price, 63.4% of listed nodes.
- Unlabeled 524 million DAG wallet moves into the thin books.
- Kraken halts the pair.
- A regulator reads the seat rule as an offer. No such order is in the file.

Incidents: PacaSwap exploit, September 9, 2026. Unknowns: who was made whole, marked unverified pending the sheet.

Kill criteria: revisit the avoid if snapshot fees exceed 50,000 DAG in any rolling 7 days on Dagscan and the same jump is visible on the official explorer, with a published fee wallet. That is 21x the current 90-day week. A landed October 15 cut is not a kill of the avoid. It is the base path.

Monitoring:

1. Live Ready count after October 15. A landed cut is about 30, not 60. Still above 60 after October 20 means the cut did not land.
2. Snapshot fees, 7-day, above 50,000 DAG, confirmed on the official explorer. That is the bull signpost. It is 21x the 90-day week.
3. A new USAspending row for UEI HH64FJ1EB5S7 whose description is Hypergraph work.
4. CoinGecko circulating daily delta. A one-day jump near the size of the October 2025 step is a restatement until an on-chain supply history says otherwise.
5. The unlabeled 524 million wallet. A move over 20 million DAG in a day into an exchange-labeled address.
6. Kraken pair status.
7. The emission schedule, once the Stardust Collective vote is published.

Constraint sweep, binding limits that survived: the fee tape, the host, and the seat rule. Physics of snapshot inclusion is not binding at measured volume. Geography is a host choice (Hetzner, Germany and Finland, 63.4%). Law is unadjudicated. Seat allocation is a rewriteable rule: $15,237 to match the cutoff, $243,791 for 16 seats. Supply chain is the CPX51 at $79.70 in the EU, or $267.16 in the US. Energy is not binding for a CPU node. GPU inference is unpriced. Capital is token collateral and delegation: protocol, $963 a day of new coins; 1,000,000 DAG to qualify. Talent is not measured. Time: October 9 and October 15 are dated. Network effects are not evidenced by fees. A new metagraph pays $0.000053 a snapshot.

Unit line: no physical limit makes a snapshot worth more than $0.000053 today. The memo is avoid because $1,068 a year is the measured business.

## Data we could not get

- A day-by-day social corpus and a Google Trends series. The bundle marks that work internal. Chart 17 is not published. Nothing in the saved attention material raises the $2.93 fee day.
- PacaSwap sheet rows. URL saved. HTML view had no rows.
- SAM.gov entity print, a sbir.gov award page for this UEI, and an AFWERX award body. USAspending awards stand.
- Hedera has no calendar-day total, only two interval censuses. The inclusive count includes 553 rejected duplicates. The like-for-like count is the one used for growth.
- Order-book depth and active addresses.
- A long-form independent skeptic essay. The search across YouTube, Substack, Medium, Reddit, and Messari saved no essay. The named gap is accepted. It is not evidence of safety.
- Industry insider added in the bundle: BioFi, a metagraph builder, 2026-08-12. Three managed nodes, fees paid in DAG, no dollar rate.
- D4 red team (Duwa) has not been done. Placeholder: [D4 pending].
- ip-api.com terms: geolocation used the free batch endpoint. Country counts in this note are the graded Oct 4 figures (Germany 52, United States 33, Finland 32, and 6 elsewhere; Hetzner 78 of 123). Orda should read https://ip-api.com/docs/legal before any public display is treated as cleared. This flag is not a clearance.
- The two Justia browser saves from Oct 4 22:15 ET are outside the bundle hash manifest. They are not cited as a second source. The disposition used here is the page extract and the complaint PDF.

## Methods

- Fee run rate: Dagscan 90-day totals divided by 90, times the price box. Snapshot and transfer kept separate, then summed. Annualized times 365.
- Issuance construction A: delegated times 0.102 / 365 is delegator pay. Subtract delegated times 0.03 / 365. Divide the remainder by 0.45 to get variable emissions. Add the fixed piece back. Construction B skips the subtraction.
- Reconciliation: median of the last 100 CoinGecko circulating deltas (cap / price). Tolerance 15%.
- Volatility: standard deviation of daily log returns over the overlapping CoinGecko days, times square root of 365. Population standard deviation. Correlation is the matching covariance with Bitcoin.
- Hosting: EUR list price times Frankfurter EURUSD 1.1225, rate date 2026-10-02. Base SKU is CPX51 in Germany and Finland because the operator guide names it and because 74 of 78 Hetzner nodes are there.
- Concentration: top 5 delegated amounts over totalDelegated. Hetzner share is isp equal to "Hetzner Online GmbH," 78 of 123, not a substring match.
- Implied fees: cap divided by the assumed multiple, divided by annualized fees. Hurdle is cap times the rate, a perpetuity, labeled as such.
- Peer set: IOTA, Hedera, Sonic. IOTA is the last closed 24-hour epoch. Sonic's labelled point is the explorer daily chart. Sonic's 12-month growth is the 30-day mean from that chart. Hedera is an interval census. The like-for-like Hedera count drops DUPLICATE_TRANSACTION rows. IOTA and Sonic dollar legs use the 15:39:42 CoinGecko print. Hedera fee dollars use the mirror-node exchange rate.
- Geolocation: ip-api.com batch on L0 IPs. Third party. Not a network field. Flagged for Orda.
- Charts in this note are the graded bundle drawings, except chart 17, which is omitted. No new package was installed to redraw them. No CoinGecko raw is committed.

Charts in this note use the Oct 4 research pulls. The Oct 6 publish pull is prose only. No CoinGecko raw JSON or CSV is committed with the article. [Data provided by CoinGecko](https://www.coingecko.com/).

Research only. Not financial advice. Nothing here is an offer to buy, sell or hold any asset.
