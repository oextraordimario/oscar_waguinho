#!/usr/bin/env python3
"""Phase 2 source inspection for the Oscar Best Actor scraping project.

This script inspects the main Wikipedia page, a ceremony page, and a small
sample of actor pages to confirm selectors and edge cases before the full
scraper is implemented.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install requests and beautifulsoup4 before running this script."
    ) from exc


BEST_ACTOR_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor"
CEREMONY_URL = "https://en.wikipedia.org/wiki/96th_Academy_Awards"
SAMPLE_ACTORS = {
    "us_actor": "https://en.wikipedia.org/wiki/Adrien_Brody",
    "europe_actor": "https://en.wikipedia.org/wiki/Cillian_Murphy",
    "latino_actor": "https://en.wikipedia.org/wiki/Anthony_Quinn",
    "puerto_rico_case": "https://en.wikipedia.org/wiki/Jose_Ferrer",
    "multi_citizenship_case": "https://en.wikipedia.org/wiki/Benicio_del_Toro",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    )
}

COUNTRY_ALIASES = {
    "u.s.": "United States",
    "us": "United States",
    "united states": "United States",
    "ireland": "Ireland",
    "mexico": "Mexico",
    "puerto rico": "Puerto Rico",
}


@dataclass
class ActorInspection:
    label: str
    url: str
    short_description: str | None
    born_text: str | None
    birth_country: str | None
    citizenships: list[str]
    citizenship_present: bool
    notes: list[str]


@dataclass
class CeremonyInspection:
    url: str
    date_text: str | None
    ceremony_year: int | None


@dataclass
class MainPageInspection:
    url: str
    decade_headings: list[str]
    decade_table_count: int
    first_table_headers: list[str]
    winner_marker_found: bool
    notes: list[str]


def fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip()


def iter_infobox_rows(soup: BeautifulSoup) -> Iterable[Tag]:
    infobox = soup.select_one("table.infobox")
    if infobox is None:
        return []
    return infobox.select("tr")


def extract_infobox_field_text(soup: BeautifulSoup, field_name: str) -> str | None:
    for row in iter_infobox_rows(soup):
        header = row.find("th")
        data = row.find("td")
        if header is None or data is None:
            continue
        label = clean_text(header.get_text(" ", strip=True))
        if label == field_name:
            return clean_text(data.get_text(" ", strip=True))
    return None


def extract_infobox_field_links(soup: BeautifulSoup, field_name: str) -> list[str]:
    for row in iter_infobox_rows(soup):
        header = row.find("th")
        data = row.find("td")
        if header is None or data is None:
            continue
        label = clean_text(header.get_text(" ", strip=True))
        if label == field_name:
            values = [clean_text(link.get_text(" ", strip=True)) for link in data.find_all("a")]
            return [value for value in values if value]
    return []


def infer_birth_country(born_text: str | None) -> str | None:
    if not born_text:
        return None

    lowered = born_text.lower()
    for alias, canonical in COUNTRY_ALIASES.items():
        if alias in lowered:
            return canonical

    parts = [part.strip(" .") for part in born_text.split(",") if part.strip()]
    if not parts:
        return None

    candidate = parts[-1]
    normalized = COUNTRY_ALIASES.get(candidate.lower())
    return normalized or candidate


def inspect_actor_page(label: str, url: str) -> ActorInspection:
    soup = fetch_soup(url)
    short_description = clean_text(soup.select_one("meta[property='og:description']").get("content"))
    born_text = extract_infobox_field_text(soup, "Born")
    citizenships = extract_infobox_field_links(soup, "Citizenship")
    notes: list[str] = []

    if not born_text:
        notes.append("No infobox Born field found; fallback to lead paragraph or Wikidata is required.")
    if not citizenships:
        notes.append("No Citizenship row found; birth country becomes the deterministic classification source.")
    if "Puerto Rico" in (born_text or ""):
        notes.append("Puerto Rico appears in birth place; project rule should map this case to EUA.")
    if len(citizenships) > 1:
        notes.append("Multiple citizenships found; keep raw values and classify by birth country.")

    return ActorInspection(
        label=label,
        url=url,
        short_description=short_description,
        born_text=born_text,
        birth_country=infer_birth_country(born_text),
        citizenships=citizenships,
        citizenship_present=bool(citizenships),
        notes=notes,
    )


def inspect_ceremony_page(url: str) -> CeremonyInspection:
    soup = fetch_soup(url)
    date_text = extract_infobox_field_text(soup, "Date")
    years = [int(match) for match in re.findall(r"\b(19\d{2}|20\d{2})\b", date_text or "")]
    ceremony_year = years[-1] if years else None
    return CeremonyInspection(url=url, date_text=date_text, ceremony_year=ceremony_year)


def inspect_best_actor_page(url: str) -> MainPageInspection:
    soup = fetch_soup(url)
    content = soup.select_one("div.mw-parser-output")
    if content is None:
        raise RuntimeError("Main content not found on Best Actor page.")

    winners_header = content.find(id="Winners_and_nominees")
    if winners_header is None:
        raise RuntimeError("Winners_and_nominees section not found.")

    decade_headings: list[str] = []
    tables = []
    notes: list[str] = []
    cursor = winners_header.parent

    while cursor is not None:
        cursor = cursor.find_next_sibling()
        if cursor is None:
            break
        if cursor.name == "h2":
            break
        if cursor.name == "h3":
            heading = clean_text(cursor.get_text(" ", strip=True))
            if heading:
                decade_headings.append(heading.replace("[edit]", "").strip())
        if cursor.name == "table" and "wikitable" in (cursor.get("class") or []):
            tables.append(cursor)

    first_table_headers: list[str] = []
    if tables:
        first_header_row = tables[0].find("tr")
        if first_header_row is not None:
            first_table_headers = [
                clean_text(cell.get_text(" ", strip=True))
                for cell in first_header_row.find_all(["th", "td"])
            ]

    winner_marker_found = "Indicates the winner" in content.get_text(" ", strip=True)

    notes.append("The page uses one wikitable per decade inside the Winners and nominees section.")
    notes.append("Winner rows are marked with the symbol '?' in the Actor cell.")
    notes.append("Early ceremonies include multi-line rows, ties, and multi-film entries; normalization logic must handle this explicitly.")
    notes.append("The year column follows Academy convention and usually represents film year, not ceremony year.")

    return MainPageInspection(
        url=url,
        decade_headings=decade_headings,
        decade_table_count=len(tables),
        first_table_headers=first_table_headers,
        winner_marker_found=winner_marker_found,
        notes=notes,
    )


def build_markdown(main_page: MainPageInspection, ceremony: CeremonyInspection, actors: list[ActorInspection]) -> str:
    lines: list[str] = []
    lines.append("# Fase 2 - Mapa das Fontes")
    lines.append("")
    lines.append("## Escopo")
    lines.append("Inspecao estrutural das paginas-fonte para confirmar como extrair dados da pagina principal, das paginas dos atores e das paginas de cerimonia.")
    lines.append("")
    lines.append("## Pagina principal")
    lines.append(f"- URL: `{main_page.url}`")
    lines.append(f"- Tabelas por decada encontradas: `{main_page.decade_table_count}`")
    lines.append(f"- Cabecalhos da primeira tabela: `{', '.join(main_page.first_table_headers)}`")
    lines.append(f"- Marcador de vencedor localizado: `{main_page.winner_marker_found}`")
    lines.append(f"- Decadas detectadas: `{', '.join(main_page.decade_headings)}`")
    lines.append("- Notas:")
    for note in main_page.notes:
        lines.append(f"  - {note}")
    lines.append("")
    lines.append("## Pagina de cerimonia")
    lines.append(f"- URL: `{ceremony.url}`")
    lines.append(f"- Campo Date: `{ceremony.date_text}`")
    lines.append(f"- Ano da cerimonia inferido: `{ceremony.ceremony_year}`")
    lines.append("")
    lines.append("## Amostra de paginas de atores")
    for actor in actors:
        lines.append(f"### {actor.label}")
        lines.append(f"- URL: `{actor.url}`")
        lines.append(f"- Descricao curta: `{actor.short_description}`")
        lines.append(f"- Born: `{actor.born_text}`")
        lines.append(f"- Pais de nascimento inferido: `{actor.birth_country}`")
        lines.append(f"- Citizenship presente: `{actor.citizenship_present}`")
        lines.append(f"- Citizenship(s): `{', '.join(actor.citizenships) if actor.citizenships else ''}`")
        if actor.notes:
            lines.append("- Notas:")
            for note in actor.notes:
                lines.append(f"  - {note}")
        lines.append("")
    lines.append("## Recomendacoes para a Fase 3")
    lines.append("- Raspar a pagina principal por decada, preservando o contexto da linha para tratar multiplos filmes e empates nas primeiras cerimonias.")
    lines.append("- Tratar `ano_filme` como o valor exibido na tabela principal e `ano_cerimonia` como o ano extraido da pagina da cerimonia.")
    lines.append("- Nas paginas dos atores, usar `Born` como fonte primaria para `pais_nascimento`.")
    lines.append("- Usar `Citizenship` apenas como dado bruto complementar; nao como chave principal de classificacao.")
    lines.append("- Quando `Born` ou `Citizenship` faltarem ou vierem ambiguos, usar Wikidata como fallback e registrar isso em `fonte_classificacao`.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect source page structure for phase 2.")
    parser.add_argument("--out-md", default="docs/fase2_mapa_fontes.md")
    parser.add_argument("--out-json", default="docs/fase2_mapa_fontes.json")
    args = parser.parse_args()

    main_page = inspect_best_actor_page(BEST_ACTOR_URL)
    ceremony = inspect_ceremony_page(CEREMONY_URL)
    actors = [inspect_actor_page(label, url) for label, url in SAMPLE_ACTORS.items()]

    markdown = build_markdown(main_page, ceremony, actors)
    Path(args.out_md).write_text(markdown, encoding="utf-8", newline="\n")

    payload = {
        "main_page": asdict(main_page),
        "ceremony": asdict(ceremony),
        "actors": [asdict(actor) for actor in actors],
    }
    Path(args.out_json).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
