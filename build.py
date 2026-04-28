"""Build mp-playbook static site. No frameworks. Python + Jinja + markdown."""
from __future__ import annotations
import re
import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "site"

BASE_URL = "/mp-playbook"

NAV = [
    {
        "section": "Введение",
        "number": "00",
        "pages": [{"title": "Главная", "path": "index.md", "slug": "", "kicker": "Старт"}],
    },
    {
        "section": "Курс — конвейер новинок",
        "number": "01",
        "pages": [
            {"title": "Методология", "path": "course/01-methodology.md", "slug": "course/methodology", "kicker": "I"},
            {"title": "Выбор товара и 1688", "path": "course/02-product-search.md", "slug": "course/product-search", "kicker": "II"},
            {"title": "Юнит-экономика", "path": "course/03-unit-economics.md", "slug": "course/unit-economics", "kicker": "III"},
            {"title": "SEO и карточка", "path": "course/04-seo-card.md", "slug": "course/seo-card", "kicker": "IV"},
            {"title": "Запуск и реклама", "path": "course/05-launch-ads.md", "slug": "course/launch-ads", "kicker": "V"},
        ],
    },
    {
        "section": "Обновления 2026",
        "number": "02",
        "pages": [
            {"title": "Best practices апр'26", "path": "updates/best-practices-2026.md", "slug": "updates/best-practices", "kicker": "Δ"},
            {"title": "Runbook · 1 час", "path": "updates/runbook-discovery-1h.md", "slug": "updates/runbook-discovery-1h", "kicker": "⏱"},
            {"title": "API · WB / Ozon / MPStats", "path": "updates/api-limits.md", "slug": "updates/api-limits", "kicker": "API"},
            {"title": "MPStats API каталог", "path": "updates/mpstats-api-catalog.md", "slug": "updates/mpstats-api-catalog", "kicker": "⌬"},
            {"title": "Источник · дип-ресёрч 2026-04-28", "path": "updates/sources/deep-research-2026-04-28.md", "slug": "updates/sources/deep-research-2026-04-28", "kicker": "✦"},
        ],
    },
    {
        "section": "Сканы",
        "number": "03",
        "pages": [
            {"title": "Пилот · 2026-04-27", "path": "scans/2026-04-27-pilot.md", "slug": "scans/2026-04-27-pilot", "kicker": "⊙"},
        ],
    },
    {
        "section": "Инструмент",
        "number": "04",
        "pages": [
            {"title": "Дизайн инструмента", "path": "tool/design.md", "slug": "tool/design", "kicker": "⊕"},
            {"title": "Принятые решения", "path": "tool/decisions.md", "slug": "tool/decisions", "kicker": "⊢"},
            {"title": "Фазы и гейты", "path": "tool/phases.md", "slug": "tool/phases", "kicker": "⤿"},
            {"title": "Чек-лист методологии", "path": "tool/methodology-checklist.md", "slug": "tool/methodology-checklist", "kicker": "✓"},
            {"title": "Бюджет и цикл денег", "path": "tool/budget-cycle.md", "slug": "tool/budget-cycle", "kicker": "₽"},
        ],
    },
]


def build_md() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=[
            "extra", "admonition", "toc", "tables", "footnotes",
            "sane_lists", "attr_list", "fenced_code", "def_list", "codehilite",
        ],
        extension_configs={
            "codehilite": {"css_class": "hl", "guess_lang": False, "noclasses": False},
            "toc": {"permalink": False, "toc_depth": "2-3"},
        },
    )


def render_internal_links(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)
        # relative links inside docs: map to routes
        target = href.rstrip("/").removesuffix(".md")
        # handle relative ../ and ./ prefixes
        target = re.sub(r"^\./", "", target)
        for section in NAV:
            for page in section["pages"]:
                if page["path"].endswith(href) or page["path"].removesuffix(".md") == target:
                    return f'href="{BASE_URL}/{page["slug"]}/"' if page["slug"] else f'href="{BASE_URL}/"'
        return match.group(0)

    return re.sub(r'href="([^"]+)"', repl, html)


def render_site() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(STATIC, OUT / "assets", dirs_exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(enabled_extensions=("html",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("page.html")
    total = 0
    for section in NAV:
        for page in section["pages"]:
            src = DOCS / page["path"]
            if not src.exists():
                print(f"SKIP (missing): {page['path']}")
                continue
            md = build_md()
            raw = src.read_text(encoding="utf-8")
            first_h1 = re.search(r"^# (.+)$", raw, re.M)
            title = first_h1.group(1) if first_h1 else page["title"]
            body_md = re.sub(r"^# .+\n?", "", raw, count=1, flags=re.M)
            # Home page: keep hero only, no title duplication
            if page["slug"] == "":
                title = "Конвейер новинок · методичка WB / Ozon"
            body_html = md.convert(body_md)
            body_html = render_internal_links(body_html)
            toc_html = md.toc if md.toc.strip() != '<div class="toc"><ul></ul></div>' else ""

            out_dir = OUT if not page["slug"] else OUT / page["slug"]
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "index.html"

            html = template.render(
                base_url=BASE_URL,
                title=title,
                page_title=page["title"],
                kicker=page["kicker"],
                body=body_html,
                toc=toc_html,
                nav=NAV,
                current_slug=page["slug"],
                current_section=section["section"],
                section_number=section["number"],
                is_home=(page["slug"] == ""),
            )
            out_path.write_text(html, encoding="utf-8")
            total += 1
            print(f"built: {out_path.relative_to(ROOT)}")
    print(f"\n✓ {total} pages built → {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    render_site()
