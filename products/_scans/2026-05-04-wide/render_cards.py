"""Собирает компактную HTML-сетку карточек по 21+ кандидатам из raw/*.json."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "raw"

GROUPS = [
    {
        "title": "Wildberries · Насосы — 🟢 две основные идеи",
        "platform": "wb",
        "ids": [
            ("967198645", "garden_nasosy", "🟢 ОСНОВНАЯ", "ВИХРЬ скв. — упущ. прибыль БОЛЬШЕ выручки (810К/708К)"),
            ("846822394", "garden_nasosy", "🟢 ИДЕЯ", "Джилекс водомёт — остатков на 6 дней"),
        ],
    },
    {
        "title": "Wildberries · Триммеры — 4 живых",
        "platform": "wb",
        "ids": [
            ("924534235", "garden_trimmery", "🟡 РЕЗЕРВ", "HUTER GGT-52 бензо — рынок насыщен (lost 78К)"),
            ("767120349", "garden_trimmery", "🟡 РЕЗЕРВ", "HUTER GET-LS45 электро — аналогично"),
            ("945646115", "garden_trimmery", "❌", "Oasis — оборачиваемость 202 дня"),
            ("918413648", "garden_trimmery", "❌", "TESFE — оборачиваемость 177 дн + псевдо-бренд"),
        ],
    },
    {
        "title": "Wildberries · Расходка / ручной — 2 живых",
        "platform": "wb",
        "ids": [
            ("967675632", "ruchnoy_otvertka", "🟢 ИДЕЯ", "Электроотвёртка SMART — упущ. прибыль 88% выручки"),
            ("930713387", "rashodka_tsep_pily", "🟡 РЕЗЕРВ", "Цепь HUTER — низкая упущенная прибыль"),
            ("792999506", "rashodka_koronka", "⚠ ПЕРЕПРОВЕРИТЬ", "Алмазная коронка — карточке всего 5 дней"),
        ],
    },
    {
        "title": "Wildberries · Сумки строительные — 4 карточки одного продавца (свежая ниша)",
        "platform": "wb",
        "ids": [
            ("917763039", "akses_sumka", "🟢 ИДЕЯ", "MrFixit, упущ. прибыль = выручке"),
            ("917896171", "akses_sumka", "🟢 ИДЕЯ", "MrFixit, аналог в серии"),
            ("917785287", "akses_sumka", "🟢 ИДЕЯ", "MrFixit с пластиковым дном"),
            ("913399867", "akses_sumka", "🟢 ИДЕЯ", "MrFixit, нижний сегмент"),
        ],
    },
    {
        "title": "Озон · Культиваторы АКБ — 🟢 главная находка скана",
        "platform": "oz",
        "ids": [
            ("3960730994", "oz_garden_motobloki", "🟢 ОСНОВНАЯ", "ТОЧКА КУЛЬТУРЫ — упущ. прибыль 1,53 млн ₽ (150% выручки!)"),
            ("3813116094", "oz_garden_motobloki", "🟢 ИДЕЯ", "Маривойс — выручка 1 млн, остатков на 1 день"),
            ("3958109682", "oz_garden_motobloki", "🟢 ИДЕЯ", "Маккензи Премиум — упущ. прибыль = выручке"),
        ],
    },
    {
        "title": "Озон · Цепные пилы АКБ — 3 живых",
        "platform": "oz",
        "ids": [
            ("3857802055", "oz_garden_pily_tsep", "🟢 ИДЕЯ", "Metax&Thng — остатков на 0,15 дня"),
            ("3814420993", "oz_garden_pily_tsep", "🟢 ИДЕЯ", "AMF-GROUP бесщёточная — lost 347К ₽"),
            ("3849801875", "oz_garden_pily_tsep", "⚠ ПЕРЕПРОВЕРИТЬ", "SawWoW — 5 дней с продажами (пиковые партии)"),
        ],
    },
    {
        "title": "Озон · Триммеры АКБ — 3 живых",
        "platform": "oz",
        "ids": [
            ("3880544441", "oz_garden_trimmery", "🟢 ИДЕЯ", "BEKMI — упущ. прибыль 88% выручки"),
            ("3762941042", "oz_garden_trimmery", "🟢 ИДЕЯ", "Без бренда — фабричная карточка с 2 АКБ"),
            ("3757208550", "oz_garden_trimmery", "🟡 РЕЗЕРВ", "Larbor — низкая упущ. прибыль (20%)"),
        ],
    },
    {
        "title": "Озон · Прочее — 1 резерв",
        "platform": "oz",
        "ids": [
            ("3812920444", "oz_ruchnoy_klyuchi_otvertki", "🟡 РЕЗЕРВ", "ZAР ударные головки 1/2 — рынок насыщен"),
        ],
    },
]


def fmt_money(n: float | None) -> str:
    if n is None or n == 0:
        return "—"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}&nbsp;млн&nbsp;₽".replace(".", ",")
    if n >= 1000:
        return f"{n/1000:.0f}&nbsp;тыс.&nbsp;₽"
    return f"{int(n)}&nbsp;₽"


def fmt_int(n: int) -> str:
    return f"{int(n):_}".replace("_", "&nbsp;")


def find_item(file_slug: str, item_id: str) -> dict | None:
    path = RAW / f"{file_slug}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    for row in data.get("data", []):
        if str(row.get("id")) == item_id:
            return row
    return None


def render_card(item_id: str, file_slug: str, verdict: str, hint: str, platform: str) -> str:
    row = find_item(file_slug, item_id)
    if not row:
        return f'<article class="card"><div class="card-error">Артикул {item_id} не найден в {file_slug}</div></article>'

    name = (row.get("name") or "").replace('"', "&quot;")[:80]
    brand = row.get("brand") or "—"
    seller = row.get("seller") or "—"
    price = row.get("final_price") or 0
    revenue = row.get("revenue") or 0
    lost = row.get("lost_profit") or 0
    days_in_site = row.get("days_in_site") or 0
    days_with_sales = row.get("days_with_sales") or 0
    comments = row.get("comments") or 0
    turnover = row.get("turnover_days") if platform == "wb" else row.get("turnover")
    sales = row.get("sales") or 0
    balance = row.get("balance") or 0
    rating = row.get("rating") or 0

    thumb = row.get("thumb_middle") or row.get("thumb") or ""
    if thumb.startswith("//"):
        thumb = "https:" + thumb

    if platform == "wb":
        link = f"https://www.wildberries.ru/catalog/{item_id}/detail.aspx"
        platform_label = "WB"
    else:
        link = f"https://www.ozon.ru/product/{item_id}/"
        platform_label = "Озон"

    if turnover is None or turnover == "?" or turnover == 0:
        turnover_txt = "—"
    else:
        try:
            t = float(turnover)
            turnover_txt = f"{t:.1f} дн" if t < 100 else f"{int(t)} дн"
        except (TypeError, ValueError):
            turnover_txt = str(turnover)

    verdict_class = "v-main" if "ОСНОВНАЯ" in verdict else \
                    "v-idea" if "ИДЕЯ" in verdict else \
                    "v-reserve" if "РЕЗЕРВ" in verdict else \
                    "v-recheck" if "ПЕРЕПРОВЕРИТЬ" in verdict else \
                    "v-reject"
    rating_str = f"{rating:.1f}".rstrip("0").rstrip(".") if rating else "—"
    return f'''<article class="card {verdict_class}">
  <a class="card-img" href="{link}" target="_blank" rel="noopener">
    <img src="{thumb}" alt="{name}" loading="lazy">
  </a>
  <div class="card-badge">{verdict} · {platform_label}</div>
  <div class="card-name">{name}</div>
  <div class="card-hint">{hint}</div>
  <dl class="card-meta">
    <dt>Бренд</dt><dd>{brand}</dd>
    <dt>Цена</dt><dd>{fmt_int(price)}&nbsp;₽</dd>
    <dt>Выручка / мес</dt><dd><b>{fmt_money(revenue)}</b></dd>
    <dt>Упущ. прибыль</dt><dd><b>{fmt_money(lost)}</b></dd>
    <dt>Продаж за 30 дн</dt><dd>{fmt_int(sales)}&nbsp;шт</dd>
    <dt>Остаток</dt><dd>{fmt_int(balance)}&nbsp;шт</dd>
    <dt>Оборот</dt><dd>{turnover_txt}</dd>
    <dt>Возраст карточки</dt><dd>{days_in_site}&nbsp;дн</dd>
    <dt>Отзывы / рейтинг</dt><dd>{comments} / {rating_str}</dd>
    <dt>Дней с продажами</dt><dd>{days_with_sales} из 30</dd>
  </dl>
  <a class="card-link" href="{link}" target="_blank" rel="noopener">Открыть на {platform_label} →</a>
</article>'''


def render() -> str:
    parts = ['''<style>
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin: 16px 0 28px; }
.card { background: #fff; border: 1px solid #e6e6e6; border-radius: 8px; padding: 12px; font-size: 13px; line-height: 1.35; display: flex; flex-direction: column; border-top-width: 4px; }
.card.v-main { border-top-color: #2a6f2a; }
.card.v-idea { border-top-color: #4caf50; }
.card.v-reserve { border-top-color: #f9a825; }
.card.v-recheck { border-top-color: #ff7043; }
.card.v-reject { border-top-color: #c62828; opacity: 0.7; }
.card-img { display:block; width:100%; aspect-ratio: 3 / 4; overflow:hidden; border-radius:6px; margin-bottom:8px; background:#f5f5f5; }
.card-img img { width:100%; height:100%; object-fit:cover; display:block; }
.card-badge { font-size: 11px; font-weight: 600; color: #555; margin-bottom: 4px; letter-spacing: 0.02em; }
.card-name { font-weight: 600; font-size: 13px; line-height: 1.3; margin-bottom: 4px; min-height: 34px; }
.card-hint { color: #666; font-size: 11px; line-height: 1.35; margin-bottom: 8px; min-height: 30px; }
.card-meta { display: grid; grid-template-columns: auto 1fr; gap: 2px 8px; margin: 0 0 10px; font-size: 12px; }
.card-meta dt { color: #888; margin: 0; }
.card-meta dd { margin: 0; text-align: right; }
.card-meta dd b { color: #2a6f2a; }
.card-link { margin-top: auto; font-size: 12px; color: #1a73e8; text-decoration: none; padding-top: 6px; border-top: 1px solid #f0f0f0; }
.card-link:hover { text-decoration: underline; }
.card-error { color: #aa2222; }
.scan-group { margin: 28px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #1a73e8; font-size: 16px; font-weight: 600; }
</style>
''']
    for group in GROUPS:
        parts.append(f'<h3 class="scan-group">{group["title"]}</h3>')
        parts.append('<div class="card-grid">')
        for item_id, file_slug, verdict, hint in group["ids"]:
            parts.append(render_card(item_id, file_slug, verdict, hint, group["platform"]))
        parts.append('</div>')
    return "\n".join(parts)


if __name__ == "__main__":
    out = render()
    Path(ROOT / "cards.html").write_text(out)
    print(f"OK, {len(out)} chars → cards.html")
