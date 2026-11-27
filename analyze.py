#!/usr/bin/env python3
"""
Строит статистику по собранным данным и ищет самое свободное время.

  pip install pandas matplotlib
  python3 analyze.py --club Imanta                     # тепловая карта + топ свободных слотов
  python3 analyze.py --club Imanta --hours 7-22 --slot 30 --top 15

Результат: heatmap_<club>.png и таблица в консоли.
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(HERE, "data", "occupancy.csv"))
    ap.add_argument("--club", help="часть названия клуба (без него — список клубов)")
    ap.add_argument("--slot", type=int, default=30, help="размер слота, минут (по умолчанию 30)")
    ap.add_argument("--hours", default="0-24", help="часы, напр. 7-22 (по умолчанию все, за которые есть данные)")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()

    df = pd.read_csv(a.csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Europe/Riga")

    if not a.club:
        print(df.groupby("club")["occupancy_pct"].agg(["count", "mean", "max"]).round(1))
        print("\nУкажите --club <название>")
        return

    d = df[df["club"].str.contains(a.club, case=False)].copy()
    if d.empty:
        raise SystemExit(f"Клуб '{a.club}' не найден. Есть: {', '.join(sorted(df['club'].unique()))}")
    club = d["club"].iloc[0]

    h0, h1 = map(int, a.hours.split("-"))
    t = d["timestamp"]
    d["dow"] = t.dt.day_of_week
    d["slot"] = (t.dt.hour * 60 + t.dt.minute) // a.slot * a.slot
    d = d[(t.dt.hour >= h0) & (t.dt.hour < h1)]

    g = d.groupby(["dow", "slot"])["occupancy_pct"].agg(mean="mean", median="median", n="count",
                                                        p90=lambda s: s.quantile(.9))
    days_seen = d["timestamp"].dt.date.nunique()
    print(f"{club}: {len(d)} замеров за {days_seen} дн. "
          f"({d['timestamp'].min():%d.%m %H:%M} – {d['timestamp'].max():%d.%m %H:%M})")
    if days_seen < 14:
        print("⚠ Меньше двух недель данных — выводы предварительные.")

    best = g[g["n"] >= 2].sort_values(["mean", "p90"]).head(a.top).reset_index()
    best["день"] = best["dow"].map(lambda i: DAYS[i])
    best["время"] = best["slot"].map(lambda m: f"{m//60:02d}:{m%60:02d}–{(m+a.slot)//60:02d}:{(m+a.slot)%60:02d}")
    print(f"\nСамые свободные слоты ({a.hours} ч):")
    print(best[["день", "время", "mean", "median", "p90", "n"]].round(1).to_string(index=False))

    # Лучшее время по каждому дню недели
    per_day = g[g["n"] >= 2].reset_index().sort_values("mean").groupby("dow").head(1).sort_values("dow")
    print("\nЛучший слот в каждый день:")
    for _, r in per_day.iterrows():
        m = int(r["slot"])
        print(f"  {DAYS[int(r['dow'])]}  {m//60:02d}:{m%60:02d}  ≈{r['mean']:.0f}%")

    pivot = g["mean"].unstack("dow").reindex(columns=range(7))
    fig, ax = plt.subplots(figsize=(8, max(4, len(pivot) * 0.22)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0,
                   vmax=max(60, float(pd.Series(pivot.values.ravel()).max(skipna=True) or 60)))
    ax.set_xticks(range(7), DAYS)
    ax.set_yticks(range(len(pivot)), [f"{m//60:02d}:{m%60:02d}" for m in pivot.index])
    for (i, j), v in pd.DataFrame(pivot.values).stack().dropna().items():
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7)
    ax.set_title(f"Lemon Gym {club}: средняя загрузка, %")
    fig.colorbar(im, ax=ax, shrink=.6)
    fig.tight_layout()
    out = os.path.join(HERE, f"heatmap_{club.replace(' ', '_')}.png")
    fig.savefig(out, dpi=130)
    print(f"\nТепловая карта: {out}")


if __name__ == "__main__":
    main()
