# MPStats API — каталог под поиск новинок

Практический мост между правилами ручного поиска из курса и конкретными эндпоинтами MPStats. Читать после [api-limits](api-limits.md) — там обзор, здесь конкретика под наш пайплайн.

## Что этим закрываем

Ручной поиск в UI MPStats хорош для одной ниши за вечер. Когда категорий 7+ (дом/сад, строительство, бытовая техника, авто, спорт, зоо, хобби — как рекомендует курс) и прогон надо делать регулярно под обновляющийся бюджет — нужен API. Правила поиска остаются те же, меняется только способ их применения.

## Базовые настройки

| | |
|---|---|
| Базовый URL | `https://mpstats.io/api` |
| Аутентификация | заголовок `X-Mpstats-TOKEN: <token>` |
| Лимит записей в ответе | до 5 000 на запрос |
| Rate limit | ~100 req/min, при превышении — `429` |
| Дневная квота | 10 000 запросов/день на каждый из модулей `wb_external` и `ozon_external` (тариф 200, апрель 2026) |
| Тариф | Advanced Jam / Premium Jam (~7–15 тыс ₽/мес, API открывается на Advanced+) |
| Документация | [docs.mpstats.io](https://docs.mpstats.io) |

Профиль и квоту проверяем через `GET /me` — отдаёт `subscriptionStatus.<module>.dailyLimits` и `availableTools`. Эндпоинт `/user/check/limits` из старой документации больше не работает, отвечает `405`.

## Карта «правило курса → эндпоинт MPStats»

Шесть правил выбора товара из [методологии](../course/methodology/) и [поиска товара](../course/product-search/) ложатся на 2–3 эндпоинта. Основная нагрузка — `POST /wb/get/category`, он умеет и сортировку, и фильтры.

| Правило из курса | Endpoint | Параметр запроса |
|---|---|---|
| Топ SKU категории по выручке | `POST /wb/get/category` | `sortModel: [{colId: "revenue", sort: "desc"}]` |
| Фильтр выручки под бюджет (100–300К при бюджете 150К) | тот же | `filterModel.revenue: {filter: 100000, filterTo: 300000, type: "inRange"}` |
| Новизна ≤ 180 дней | тот же | `filterModel.firstAppearOn: {type: "greaterThan", filter: "<дата −180 дн>"}` |
| Отзывов мало (≤ 100) | тот же | `filterModel.comments: {type: "lessThanOrEqual", filter: 100}` |
| Плавное распределение на первой странице | тот же | `startRow: 0, endRow: 20` — потом проверяем отношение revenue[0] / revenue[19] ≤ 10× |
| Остатки быстро заканчиваются | тот же + `GET /wb/get/item/{sku}/sales` | `balance` из категории, `sales` из item → days_of_stock = balance / sales_per_day |
| Потенциал карточки (текущая + упущенная) | `POST /wb/get/category` | поля `revenue` и `lost_profit` / `lost_revenue` в ответе |
| Тренд ниши (не падает ли) | `POST /wb/get/category/trend` | `path`, `d1/d2` за 180 дней |
| Список предметов внутри категории | `GET /wb/get/subject/list` | `path` |
| SEO-ядро по топу конкурентов | `GET /wb/get/item/{sku}/by_keywords` | `d1/d2` — собираем по топ-30, чистим НЧ <1000 |
| Отзывы конкурента (боли для инфографики) | `GET /wb/get/item/{sku}/reviews` | |

Для Ozon используется префикс `/oz/` вместо `/wb/`: `POST /oz/get/category`, и поля частично отличаются (есть флаги склейки).

## Чистая карточка без склейки

Это слабое место API: MPStats не отдаёт явный флаг «это склейка». Практика на 2026-04:

1. Ozon — берём `POST /oz/get/category`, у каждой карточки проверяем `sku_first` / `parent_sku`. Если есть — склейка.
2. WB — смотрим `color_count` и `size_count`. Больше 3–4 вариантов при одном nm_id = вероятная склейка.
3. Финал — ручная проверка топ-10 отобранных карточек в UI по ссылке `https://www.wildberries.ru/catalog/<nm_id>/detail.aspx`.

Поэтому **пайплайн гибридный**: API грубо фильтрует до 50–100 карточек, человек финалит топ-10.

## Пайплайн под конвейер новинок

```
DISCOVER   POST /wb/get/category  → 100-500 SKU по категории + бюджет
   ↓
ENRICH     GET /wb/get/item/{sku}/sales    (по топ-30)
           GET /wb/get/item/{sku}/by_keywords  (по топ-10)
   ↓
FILTER     новизна ≤180дн + отзывов ≤100 + тренд не падает
   ↓
RANK       потенциал (revenue + lost_profit) / (capital_needed)
   ↓
REPORT     csv с топ-10 → человек финалит в UI
```

Фаза 2 MARKET из [phases](../tool/phases/) работает именно по этому пайплайну.

## Пример скрипта (без выполнения — референс)

```python
# scripts/mpstats_new_products.py — заглушка под фазу 2 MARKET
# Запускать когда будет Advanced Jam подписка и токен.

import os
from datetime import date, timedelta
import httpx

TOKEN = os.getenv("MPSTATS_TOKEN")  # токен появится с подпиской
BASE = "https://mpstats.io/api"
HEADERS = {"X-Mpstats-TOKEN": TOKEN} if TOKEN else {}


def discover_new_products(
    path: str,             # напр. "Дом/Инструменты/Ручной инструмент"
    budget_rub: int,       # напр. 150_000
    days_back: int = 60,   # окно анализа продаж
    max_reviews: int = 100,
    max_age_days: int = 180,
) -> list[dict]:
    """Фаза 2 MARKET — дискавери кандидатов."""
    d2 = date.today()
    d1 = d2 - timedelta(days=days_back)
    cutoff = d2 - timedelta(days=max_age_days)

    body = {
        "path": path,
        "d1": d1.isoformat(),
        "d2": d2.isoformat(),
        "startRow": 0,
        "endRow": 500,
        "sortModel": [{"colId": "revenue", "sort": "desc"}],
        "filterModel": {
            "revenue": {
                "type": "inRange",
                "filter": int(budget_rub * 0.67),
                "filterTo": int(budget_rub * 2),
            },
            "firstAppearOn": {"type": "greaterThan", "filter": cutoff.isoformat()},
            "comments": {"type": "lessThanOrEqual", "filter": max_reviews},
        },
    }

    r = httpx.post(f"{BASE}/wb/get/category", headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


def check_trend_not_falling(path: str, months: int = 6) -> bool:
    """Гейт: тренд ниши не падает за последние 6 мес."""
    d2 = date.today()
    d1 = d2 - timedelta(days=30 * months)
    body = {"path": path, "d1": d1.isoformat(), "d2": d2.isoformat()}
    r = httpx.post(f"{BASE}/wb/get/category/trend", headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    monthly = r.json().get("revenue_by_month", [])
    if len(monthly) < 3:
        return True
    first_third = sum(monthly[:2]) / 2
    last_third = sum(monthly[-2:]) / 2
    return last_third >= first_third * 0.9  # падение не больше 10%


def rank_by_potential(items: list[dict]) -> list[dict]:
    """Сортировка по суммарному потенциалу = выручка + упущенная."""
    for item in items:
        item["potential"] = (item.get("revenue") or 0) + (item.get("lost_profit") or 0)
    return sorted(items, key=lambda x: x["potential"], reverse=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("MPSTATS_TOKEN не задан — дождёмся подписки Advanced Jam")
    candidates = discover_new_products(
        path="Дом/Инструменты/Ручной инструмент",
        budget_rub=150_000,
    )
    ranked = rank_by_potential(candidates)[:10]
    for i, x in enumerate(ranked, 1):
        print(f"{i}. {x['name'][:50]:50} | {x['revenue']:>8} ₽ | отз {x['comments']}")
```

Код — *как это будет работать*, не рабочий скрипт. Запускать смысл только после Advanced Jam.

## Альтернатива без MPStats

Пока подписки нет, MVP фазы MARKET можно запускать через связку:

- **Wildbox** (`wildbox.ru`) — аналог MPStats, у них есть публичное API и триал.
- **Ozon внутренний «Товары в поиске»** — для Ozon-части.
- **Ручной выгруз в CSV** из UI MPStats-триала на одну категорию за раз.

Решение по поставщику аналитики — в [decisions](../tool/decisions/).

## Чего API не заменит

- **Эстетика карточки** топ-3 — смотреть глазами, алгоритм не оценит инфографику.
- **Качество инфографики** — то же.
- **Разница в позиционировании** между собой и конкурентами — читать их описания.
- **Сигналы из рекомендательных блоков WB** («С этим товаром покупают») — в API их нет.
- **Склейка** — детектируется плохо, см. выше.

Поэтому пайплайн финалится человеком на топ-10 после автофильтра до 100.

## Ссылки

- [Обзор API MPStats / WB / Ozon](api-limits.md) — сравнительная таблица и общий обзор
- [Фазы и гейты пайплайна](../tool/phases/) — где именно эти эндпоинты вызываются
- [wiki.mpstats.io](https://wiki.mpstats.io/) — база знаний MPStats
