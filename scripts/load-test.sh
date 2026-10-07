#!/usr/bin/env bash
# hammer the api so the prometheus counters and the HPA have something to look at
#
#   ./load-test.sh                                   # defaults below
#   ./load-test.sh http://192.168.49.2 500           # 500 rounds
#   ./load-test.sh http://bookshelf.local 200 ""     # no Host header override
set -uo pipefail

URL="${1:-http://192.168.49.2}"
ROUNDS="${2:-200}"
HOST_HEADER="${3:-bookshelf.local}"

args=(-s -o /dev/null -m 5)
if [ -n "$HOST_HEADER" ]; then
  args+=(-H "Host: $HOST_HEADER")
fi

echo "sending $((ROUNDS * 3)) requests to $URL"
for _ in $(seq 1 "$ROUNDS"); do
  curl "${args[@]}" "$URL/api/books" || true
  curl "${args[@]}" "$URL/api/books/stats" || true
  curl "${args[@]}" "$URL/health" || true
done
echo "done"
