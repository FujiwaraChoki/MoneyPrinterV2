"""CLI handler for the 'scan' command."""

from __future__ import annotations

import argparse

from prettytable import PrettyTable
from termcolor import colored

from spotfinder.adapters.db import Database
from spotfinder.adapters.google_maps import GoogleMapsScraper
from spotfinder.adapters.http_client import HttpClient
from spotfinder.core.errors import SpotFinderError, ValidationError
from spotfinder.core.types import ScanRequest
from spotfinder.services.pipeline import Pipeline


def handle_scan(args: argparse.Namespace) -> None:
    """Maneja el comando 'scan' del CLI."""
    scan = _build_scan_request(args)
    print(colored(
        f"\n  Iniciando escaneo: {scan.niche} en {scan.location_query}",
        "cyan",
    ))

    db = Database()
    scraper = GoogleMapsScraper()
    http_client = HttpClient()
    pipeline = Pipeline(db, scraper, http_client)

    try:
        pipeline.run(scan)
    except SpotFinderError as exc:
        print(colored(f"\n  Error: {exc}", "red"))
        return

    _print_summary(db, scan.id)


def _build_scan_request(args: argparse.Namespace) -> ScanRequest:
    _validate_inputs(args)
    return ScanRequest(
        location_query=args.location,
        niche=args.niche,
        country_code=args.country,
        latitude=getattr(args, "lat", None),
        longitude=getattr(args, "lng", None),
        radius_km=getattr(args, "radius", None),
    )


def _validate_inputs(args: argparse.Namespace) -> None:
    if not args.location or not args.location.strip():
        raise ValidationError(
            code="INVALID_LOCATION",
            message="La ubicacion no puede estar vacia.",
        )
    if not args.niche or not args.niche.strip():
        raise ValidationError(
            code="INVALID_NICHE",
            message="El nicho no puede estar vacio.",
        )
    if not args.country or len(args.country) != 2:
        raise ValidationError(
            code="INVALID_COUNTRY_CODE",
            message="El codigo de pais debe ser de 2 caracteres (ISO 3166).",
        )


def _print_summary(db: Database, scan_id: str) -> None:
    scores = db.get_scores_by_scan(scan_id)
    businesses = db.get_businesses_by_scan(scan_id)
    biz_by_id = {b.id: b for b in businesses}

    count = len(scores)
    print(colored(
        f"\n  Escaneo completo. Se encontraron {count} negocios.",
        "green",
    ))

    if not scores:
        return

    print(colored("  Top 10:", "green"))
    table = _build_top_table(scores, biz_by_id)
    print(table)


def _build_top_table(scores, biz_by_id) -> PrettyTable:
    table = PrettyTable()
    table.field_names = [
        "#", "Nombre", "Categoria", "Rating", "Reviews",
        "Website?", "Score",
    ]
    table.align["Nombre"] = "l"
    table.align["Categoria"] = "l"

    top_10 = sorted(scores, key=lambda s: s.rank)[:10]
    for score in top_10:
        biz = biz_by_id.get(score.business_id)
        if biz is None:
            continue
        _add_top_row(table, score, biz)
    return table


def _add_top_row(table: PrettyTable, score, biz) -> None:
    has_web = "Si" if biz.website_url else "No"
    table.add_row([
        score.rank,
        _truncate(biz.name, 30),
        _truncate(biz.category, 20),
        biz.google_rating or "-",
        biz.google_review_count or "-",
        has_web,
        f"{score.opportunity_score:.2f}",
    ])


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
