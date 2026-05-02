# MPStats API — каталог под поиск новинок (актуализация на II квартал 2026)

Практический мост между правилами поиска из курса и точками доступа MPStats. Читать после [api-limits](api-limits.md) и параллельно с [`best-practices-2026.md`](best-practices-2026.md) §10–§13 — пороги ниже параметризованы под бюджет селлера, не дословные числа курса 2024.

## Что этим закрываем

Ручной поиск в интерфейсе MPStats хорош для одной ниши за вечер. Когда категорий много и прогон надо делать регулярно под обновляющийся бюджет — нужен API. Логика курса остаётся, меняется способ применения и пороги (см. §10.9 b-p-2026).

## Базовые настройки

| | |
|---|---|
| Базовый адрес | `https://mpstats.io/api` |
| Аутентификация | Заголовок `X-Mpstats-TOKEN: <токен>` |
| Лимит записей в ответе | До 5 000 на запрос |
| Лимит запросов | ~100 запросов/мин, при превышении — `429` |
| Дневная квота | 10 000 запросов/день на каждый из модулей `wb_external` и `ozon_external` (тариф 200, апрель 2026) |
| Тариф | Advanced Jam / Premium Jam (~7–15 тыс. ₽/мес, API открывается на Advanced и выше) |
| Документация | [docs.mpstats.io](https://docs.mpstats.io), [wiki.mpstats.io](https://wiki.mpstats.io) |

Профиль и квоту проверяем через `GET /me`. Старый `/user/check/limits` отвечает `405`.

## Insight — метод обработки данных, не endpoint

В 2026 MPStats внедрил **Insight** — закрытую технологию восстановления факта продаж по скрытым остаткам. Это **не отдельный endpoint и не отдельная подписка**: метод применяется *внутри* стандартных модулей `wb_external` / `ozon_external` к данным item-level. Сверка Тимура Товарка с WB-кабинетом за март 2026 — расхождение **0%** (источник: пост #3718 ~22.04.2026, цитируется в `sources/timur-tovarka-2026-04-29.md`).

**Прикладной вывод:** для оценки потенциала кандидата фактическая выручка берётся **не** из `revenue` категорийного запроса (это оценка ниши), а из дневного ряда `/wb/get/item/{nm_id}/sales` (Insight применён). Подробнее — в [`best-practices-2026.md` §11.2](best-practices-2026.md).

## Факт против оценки — какой endpoint что отдаёт

| Endpoint | Тип данных | Уровень | Когда брать |
|---|---|---|---|
| `POST /wb/get/category` (поле `revenue`) | **Оценка** ниши | subject / category | Скрининг массы кандидатов, шаги 1–4 рунбука |
| `POST /wb/get/category/trend` | **Оценка** | subject | Проверка падения / роста ниши |
| `GET /wb/get/item/{nm_id}/sales` | **Факт** (Insight) | карточка | Шаг 5b рунбука, окончательная оценка кандидата |
| `GET /wb/get/item/{nm_id}/by_keywords` | Факт | карточка | Сбор ключей по топ-30 для SEO |
| `GET /wb/get/item/{nm_id}/reviews` | Факт | карточка | Боли для инфографики |
| `GET /wb/get/subject/list` | Справочник | category | Спуск по дереву subject |

**Важная развилка по идентификаторам:** в ответе категорийного запроса есть два разных ID — `id` (это реальный WB nmId, по нему открывается карточка `wildberries.ru/catalog/{id}/detail.aspx`) и `itemid` (внутренний MPStats ID). Item-endpoints `/wb/get/item/{...}/sales`, `/wb/get/item/{...}/by_keywords`, `/wb/get/item/{...}/reviews` принимают **`nm_id`**, не `itemid`. Передача `itemid` отвечает `500 «SKU не найден»`. В brief.yaml храним оба, для API-вызовов используем `wb_nm_id`.

## Карта «правило плейбука 2026 → точка доступа»

Параметры порогов берутся из [`b-p-2026.md` §10.9–§10.12](best-practices-2026.md), а не дословно из курса. Курс задаёт **логику** (зачем фильтр), плейбук 2026 — **число**.

| Правило | Точка доступа | Параметр запроса |
|---|---|---|
| Топ артикулов категории по выручке (оценка) | `POST /wb/get/category` | `sortModel: [{colId: "revenue", sort: "desc"}]` |
| Целевая полка выручки конкурента под бюджет | Та же | `filterModel.revenue: {filterType: "number", type: "inRange", filter: budget*1.1, filterTo: budget*2.9}` (§10.9) |
| Окно «новинки» = 14 дней (Newbie-Boost 3.0) | Та же | `filterModel.firstAppearOn: {filterType: "date", type: "greaterThan", dateFrom: "<сегодня −14 дней>"}` (§10.1) |
| Маленькое число отзывов | Та же | `filterModel.comments: {filterType: "number", type: "lessThanOrEqual", filter: 30}` (§10.3) |
| Размер ниши 100–1000 SKU | Категорийный запрос без фильтров → `total` | (§10.12) |
| Доля топ-3 продавцов | Категорийный запрос с агрегацией по бренду / продавцу | Считается на стороне клиента (§10.8) |
| Sales/day по карточке (зелёная 3–10) | `GET /wb/get/item/{nm_id}/sales` | `d1`, `d2` — окно 30 дней; средняя по активным дням (§10.11) |
| Факт-выручка карточки | Та же | `Σ sales × final_price` за окно (Insight) |
| Тренд ниши за 6 мес | `POST /wb/get/category/trend` | `path`, `d1/d2` за 180 дней |
| Поисковые запросы по топу конкурентов | `GET /wb/get/item/{nm_id}/by_keywords` | `d1/d2` |
| Отзывы конкурента (боли) | `GET /wb/get/item/{nm_id}/reviews` | |

Для Ozon — префикс `/oz/` вместо `/wb/`. Поля частично отличаются (есть признаки склейки `parent_sku`, `sku_first`).

## Sales/day на NB-окне — нюанс

`/wb/get/item/{nm_id}/sales` отдаёт ряд по дням с полями `sales`, `final_price`, `balance`, `is_new`, `comments`. Для свежей карточки в Newbie-Boost окне (≤14 дней) средняя по календарным дням обманчива: часто половина окна идёт `balance=0` (товар ещё не подъехал) и `sales=0`. Считать **активный темп** = средняя `sales/day` по дням с `balance>0`. Пометка «NB-окно нестабильно» обязательна в `brief.yaml`, если активных дней меньше 7.

## Чистая карточка без склейки

API отдаёт это плохо:

1. Ozon — у каждой карточки проверяем `parent_sku` / `sku_first`. Если есть — склейка.
2. WB — `color_count` не отдаётся, косвенно: соотношение `start_price / final_price` >5× = подозрение на болванку, плюс `size_count`.
3. Финал — глазами по `wildberries.ru/catalog/{nm_id}/detail.aspx`.

Дисконт выручки склеек по §10.10 b-p-2026:

| Площадка | Тип | Доля выручки на ваш артикул |
|---|---|---:|
| WB | 5+ вариантов | 35–50% |
| WB | 2–4 одной модели | 60–75% |
| Ozon | одна модель | 70–85% |

## Конвейер под «Конвейер новинок» (2026)

```
РАЗВЕДКА     POST /wb/get/category  → 100–500 артикулов по subject + бюджетная полка 1.1×–2.9×
   ↓
ОТСЕВ        возраст ≤14 дней + отзывов ≤30 + тренд не падает
   ↓
ОБОГАЩЕНИЕ   GET  /wb/get/item/{nm_id}/sales         (по топ-30, окно 30 дней — Insight-факт)
             GET  /wb/get/item/{nm_id}/by_keywords   (по топ-10)
   ↓
ФАКТ-ФИЛЬТР  факт-выручка карточки в полке 1.1×–2.9× бюджета (после дисконта склейки)
             sales/day на активных днях в зелёной зоне 3–10
   ↓
РАНЖИР       потенциал = факт-выручка + lost_profit
   ↓
ОТЧЁТ        topN → человек финально оценивает в интерфейсе WB / Ozon
```

Фаза 2 «Рынок» из [phases](../tool/phases.md) работает по этому конвейеру; пошаговый план с таймингом — [`runbook-discovery-1h.md`](runbook-discovery-1h.md).

## Пример скрипта (справочный, не запускаемый)

```python
# scripts/mpstats_new_products.py — каркас фазы 2 «Рынок» под 2026
# Параметры — из b-p-2026 §10.

import os
from datetime import date, timedelta
import httpx

TOKEN = os.getenv("MPSTATS_TOKEN")
BASE = "https://mpstats.io/api"
HEADERS = {"X-Mpstats-TOKEN": TOKEN} if TOKEN else {}


def discover_new_products(
    path: str,             # subject, не корень. Пример: "Дом/Сад/Сучкорезы аккумуляторные"
    budget_rub: int,       # бюджет закупки
    nb_window_days: int = 14,
    max_reviews: int = 30,
) -> list[dict]:
    """Шаг 1–4 рунбука: разведка по subject через категорийный endpoint (оценка)."""
    today = date.today()
    cutoff = today - timedelta(days=nb_window_days)

    body = {
        "path": path,
        "startRow": 0,
        "endRow": 500,
        "sortModel": [{"colId": "revenue", "sort": "desc"}],
        "filterModel": {
            "revenue": {
                "filterType": "number",
                "type": "inRange",
                "filter": int(budget_rub * 1.1),
                "filterTo": int(budget_rub * 2.9),
            },
            "firstAppearOn": {
                "filterType": "date",
                "type": "greaterThan",
                "dateFrom": cutoff.isoformat(),
            },
            "comments": {
                "filterType": "number",
                "type": "lessThanOrEqual",
                "filter": max_reviews,
            },
        },
    }
    r = httpx.post(f"{BASE}/wb/get/category?path={path}", headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


def fact_revenue_30d(nm_id: int) -> dict:
    """Шаг 5b рунбука: факт-выручка карточки через Insight (item-level sales)."""
    d2 = date.today()
    d1 = d2 - timedelta(days=30)
    r = httpx.get(
        f"{BASE}/wb/get/item/{nm_id}/sales",
        headers=HEADERS,
        params={"d1": d1.isoformat(), "d2": d2.isoformat()},
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json()
    active = [x for x in rows if x.get("balance", 0) > 0]
    sales_total = sum(x.get("sales", 0) for x in rows)
    rev_total = sum(x.get("sales", 0) * x.get("final_price", 0) for x in rows)
    return {
        "calendar_days": len(rows),
        "active_days": len(active),
        "sales_total": sales_total,
        "revenue_30d": rev_total,
        "sales_per_active_day": (sales_total / len(active)) if active else 0,
        "nb_unstable": len(active) < 7,  # NB-окно нестабильно
    }


def check_trend_not_falling(path: str, months: int = 6) -> bool:
    d2 = date.today()
    d1 = d2 - timedelta(days=30 * months)
    body = {"path": path, "d1": d1.isoformat(), "d2": d2.isoformat()}
    r = httpx.post(f"{BASE}/wb/get/category/trend?path={path}", headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    monthly = r.json().get("revenue_by_month", [])
    if len(monthly) < 3:
        return True
    return sum(monthly[-2:]) / 2 >= sum(monthly[:2]) / 2 * 0.9


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("MPSTATS_TOKEN не задан")
    candidates = discover_new_products(
        path="Дом/Сад/Сучкорезы аккумуляторные",
        budget_rub=1_000_000,
    )
    enriched = []
    for c in candidates[:30]:
        f = fact_revenue_30d(c["id"])  # здесь именно id (= nm_id), не itemid
        enriched.append({**c, "fact": f})
    enriched.sort(key=lambda x: x["fact"]["revenue_30d"], reverse=True)
    for i, x in enumerate(enriched[:10], 1):
        f = x["fact"]
        flag = " ⚠NB" if f["nb_unstable"] else ""
        print(f"{i}. {x['name'][:40]:40} | факт30={f['revenue_30d']:>10,.0f} ₽ | "
              f"акт.дн={f['active_days']}/30 | sales/акт={f['sales_per_active_day']:.1f}{flag}")
```

Скрипт — каркас (не исполнялся в проекте). Реальный прогон по садовой нише — после ручной верификации первых вызовов.

## Альтернативы без MPStats

- **Wildbox Cerebro** — открыт всем продавцам, оценка выручки конкурентов с погрешностью до 25% (Тимур #3677). Полезен как второй источник к Insight.
- **Ozon, встроенный «Товары в поиске»** — для Ozon-части.
- **Ручная выгрузка csv** из интерфейса MPStats на одну категорию за раз.

## Чего API не заменит

- **Эстетика карточки** топ-3 — глазами.
- **Качество инфографики** — глазами.
- **Позиционирование** относительно конкурентов — читать описания.
- **Сигналы из «С этим товаром покупают»** — в API нет.
- **Склейка** — определяется плохо, см. выше.

Финальная оценка топ-10 — всегда человеком.

## Ссылки

- [Обзор API MPStats / WB / Ozon](api-limits.md) — сравнительная таблица.
- [`runbook-discovery-1h.md`](runbook-discovery-1h.md) — пошаговый план с таймингом.
- [`best-practices-2026.md`](best-practices-2026.md) §10–§13 — пороги и формулы.
- [`tool/phases.md`](../tool/phases.md) — где именно эти точки доступа вызываются.
- [`tool/methodology-checklist.md`](../tool/methodology-checklist.md) — 9 SKU-критериев + дополнительные гейты.
- [docs.mpstats.io](https://docs.mpstats.io) / [wiki.mpstats.io](https://wiki.mpstats.io) — официальная документация.
