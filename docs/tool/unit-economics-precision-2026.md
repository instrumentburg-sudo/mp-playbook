# Точная юнит-экономика 2026: цена, рынок, кабинет

Цель документа — считать не «примерную маржу», а решение по SKU: какую цену ставить,
какой запас до рынка есть, где мы сравниваемся с конкурентами и какие допущения делают
расчёт хрупким.

## 1. Что считаем

Для каждого SKU считаем не одну строку, а матрицу:

| Срез | Что означает | Источник |
|---|---|---|
| `cabinet_price` | наша текущая цена в кабинете, если карточка уже заведена | WB `api/v2/list/goods/filter`, Ozon `v5/product/info/prices` |
| `buyer_price` | цена, которую видит/платит покупатель | WB `discountedPrice` / `clubDiscountedPrice`; Ozon `marketing_seller_price`; для новых SKU — рекомендованная цена |
| `supplier_cost` | себестоимость закупки | прайс KQ с партнёрской скидкой |
| `market_price` | цены конкурентов в нише | MPStats category top-500: p25 / median / p75 |
| `green_floor` | минимальная цена, где маржа проходит порог | `mp-trade/monitoring/unit_economy.py` |
| `chosen_price` | цена запуска/изменения | психологически округлённая цена не ниже `green_floor` |

Ключевой принцип: `cabinet_price` и `buyer_price` не смешиваются. На WB продавец может
видеть одну цену до скидки, покупатель — цену со скидкой или цену Кошелька. На Ozon
ориентир для покупателя — `marketing_seller_price`.

## 2. Лестница точности

| Класс | Когда ставим | Можно ли принимать закупочное решение |
|---|---|---|
| A | карточка есть в кабинете, ставки/цены взяты live, габариты известны | да, после проверки конкурентных карточек |
| B | live-тарифы есть, но карточки или габариты неполные | можно только для shortlist |
| C | карточки нет в кабинете, габариты/ставки частично модельные | только скрининг, закупку не подтверждает |

Если класс C показывает STOP — это почти всегда настоящий STOP. Если класс C показывает GO,
его надо поднять до A/B: завести карточку/получить точные габариты/проверить тариф в ЛК.

## 3. Источники данных по приоритету

1. Прайс поставщика: `price`, `discount_cost`, остаток, эффективный себес.
2. Карточка в кабинете:
   - Ozon Seller API `v5/product/info/prices`: `marketing_seller_price`, `min_price`,
     `sales_percent_fbo/fbs`, `acquiring`, `fbo_*`, `fbs_*`.
   - WB Discounts & Prices API `api/v2/list/goods/filter`: `vendorCode`, `nmID`, `price`,
     `discountedPrice`, `clubDiscountedPrice`, `discount`.
3. Тарифы площадок:
   - WB: тариф коробов, комиссия по предмету, коэффициенты складов.
   - Ozon: live-поля `ProductInfoPrices`; если карточки нет — модель с пометкой.
4. MPStats:
   - category top-500 — быстрый коридор ниши;
   - item-level sales — обязательный факт по 2-3 финальным конкурентам.
5. Ручной факт:
   - точные габариты упаковки;
   - КГТ/КГТ+;
   - сертификаты, декларации, гарантийная нагрузка;
   - рекламная ставка в категории.

## 4. Формула одной цены

На каждую цену-кандидат:

```text
profit =
  buyer_price
  - supplier_cost
  - packaging_and_delivery_to_mp
  - marketplace_commission
  - acquiring
  - client_logistics
  - return_logistics_by_redemption
  - fbo_storage_and_acceptance
  - ads_drr
  - defect_reserve
  - tax
  - marketplace_specific_fees
```

Маржа = `profit / buyer_price`. Рентабельность к себесу = `profit / supplier_cost`.

Зелёная цена должна пройти оба пола:

```text
margin >= 15%
buyer_price >= supplier_cost * 1.40
```

