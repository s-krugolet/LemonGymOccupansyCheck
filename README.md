# Мониторинг загруженности Lemon Gym Latvija

Источник — открытый эндпоинт сайта (тот же, что рисует страницу https://www.lemongym.lv/en/clubs-occupancy/):

```
GET https://www.lemongym.lv/wp-json/api/async-render-block?pid=MzkxNg==&bid=YWNmL2NsdWJzLW9jY3VwYW5jeQ==&rest_language=en
```
`pid` = base64("3916") — ID страницы, `bid` = base64("acf/clubs-occupancy") — блок.
Ответ: `{"success":true,"content":"<html>"}`; в HTML у каждого клуба название, адрес и загрузка в **процентах**. Авторизация не нужна.

## Вариант A — бесплатно на GitHub Actions (компьютер не нужен)
1. Создайте приватный репозиторий на GitHub и загрузите туда все файлы (вместе с `.github/workflows/collect.yml`).
2. Settings → Actions → General → Workflow permissions → **Read and write**.
3. Actions → collect-occupancy → **Run workflow** (проверка). Дальше данные копятся в `data/occupancy.csv` примерно каждые 10–15 минут.

## Вариант B — на своём компьютере / Raspberry Pi
```bash
python3 collect.py --loop 300          # каждые 5 минут
# или через cron:  */5 * * * * /usr/bin/python3 /path/collect.py
```

## Анализ (через 2–4 недели)
```bash
pip install pandas matplotlib
python3 analyze.py                       # список клубов
python3 analyze.py --club Imanta --hours 7-22
```
Выводит самые свободные получасовые слоты, лучший слот на каждый день недели и сохраняет тепловую карту `heatmap_<клуб>.png`.
