#!/usr/bin/env python3
"""
Снимает текущую загруженность клубов Lemon Gym Latvija и дописывает её в CSV.

Источник: страница https://www.lemongym.lv/en/clubs-occupancy/
Данные подгружаются из WordPress REST-эндпоинта:
  /wp-json/api/async-render-block?pid=<base64("3916")>&bid=<base64("acf/clubs-occupancy")>
Он возвращает JSON {"success":true,"content":"<html>"} с процентом загрузки каждого клуба.

Только стандартная библиотека Python 3.9+.
Запуск:  python3 collect.py               (один замер)
         python3 collect.py --loop 300    (замер каждые 300 с, бесконечно)
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

URL = ("https://www.lemongym.lv/wp-json/api/async-render-block"
       "?pid=MzkxNg==&bid=YWNmL2NsdWJzLW9jY3VwYW5jeQ==&rest_language=en")
TZ = ZoneInfo("Europe/Riga")
CSV_PATH = os.environ.get("LEMON_CSV", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "occupancy.csv"))

BLOCK_RE = re.compile(
    r'clubs-occupancy__club">\s*<h6[^>]*>(?P<club>.*?)</h6>\s*<p[^>]*>(?P<addr>.*?)</p>'
    r'.*?clubs-occupancy__percentage[^"]*">\s*(?P<pct>\d+)\s*%',
    re.S,
)


def fetch():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (personal occupancy logger)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    # Раньше HTML лежал в data["content"], теперь сайт отдаёт его в data["data"]["content"]
    content = data.get("content") or (data.get("data") or {}).get("content", "")
    return parse(content)


def parse(content):
    rows = []
    for m in BLOCK_RE.finditer(content):
        club = html.unescape(m["club"]).replace("\U0001F195", "").strip()  # убираем значок 🆕
        rows.append((club, html.unescape(m["addr"]).strip(), int(m["pct"])))
    return rows


def save(rows):
    ts = datetime.now(TZ).replace(microsecond=0).isoformat()
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "club", "address", "occupancy_pct"])
        for club, addr, pct in rows:
            w.writerow([ts, club, addr, pct])
    return ts


def once():
    rows = fetch()
    if not rows:
        print("Не нашёл данных в ответе — возможно, изменилась вёрстка сайта.", file=sys.stderr)
        return False
    ts = save(rows)
    print(ts, "  ".join(f"{c}:{p}%" for c, _, p in rows))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, metavar="SEC", help="повторять каждые SEC секунд")
    a = ap.parse_args()
    if not a.loop:
        sys.exit(0 if once() else 1)
    while True:
        try:
            once()
        except Exception as e:  # сеть упала и т.п. — пишем и продолжаем
            print(datetime.now(TZ).isoformat(), "ошибка:", e, file=sys.stderr)
        time.sleep(a.loop)


if __name__ == "__main__":
    main()