Жёлтая зона 5-15% годится только как гипотеза для карточки с понятным СПП/акцией и
быстрым оборотом. Для закупки партии это не зелёный свет.

## 5. Как выбираем цену

1. Считаем `green_floor` по четырём связкам: WB FBS, WB FBO, Ozon FBS, Ozon FBO.
2. Берём связку с минимальной зелёной наценкой, если она не ломает рынок.
3. `chosen_price` = ближайшая психологическая цена не ниже `green_floor`
   (`5 684 -> 5 690`, `17 861 -> 17 890`).
4. Сравниваем `chosen_price` с MPStats:
   - `<= p50` — нормальная цена запуска;
   - `p50..p75` — можно запускать, но нужна сильная карточка/комплект/рейтинг;
   - `> p75` — STOP market, если нет явного премиального отличия;
   - `> p75 * 1.15` — стоп до пересмотра себеса или комплектации.
5. Проверяем `cabinet_price`:
   - если текущая цена ниже `green_floor`, карточка продаёт маржу;
   - если выше `p75`, карточка требует доказательства конверсией;
   - если `min_price` Ozon выше зелёной цены, нельзя опускаться ниже пола акции.

## 6. Что выводить в визуальный отчёт

Минимальный набор для каждого SKU:

| Блок | Что показывать |
|---|---|
| Шапка | SKU, тип, остаток, себес, вердикт, класс точности |
| Кабинет | WB цена до скидки / цена покупателю / club; Ozon buyer price / min price |
| Рынок | WB и Ozon p25 / median / p75, маркер нашей цены |
| Цена | `green_floor`, `chosen_price`, лучшая связка, маржа, прибыль |
| Затраты | себес, комиссия, логистика, реклама, налог, прочее, прибыль в процентах от цены |
| Риск | live/не live, габариты-инференс, КГТ-риск, item-level MPStats не добран |

В `mp-trade` текущий артефакт:

- [визуальный отчёт садовых SKU](../../assets/reports/2026-05-12/garden-unit-economy-visual.html)
- [JSON для автоматизации](../../assets/reports/2026-05-12/garden-unit-economy-visual.json)
- [markdown-сводка](../../assets/reports/2026-05-12/garden-unit-economy-mpstats.md)

## 7. Обязательные стопы

STOP до закупки:

- карточка класса C показывает GO, но нет точных габаритов;
- `chosen_price > p75 * 1.15`;
- товар может попасть в КГТ+/Ozon >190 л, а коробка не подтверждена;
- у конкурентов p25/median держатся за счёт склеек или другого комплекта;
- MPStats category показывает спрос, но item-level конкурентов не подтверждает продажи;
- текущая кабинетная комиссия/логистика отличается от модели больше чем на 5 п.п. цены.

## 8. Команды

```bash
cd /home/iamsohappy/projects/mp-trade
set -a && source .env && source ../mp-playbook/.env && set +a
uv run python scripts/snapshot_ozon_tariffs.py
uv run python scripts/snapshot_wb_tariffs.py
uv run python scripts/garden_unit_economy_report.py
```

Проверка:

```bash
uv run pytest tests/test_unit_economy.py tests/test_ozon_tariffs_snapshot.py tests/test_wb_tariffs_snapshot.py
uv run ruff check --select F,E9,B,E501,N monitoring/unit_economy.py scripts/unit_economy_report.py scripts/garden_unit_economy_report.py tests/test_unit_economy.py
```

## 9. Источники

- Ozon Seller API: `https://docs.ozon.ru/api/seller/`, метод `v5/product/info/prices`.
- Wildberries API: `https://dev.wildberries.ru/docs/openapi/work-with-products`,
  раздел Discounts & Prices.
- MPStats API: `docs/updates/mpstats-api-catalog.md`.
- Актуальные правки 2026: `docs/updates/best-practices-2026.md`.
