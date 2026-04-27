# products/

Каждый кандидат в новинку живёт в своей подпапке. Цикл папки = цикл фазы из `docs/tool/phases.md`.

## Нэйминг

До получения SKU на WB:
```
products/2026-04-001-shurupovert-12v-kompakt/
```
Формат: `YYYY-MM-NNN-slug`, где `NNN` — сквозной счётчик внутри месяца, `slug` — короткое kebab-case имя ниши.

После публикации карточки (фаза 6 CARD) — папка переименовывается в реальный SKU:
```
products/892-1-shurupovert-12v/
```

## Артефакты по фазам

| Фаза | Файл |
|---|---|
| 1 IDEA | `brief.yaml` |
| 2 MARKET | `market.yaml` + `competitors-top30.csv` |
| 3 SUPPLIER | `supplier.yaml` |
| 4 UNIT-ECO | `unit.yaml` |
| 5 BUY | `buy-log.yaml` |
| 6 CARD | `card.yaml` |
| 7 LAUNCH | `launch.yaml` + `sales-log.csv` |
| 8 SCALE/KILL | `decision.yaml` |

Шаблоны лежат в `_template/`, копируются как стартовая точка.
