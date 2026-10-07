#!/usr/bin/env bash
# hammer the api so the prometheus counters and the HPA have something to look at
set -euo pipefail

URL="${1:-http://bookshelf.local}"
REQUESTS="${2:-300}"

echo "sending $REQUESTS requests to $URL"
for i in $(seq 1 "$REQUESTS"); do
  curl -s -o /dev/null "$URL/api/books" || true
  curl -s -o /dev/null "$URL/api/books/stats" || true
done
echo "done"
