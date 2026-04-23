# API: лимиты и возможности WB / Ozon / MPStats

Сводка на 23.04.2026. Инструмент конвейера новинок опирается на три источника: **MPStats API** (рыночная аналитика до запуска), **WB Content/Statistics API** и **Ozon Seller API** (свои данные после запуска).

## 1. Сравнительная таблица

| | MPStats API | Wildberries API | Ozon Seller API |
|---|---|---|---|
| Чьи данные | рынок целиком (конкуренты, ниши) | только свой ЛК | только свой ЛК |
| Цена | от ~7 000 ₽/мес (Advanced/Premium) | бесплатно | бесплатно |
| Нужен ЛК селлера | нет | **да** (API-ключ из WB Seller) | **да** (Client ID + API Key) |
| Общий rate limit | ~100 req/min | 3 req / 30 sec на метод | 30 000 операций / мин |
| Где нужен в пайплайне | **фазы 1–2**: идея, анализ ниши | **фазы 6–8**: запуск и скейл | **фазы 6–8**: запуск и скейл |

## 2. MPStats API

**Документация**: [mpstats.io/api](https://mpstats.io/api), [docs.mpstats.io](https://docs.mpstats.io).

Ключевые эндпоинты для пайплайна:

- **Category** — анализ категории: топ-продавцов, распределение выручки, новые карточки.
- **Keywords** — частотность запросов, сезонность, связанные ключи.
- **SKU** — детальные метрики карточки (выручка, остатки, упущенная).
- **Search** — поиск по фото, названию, артикулу.
- **Trends** — динамика ниши по месяцам.

**Тариф с API**: Advanced Jam / Premium Jam — обычно 7 000–15 000 ₽/мес. Уточнять у менеджера, т.к. тарифный конструктор меняется.

**Как использовать в MVP**:
1. `calc-niche-potential.py` — принимает категорию + бюджет → возвращает топ-20 SKU по выручке с новизной <90 дней и отзывами <50.
2. `fetch-seo-semantics.py` — по артикулам конкурентов собирает SEO-ядро (с отсечением НЧ <1000 и латиницы).

## 3. Wildberries API

**Домены**:
- `suppliers-api.wildberries.ru` — общий endpoint.
- `openapi.wildberries.ru` — документация Swagger.
- `dev.wildberries.ru` — release-notes и FAQ.

**Основные разделы**:

| Раздел | Для чего | Лимит |
|---|---|---|
| `/content` | Карточки товаров: создание, обновление, медиа | 3 req / 30 sec |
| `/statistics` | Свои продажи, заказы, остатки, возвраты | 3 req / 30 sec |
| `/analytics` | Расширенная аналитика, детализация продаж | 1 req/min, 30 строк (100 на Advanced) |
| `/promotion` | Рекламные кампании: создание, ставки, отчёты | 3 req / 30 sec |
| `/reports` | Финансовые отчёты, акты, детализация выплат | 1 req/min |
| `/warehouses` (новый, 23.03.26) | Инвентаризация склада | 1 req / 20 sec, 250 000 строк |

**API-ключ**: кабинет WB Seller → Настройки → Доступ к API → генерация токена. Токен привязан к JWT, срок 180 дней (в 2026 планируют продление).

**Скоупы**: Content, Statistics, Analytics, Promotion, Recommendations, Feedbacks, Marketplace, Buyer, Return, Calendar. Каждому — отдельный бит.

**Частые сценарии**:
- Пулл продаж за период: `/api/v1/supplier/sales?dateFrom=...` (1 req/min).
- Обновление остатков FBS: `/api/v3/stocks/{warehouseId}` (3 req/30 sec).
- Массовое создание карточек: `/content/v2/cards/upload` — порциями по 3 000 карточек, `taskId` для проверки статуса.

## 4. Ozon Seller API

**Домен**: `api-seller.ozon.ru`.
**Документация**: [docs.ozon.ru/api/seller](https://docs.ozon.ru/api/seller/).

**Авторизация**: два заголовка — `Client-Id` и `Api-Key`. Получить: кабинет Ozon Seller → Настройки → API.

**Общий лимит** (с 24.02.2026): **30 000 операций с товарами в минуту**. При превышении — `429 Too Many Requests` с `Retry-After: <sec>` и `Remaining: <items>`.

**Важно**: если в одном запросе превышено число товаров — весь запрос режектится, ни одно обновление не проходит. Пример: `limit=1000`, а осталось `500` → `429`, и всё. Бить на батчи вручную.

**Основные эндпоинты** (актуально на апрель 2026):

| Путь | Для чего |
|---|---|
| `/v3/product/list` | Список товаров (с фильтрами) |
| `/v3/product/info/list` | Детали по списку product_id |
| `/v1/product/pictures/import` | Загрузка изображений |
| `/v3/posting/fbs/list` | Заказы FBS (с 06.04.26 добавлен `Tarification_steps`) |
| `/v2/posting/fbo/list` | Заказы FBO |
| `/v1/analytics/data` | Аналитика: показы, клики, заказы, выручка |
| `/v1/finance/transaction/list/v3` | Финансовые транзакции |
| `/v1/finance/realization` | Отчёт о реализации |
| `/v1/review/list` | Отзывы |

**С 07.04.2026** устарели старые FBS/rFBS методы работы с заказами и остатками — проверять миграцию на v3.

**Performance API** (для продавцов РФ, с 06.04.2026) получил OAuth. Нужен для управления рекламой:
- `/api/client/campaign` — кампании (Трафареты, Продвижение в поиске, Баннеры).
- `/api/client/statistics` — отчёты по РК.

## 5. Связка: как данные текут через пайплайн

```
 Фаза 1 IDEA       ─┐
 Фаза 2 MARKET     ─┼─► MPStats API (чужой рынок)
 Фаза 3 SUPPLIER   ─┘       │
                            ▼
                      Гейт UNIT-ECO
                            │
                            ▼
 Фаза 4 UNIT-ECO  ◄─ локальный расчёт (commissions/*.yaml + свои формулы)
 Фаза 5 BUY       ◄─ вручную (1688, логистика, таможня)
                            │
                            ▼
 Фаза 6 CARD      ◄─ WB Content API / Ozon Product API (загрузка карточек)
 Фаза 7 LAUNCH    ◄─ WB Statistics + Promotion / Ozon Analytics + Performance
 Фаза 8 SCALE     ◄─ всё то же, ежедневный пулл в sales-log.csv
```

## 6. Чего **нет** в API

- **1688.com**: публичного стабильного API нет. Работа через UI + поиск по фото, либо посредник/CDP-скрейпинг. AliBaba International имеет API, но ассортимент и цены хуже.
- **Честный знак** (маркировка): отдельный API, нужен только для маркируемых категорий (одежда, обувь, парфюм и т.д.).
- **Таможня ФТС**: оформление ДТ через брокера, не через API.
- **Сертификация ЕАЭС**: реестр Росаккредитации читается, но процесс заявки — через аккредитованную лабораторию.

## 7. Ссылки

- [WB OpenAPI](https://openapi.wildberries.ru/)
- [WB API Release notes](https://dev.wildberries.ru/en/release-notes)
- [Ozon Seller API docs](https://docs.ozon.ru/api/seller/)
- [Ozon API Limits — февраль 2026](https://avoshop.ru/company/news/2026/limity_api_ozon_s_24_fevralya_2026_goda/)
- [MPStats tariffs](https://mpstats.io/price)
