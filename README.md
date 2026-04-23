# mp-playbook

Методичка и дизайн инструмента «Конвейер новинок» для Wildberries и Ozon. Собрана из курса (извлечение через NotebookLM) и обогащена актуальными данными на 23 апреля 2026.

**Сайт**: https://instrumentburg-sudo.github.io/mp-playbook/

## Структура

```
docs/
├── index.md                    # главная
├── course/                     # извлечение курса (5 разделов)
│   ├── 01-methodology.md
│   ├── 02-product-search.md
│   ├── 03-unit-economics.md
│   ├── 04-seo-card.md
│   └── 05-launch-ads.md
├── updates/                    # правки 2026
│   ├── best-practices-2026.md
│   └── api-limits.md
└── tool/                       # дизайн инструмента
    ├── design.md
    ├── decisions.md
    └── phases.md
```

## Локально

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install mkdocs-material mkdocs-glightbox mkdocs-awesome-pages-plugin
mkdocs serve        # http://127.0.0.1:8000
mkdocs build        # в site/
```

## Деплой

GitHub Actions собирает MkDocs на push в `main` и пушит в ветку `gh-pages`.

## Обновления

Это живой документ. Правки через PR. Ключевые решения — в `docs/tool/decisions.md`.
