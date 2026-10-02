# CoinGecko raw pulls for the 2026-10-02 Pearl (PRL) note (v3 hotfix and v4-clean)

Keyless CoinGecko public API, saved exactly as returned. Times are ET (America/New_York, UTC-4). Data provided by CoinGecko.

days=max for pearl-2 was refused (HTTP 401, error 10012: public API limited to the past 365 days), so days=365 was used. Rate-limited (429) attempts are logged in pulls.log and kept in failed/; they are not sources.

The market_chart days=1 pulls (5-minute points) archive the intraday reads the note uses: 11:45 ET price, market cap, FDV basis and volume/market cap ratios for PRL and the peer set (TAO, RENDER, ZEC, AKT). coins/pearl-2/tickers archives the venue volumes. Pull scripts: pull_days1.sh, pull_tickers.sh.

| file | URL | pulled (ET) | sha256 |
|---|---|---|---|
| akash-network_market_chart_1_20261002T192119-0400.json | https://api.coingecko.com/api/v3/coins/akash-network/market_chart?vs_currency=usd&days=1 | 2026-10-02 19:21:19 EDT | ecdf58dfa09d6edc065edc3b5abb5dbec48b1b3d3fed3b40d8bcc4fa1296b4f5 |
| bitcoin_market_chart_365_20261002T184530-0400.json | https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365 | 2026-10-02 18:45:30 EDT | d47012177fce9d460b009e26a9735134f77335fc6a1d0314744729eb49810a2b |
| bittensor_market_chart_1_20261002T191648-0400.json | https://api.coingecko.com/api/v3/coins/bittensor/market_chart?vs_currency=usd&days=1 | 2026-10-02 19:16:48 EDT | 733c83a6aa382f6d5bb70b6bb50cc2278e34bb4272106b896d6f2566e70aeabe |
| bittensor_market_chart_365_20261002T184655-0400.json | https://api.coingecko.com/api/v3/coins/bittensor/market_chart?vs_currency=usd&days=365 | 2026-10-02 18:46:56 EDT | 9618ce02113818078e794fd7cb9a2c400357123d6e9e1ccd6b9990b2af4dc059 |
| pearl-2_coin_20261002T184405-0400.json | https://api.coingecko.com/api/v3/coins/pearl-2?localization=false&tickers=false&community_data=false&developer_data=false | 2026-10-02 18:44:05 EDT | d3e635375ea3b4d17ae444fd1929d1c2a0c933d1fb34a645943f38c22752a84e |
| pearl-2_market_chart_1_20261002T191518-0400.json | https://api.coingecko.com/api/v3/coins/pearl-2/market_chart?vs_currency=usd&days=1 | 2026-10-02 19:15:18 EDT | 69204ae0b06453dec865ae0bfec6ce22f6d6ec9a220189ddc10f3fc1e64998f0 |
| pearl-2_market_chart_365_20261002T185113-0400.json | https://api.coingecko.com/api/v3/coins/pearl-2/market_chart?vs_currency=usd&days=365 | 2026-10-02 18:51:14 EDT | ca95ae7262c218adcce3244fd8adcfb8435d39bace60bf73dcbb66b712f04e4e |
| pearl-2_tickers_20261002T192311-0400.json | https://api.coingecko.com/api/v3/coins/pearl-2/tickers | 2026-10-02 19:23:12 EDT | a081f2fab53c5169196578fbb29a5c7f4400c6edd26081a859009e372505c6f8 |
| render-token_market_chart_1_20261002T191818-0400.json | https://api.coingecko.com/api/v3/coins/render-token/market_chart?vs_currency=usd&days=1 | 2026-10-02 19:18:19 EDT | 5abc7c7b6891812e4646950b5155cc28b3e101fd8bbaa2c5e64851a0b1c7e7fb |
| render-token_market_chart_365_20261002T185519-0400.json | https://api.coingecko.com/api/v3/coins/render-token/market_chart?vs_currency=usd&days=365 | 2026-10-02 18:55:19 EDT | 93986d132c67074e5e50827f9701034f22bb07377574866c722529aad39a7003 |
| zcash_market_chart_1_20261002T191949-0400.json | https://api.coingecko.com/api/v3/coins/zcash/market_chart?vs_currency=usd&days=1 | 2026-10-02 19:19:49 EDT | 9aad7c5620fccc211f1536913d5fae1c9f89aeb8b54b87d2cc2e645bea31a3a2 |
