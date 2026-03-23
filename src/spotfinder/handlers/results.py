"""CLI handler for the 'results' command."""

from __future__ import annotations

import argparse

from prettytable import PrettyTable
from termcolor import colored

from spotfinder.adapters.db import Database
from spotfinder.core.types import ScanRequest


def handle_results(args: argparse.Namespace) -> None:
    """Maneja el comando 'results' del CLI."""
    db = Database()
    db.initialize()
    scan = _resolve_scan(db, args)
    if scan is None:
        print(colored("  No se encontraron escaneos.", "yellow"))
        return

    _print_results(db, scan, _get_limit(args))


def _resolve_scan(
    db: Database, args: argparse.Namespace,
) -> ScanRequest | None:
    scan_id = getattr(args, "scan_id", None)
    if scan_id:
        return db.get_scan(scan_id)
    return db.get_latest_scan()


def _get_limit(args: argparse.Namespace) -> int:
    return getattr(args, "limit", 50) or 50


def _print_results(db: Database, scan: ScanRequest, limit: int) -> None:
    scores = db.get_scores(scan.id)
    businesses = db.get_businesses(scan.id)
    presences = db.get_digital_presences_by_scan(scan.id)

    biz_by_id = {b.id: b for b in businesses}
    dp_by_biz = {p.business_id: p for p in presences}

    print(colored(
        f"\n  Resultados: {scan.niche} en {scan.location_query} "
        f"({scan.status.value})",
        "cyan",
    ))

    table = _build_table()
    ranked = sorted(scores, key=lambda s: s.rank)[:limit]

    for score in ranked:
        biz = biz_by_id.get(score.business_id)
        if biz is None:
            continue
        dp = dp_by_biz.get(biz.id)
        _add_row(table, score, biz, dp)

    print(table)


def _build_table() -> PrettyTable:
    table = PrettyTable()
    table.field_names = [
        "#", "Nombre", "Categoria", "Direccion", "Telefono",
        "Website", "Rating", "Reviews", "Gap", "Revenue",
        "Access", "Total",
    ]
    table.align["Nombre"] = "l"
    table.align["Categoria"] = "l"
    table.align["Direccion"] = "l"
    return table


def _add_row(table: PrettyTable, score, biz, dp) -> None:
    table.add_row([
        score.rank,
        _trunc(biz.name, 25),
        _trunc(biz.category, 15),
        _trunc(biz.address, 25),
        biz.phone or "-",
        "Si" if biz.website_url else "No",
        biz.google_rating or "-",
        biz.google_review_count or "-",
        f"{score.digital_gap_score:.2f}",
        f"{score.revenue_potential_score:.2f}",
        f"{score.accessibility_score:.2f}",
        f"{score.opportunity_score:.2f}",
    ])


def _trunc(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
