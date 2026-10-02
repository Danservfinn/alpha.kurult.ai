#!/bin/bash
# Keyless CoinGecko pull of PRL venue tickers. Saved exactly as returned. Runs after pull_days1.sh.
cd /workspace/state/arghun/sources/coingecko
until grep -q DONE_DAYS1 pulls.log; do sleep 5; done
sleep 20
for try in 1 2 3 4 5 6 7 8 9 10; do
  ts=$(date +%Y%m%dT%H%M%S%z); f="pearl-2_tickers_${ts}.json"
  url="https://api.coingecko.com/api/v3/coins/pearl-2/tickers"
  code=$(curl -s -o "$f" -w '%{http_code}' -H 'accept: application/json' "$url")
  echo "$f|$url|$(date '+%Y-%m-%d %H:%M:%S %Z')|$code" >> pulls.log
  if [ "$code" = 200 ]; then break; else mv "$f" failed/; sleep 70; fi
done
echo DONE_TICKERS >> pulls.log
