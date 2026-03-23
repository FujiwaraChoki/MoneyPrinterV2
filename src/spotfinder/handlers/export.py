"""CLI handler for the 'export' command."""

from __future__ import annotations

import argparse
import csv
import json
import os

from termcolor import colored

from spotfinder.adapters.db import Database

_CSV_COLUMNS = [
    "rank", "name", "category", "address", "phone", "email",
    "website_url", "google_rating", "google_review_count",
    "has_website", "has_ssl", "has_facebook", "has_instagram",
    "has_whatsapp", "digital_gap_score", "revenue_potential_score",
    "accessibility_score", "opportunity_score", "rationale",
]


def handle_export(args: argparse.Namespace) -> None:
    """Maneja el comando 'export' del CLI."""
    db = Database()
    db.initialize()
    scan = db.get_scan(args.scan_id)
    if scan is None:
        print(colored("  Escaneo no encontrado.", "red"))
        return

    rows = _collect_rows(db, scan.id)
    if not rows:
        print(colored("  No hay resultados para exportar.", "yellow"))
        return

    if args.format == "csv":
        _export_csv(rows, args.output)
    else:
        _export_json(rows, args.output)

    print(colored(
        f"  Exportado {len(rows)} negocios a {args.output}", "green",
    ))


def _collect_rows(db: Database, scan_id: str) -> list[dict[str, object]]:
    scores = db.get_scores(scan_id)
    businesses = db.get_businesses(scan_id)
    presences = db.get_digital_presences_by_scan(scan_id)

    biz_by_id = {b.id: b for b in businesses}
    dp_by_biz = {p.business_id: p for p in presences}
    ranked = sorted(scores, key=lambda s: s.rank)

    rows: list[dict[str, object]] = []
    for score in ranked:
        biz = biz_by_id.get(score.business_id)
        if biz is None:
            continue
        dp = dp_by_biz.get(biz.id)
        rows.append(_build_row(score, biz, dp))
    return rows


def _build_row(score, biz, dp) -> dict[str, object]:
    return {
        "rank": score.rank,
        "name": biz.name,
        "category": biz.category,
        "address": biz.address,
        "phone": biz.phone or "",
        "email": biz.email or "",
        "website_url": biz.website_url or "",
        "google_rating": biz.google_rating,
        "google_review_count": biz.google_review_count,
        "has_website": dp.has_website if dp else False,
        "has_ssl": dp.website_has_ssl if dp else False,
        "has_facebook": dp.has_facebook if dp else False,
        "has_instagram": dp.has_instagram if dp else False,
        "has_whatsapp": dp.has_whatsapp if dp else False,
        "digital_gap_score": score.digital_gap_score,
        "revenue_potential_score": score.revenue_potential_score,
        "accessibility_score": score.accessibility_score,
        "opportunity_score": score.opportunity_score,
        "rationale": score.scoring_rationale,
    }


def _export_csv(rows: list[dict[str, object]], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _export_json(rows: list[dict[str, object]], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"data": rows}, f, indent=2, ensure_ascii=False)
