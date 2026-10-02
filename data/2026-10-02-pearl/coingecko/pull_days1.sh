#!/bin/bash
# Keyless CoinGecko pulls, days=1 (5-minute points) for intraday reads. Saved exactly as returned.
cd /workspace/state/arghun/sources/coingecko
for id in pearl-2 bittensor render-token zcash akash-network; do
  for try in 1 2 3 4 5 6 7 8; do
    ts=$(date +%Y%m%dT%H%M%S%z); f="${id}_market_chart_1_${ts}.json"
    url="https://api.coingecko.com/api/v3/coins/${id}/market_chart?vs_currency=usd&days=1"
    code=$(curl -s -o "$f" -w '%{http_code}' -H 'accept: application/json' "$url")
    echo "$f|$url|$(date '+%Y-%m-%d %H:%M:%S %Z')|$code" >> pulls.log
    if [ "$code" = 200 ]; then break; else mv "$f" failed/; sleep 70; fi
  done
  sleep 20
done
echo DONE_DAYS1 >> pulls.log
