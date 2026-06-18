#!/usr/bin/env python3
"""Phase 3 base-list extraction for the Oscar Best Actor scraping project.

This script fetches the main Wikipedia page for Academy Award for Best Actor,
parses the "Winners and nominees" tables, normalizes rowspans, and exports a
base dataset with actor, film, ceremony, and winner metadata.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install requests and beautifulsoup4 before running this script."
    ) from exc


BASE_URL = "https://en.wikipedia.org"
BEST_ACTOR_URL = f"{BASE_URL}/wiki/Academy_Award_for_Best_Actor"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    )
}
WINNER_MARKERS = {"\u2021", "\u00a7"}
ACADEMY_AWARDS_LINK_RE = re.compile(r"/wiki/\d+(?:st|nd|rd|th)_Academy_Awards")
YEAR_RE = re.compile(r"(19\d{2}|20\d{2})")
CEREMONY_NUMBER_RE = re.compile(r"(\d+)(?:st|nd|rd|th)")


@dataclass
class TableCell:
    text: str
    links: list[dict[str, str]]


@dataclass
class NomineeRow:
    decade: str
    ano_filme_raw: str | None
    ano_filme: int | None
    numero_cerimonia: int | None
    nome_ator: str | None
    filme_indicado: str | None
    role_raw: str | None
    url_ator: str | None
    url_filme: str | None
    url_cerimonia: str | None
    eh_vencedor: bool
    ceremony_label_raw: str | None


def fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\[[^\]]+\]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip() or None


def absolute_url(href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(BASE_URL, href)


def extract_cell(cell: Tag) -> TableCell:
    links: list[dict[str, str]] = []
    for link in cell.find_all("a"):
        href = link.get("href")
        if not href or href.startswith("#"):
            continue
        links.append(
            {
                "href": absolute_url(href) or "",
                "text": clean_text(link.get_text(" ", strip=True)) or "",
            }
        )
    return TableCell(
        text=clean_text(cell.get_text(" ", strip=True)) or "",
        links=links,
    )


def ensure_row(grid: list[list[TableCell | None]], row_index: int, width: int) -> None:
    while len(grid) <= row_index:
        grid.append([])
    while len(grid[row_index]) <= width:
        grid[row_index].append(None)


def expand_table(table: Tag) -> list[list[TableCell | None]]:
    grid: list[list[TableCell | None]] = []
    rows = table.find_all("tr")

    for row_index, row in enumerate(rows):
        ensure_row(grid, row_index, 0)
        col_index = 0
        for html_cell in row.find_all(["th", "td"], recursive=False):
            while col_index < len(grid[row_index]) and grid[row_index][col_index] is not None:
                col_index += 1

            cell = extract_cell(html_cell)
            rowspan = int(html_cell.get("rowspan", 1))
            colspan = int(html_cell.get("colspan", 1))

            for row_offset in range(rowspan):
                target_row = row_index + row_offset
                ensure_row(grid, target_row, col_index + colspan - 1)
                for col_offset in range(colspan):
                    grid[target_row][col_index + col_offset] = cell
            col_index += colspan

    width = max(len(row) for row in grid)
    for row in grid:
        while len(row) < width:
            row.append(None)
    return grid


def iter_winners_tables(soup: BeautifulSoup) -> Iterable[tuple[str, Tag]]:
    content = soup.select_one("#mw-content-text .mw-parser-output")
    if content is None:
        raise RuntimeError("Main content not found on Best Actor page.")

    winners_header = content.find(id="Winners_and_nominees")
    if winners_header is None or winners_header.parent is None:
        raise RuntimeError("Winners_and_nominees section not found.")

    decade = ""
    cursor = winners_header.parent
    while cursor is not None:
        cursor = cursor.find_next_sibling()
        if cursor is None:
            break
        if cursor.name == "h2":
            break
        if cursor.name == "h3" or (cursor.name == "div" and "mw-heading3" in (cursor.get("class") or [])):
            decade = clean_text(cursor.get_text(" ", strip=True)).replace("[edit]", "").strip()
            continue
        if cursor.name == "table":
            classes = cursor.get("class") or []
            if "wikitable" in classes and "sortable" in classes:
                yield decade, cursor


def first_relevant_link(cell: TableCell | None, *, academy_only: bool = False) -> str | None:
    if cell is None:
        return None
    for link in cell.links:
        href = link["href"]
        if not href.startswith(BASE_URL + "/wiki/"):
            continue
        if academy_only and not ACADEMY_AWARDS_LINK_RE.search(href):
            continue
        return href
    return None


def actor_name_from_cell(cell: TableCell | None) -> str | None:
    if cell is None:
        return None
    if cell.links:
        return cell.links[0]["text"] or clean_text(cell.text)
    text = clean_text(cell.text)
    if not text:
        return None
    for marker in WINNER_MARKERS:
        text = text.replace(marker, "")
    return clean_text(text)


def parse_ano_filme(raw: str | None) -> int | None:
    if not raw:
        return None
    match = YEAR_RE.search(raw)
    return int(match.group(1)) if match else None


def parse_numero_cerimonia(year_cell: TableCell | None) -> tuple[int | None, str | None, str | None]:
    if year_cell is None:
        return None, None, None

    ceremony_link = first_relevant_link(year_cell, academy_only=True)
    ceremony_label = None
    for link in year_cell.links:
        if ACADEMY_AWARDS_LINK_RE.search(link["href"]):
            ceremony_label = link["text"] or None
            break

    source_text = ceremony_label or year_cell.text
    match = CEREMONY_NUMBER_RE.search(source_text or "")
    numero = int(match.group(1)) if match else None
    return numero, ceremony_label, ceremony_link


def is_winner(actor_cell: TableCell | None) -> bool:
    if actor_cell is None:
        return False
    return any(marker in actor_cell.text for marker in WINNER_MARKERS)


def parse_nominee_row(decade: str, row: list[TableCell | None]) -> NomineeRow | None:
    meaningful = [cell for cell in row if cell and cell.text]
    if len(meaningful) < 4:
        return None

    year_cell = row[0] if len(row) > 0 else None
    actor_cell = row[1] if len(row) > 1 else None
    role_cell = row[2] if len(row) > 2 else None
    film_cell = row[3] if len(row) > 3 else None

    ano_filme_raw = clean_text(year_cell.text if year_cell else None)
    ano_filme = parse_ano_filme(ano_filme_raw)
    numero_cerimonia, ceremony_label_raw, url_cerimonia = parse_numero_cerimonia(year_cell)
    nome_ator = actor_name_from_cell(actor_cell)
    filme_indicado = clean_text(film_cell.text if film_cell else None)
    role_raw = clean_text(role_cell.text if role_cell else None)
    url_ator = first_relevant_link(actor_cell)
    url_filme = first_relevant_link(film_cell)
    eh_vencedor = is_winner(actor_cell)

    if not nome_ator or not filme_indicado:
        return None

    return NomineeRow(
        decade=decade,
        ano_filme_raw=ano_filme_raw,
        ano_filme=ano_filme,
        numero_cerimonia=numero_cerimonia,
        nome_ator=nome_ator,
        filme_indicado=filme_indicado,
        role_raw=role_raw,
        url_ator=url_ator,
        url_filme=url_filme,
        url_cerimonia=url_cerimonia,
        eh_vencedor=eh_vencedor,
        ceremony_label_raw=ceremony_label_raw,
    )


def extract_nominees(soup: BeautifulSoup) -> list[NomineeRow]:
    nominees: list[NomineeRow] = []
    for decade, table in iter_winners_tables(soup):
        grid = expand_table(table)
        for row_index, row in enumerate(grid):
            if row_index == 0:
                continue
            nominee = parse_nominee_row(decade, row)
            if nominee is not None:
                nominees.append(nominee)
    return nominees


def write_csv(rows: list[NomineeRow], path: Path) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[NomineeRow], path: Path) -> None:
    payload = [asdict(row) for row in rows]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def build_summary(rows: list[NomineeRow]) -> str:
    winners = sum(1 for row in rows if row.eh_vencedor)
    decades = sorted({row.decade for row in rows})
    sample = rows[:5]
    lines = [
        "# Fase 3 - Lista Base",
        "",
        "## Resultado esperado",
        f"- Linhas extraidas: `{len(rows)}`",
        f"- Vencedores marcados: `{winners}`",
        f"- Decadas encontradas: `{', '.join(decades)}`",
        "",
        "## Colunas exportadas",
        "- `decade`",
        "- `ano_filme_raw`",
        "- `ano_filme`",
        "- `numero_cerimonia`",
        "- `nome_ator`",
        "- `filme_indicado`",
        "- `role_raw`",
        "- `url_ator`",
        "- `url_filme`",
        "- `url_cerimonia`",
        "- `eh_vencedor`",
        "- `ceremony_label_raw`",
        "",
        "## Observacoes",
        "- `ano_filme_raw` preserva o valor original da tabela, inclusive casos como `1927/28`.",
        "- `ano_filme` guarda o primeiro ano numerico encontrado para facilitar etapas posteriores.",
        "- `numero_cerimonia` e `url_cerimonia` sao extraidos do link da propria tabela principal.",
        "- A normalizacao por `rowspan` permite carregar corretamente linhas de multiplos filmes e empates.",
        "",
        "## Amostra",
    ]
    for row in sample:
        lines.append(
            f"- `{row.ano_filme_raw}` | `{row.numero_cerimonia}` | `{row.nome_ator}` | `{row.filme_indicado}` | vencedor=`{row.eh_vencedor}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract the phase 3 Best Actor nominee base list.")
    parser.add_argument("--out-csv", default="output/fase3_lista_base.csv")
    parser.add_argument("--out-json", default="output/fase3_lista_base.json")
    parser.add_argument("--out-md", default="docs/fase3_lista_base.md")
    args = parser.parse_args()

    soup = fetch_soup(BEST_ACTOR_URL)
    rows = extract_nominees(soup)
    if not rows:
        raise RuntimeError("No nominee rows were extracted from the Best Actor page.")

    out_csv = Path(args.out_csv)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    write_csv(rows, out_csv)
    write_json(rows, out_json)
    out_md.write_text(build_summary(rows), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
