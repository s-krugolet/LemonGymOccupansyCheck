#!/usr/bin/env bash
# Тепловые карты «день недели × час»:
#   ./heatmap.sh                  — все клубы
#   ./heatmap.sh Imanta           — один клуб (часть названия, без учёта регистра)
#   ./heatmap.sh Imanta 7-22      — один клуб, только часы 7–22 (по умолчанию все часы, где есть данные)
#   ./heatmap.sh "" 7-22          — все клубы, часы 7–22
set -euo pipefail
cd "$(dirname "$0")"
club="${1:-}"
hours="${2:-0-24}"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q pandas matplotlib
fi

if [ -n "$club" ]; then
  exec .venv/bin/python analyze.py --club "$club" --slot 60 --hours "$hours" --top 5
fi

# shortcut: берёт 2-ю колонку CSV через cut, сломается, если в названии клуба появится запятая
cut -d, -f2 data/occupancy.csv | tail -n +2 | sort -u | while read -r c; do
  .venv/bin/python analyze.py --club "^${c}$" --slot 60 --hours "$hours" --top 5
done
