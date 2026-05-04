#!/usr/bin/env bash
# scan_subject.sh <slug> <path>
# Загружает top500 по revenue из subject WB за последние 30 дней,
# сохраняет JSON в raw/<slug>.json и печатает однострочную сводку.
set -euo pipefail
SLUG="$1"; SUBJECT_PATH="$2"
D1="2026-04-04"; D2="2026-05-03"
SHELF_MIN=440000; SHELF_MAX=1160000
OUT="$(dirname "$0")/raw/${SLUG}.json"
ENC=$(printf %s "$SUBJECT_PATH" | jq -sRr @uri)
curl -sS -X POST -H "X-Mpstats-TOKEN: $MPSTATS_TOKEN" -H "Content-Type: application/json" \
  "https://mpstats.io/api/wb/get/category?path=${ENC}&d1=${D1}&d2=${D2}" \
  -d '{"startRow":0,"endRow":500,"sortModel":[{"colId":"revenue","sort":"desc"}],"filterModel":{}}' \
  > "$OUT"
TOTAL=$(jq -r '.total // 0' "$OUT")
ROWS=$(jq -r '.data | length' "$OUT")
SUM_REV=$(jq -r '[.data[].revenue // 0] | add // 0 | floor' "$OUT")
TOP3_SHARE=$(jq -r '
  [.data[] | {seller, revenue: (.revenue // 0)}]
  | group_by(.seller)
  | map({seller: .[0].seller, rev: ([.[].revenue] | add)})
  | sort_by(-.rev)
  | (.[:3] | map(.rev) | add) as $t3
  | (map(.rev) | add) as $all
  | if $all > 0 then ($t3 / $all * 100 | floor) else 0 end
' "$OUT")
IN_SHELF=$(jq -r --argjson lo $SHELF_MIN --argjson hi $SHELF_MAX \
  '[.data[] | select((.revenue // 0) >= $lo and (.revenue // 0) <= $hi)] | length' "$OUT")
NB=$(jq -r --argjson lo $SHELF_MIN --argjson hi $SHELF_MAX \
  '[.data[] | select((.revenue // 0) >= $lo and (.revenue // 0) <= $hi) | select((.days_in_site // 999) <= 14)] | length' "$OUT")
NB_LOW_REV=$(jq -r --argjson lo $SHELF_MIN --argjson hi $SHELF_MAX \
  '[.data[] | select((.revenue // 0) >= $lo and (.revenue // 0) <= $hi) | select((.days_in_site // 999) <= 14) | select((.comments // 999) <= 30)] | length' "$OUT")
ANTI_TRAP3=$(jq -r --argjson lo $SHELF_MIN --argjson hi $SHELF_MAX \
  '[.data[] | select((.revenue // 0) >= $lo and (.revenue // 0) <= $hi) | select((.days_in_site // 999) <= 14) | select((.comments // 999) <= 30) | select((.days_with_sales // 0) >= 5)] | length' "$OUT")
printf "%-50s SKU=%-7s top3=%-3s%%  shelf=%-4s  NB=%-3s  NB+rev=%-3s  +trap3=%-3s\n" \
  "$SLUG" "$TOTAL" "$TOP3_SHARE" "$IN_SHELF" "$NB" "$NB_LOW_REV" "$ANTI_TRAP3"
