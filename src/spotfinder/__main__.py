"""Entry point: python -m spotfinder"""

from __future__ import annotations

import argparse
import sys

from prettytable import PrettyTable
from termcolor import colored

from spotfinder.core.types import INDUSTRIES
from spotfinder.handlers.export import handle_export
from spotfinder.handlers.results import handle_results
from spotfinder.handlers.scan import handle_scan


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spotfinder",
        description="SpotFinder - escaner de oportunidades de negocio local",
    )
    subs = parser.add_subparsers(dest="command")

    _add_scan_parser(subs)
    _add_results_parser(subs)
    _add_export_parser(subs)
    _add_industries_parser(subs)

    return parser


def _add_scan_parser(subs) -> None:
    p = subs.add_parser("scan", help="Escanear negocios en una zona")
    p.add_argument("--location", required=True, help="Ubicacion a escanear")
    p.add_argument("--niche", required=True, help="Nicho/industria")
    p.add_argument("--country", required=True, help="Codigo de pais (ISO)")
    p.add_argument("--lat", type=float, help="Latitud")
    p.add_argument("--lng", type=float, help="Longitud")
    p.add_argument("--radius", type=float, help="Radio en km")
    p.set_defaults(func=handle_scan)


def _add_results_parser(subs) -> None:
    p = subs.add_parser("results", help="Ver resultados de un escaneo")
    p.add_argument("--scan-id", help="ID del escaneo")
    p.add_argument("--limit", type=int, default=50, help="Limite de filas")
    p.set_defaults(func=handle_results)


def _add_export_parser(subs) -> None:
    p = subs.add_parser("export", help="Exportar resultados")
    p.add_argument("--scan-id", required=True, help="ID del escaneo")
    p.add_argument(
        "--format", required=True, choices=["csv", "json"],
        help="Formato de salida",
    )
    p.add_argument("--output", required=True, help="Ruta del archivo")
    p.set_defaults(func=handle_export)


def _add_industries_parser(subs) -> None:
    p = subs.add_parser("industries", help="Listar industrias objetivo")
    p.set_defaults(func=_handle_industries)


def _handle_industries(args: argparse.Namespace) -> None:
    print(colored("\n  Industrias objetivo de SpotFinder:\n", "cyan"))
    table = PrettyTable()
    table.field_names = [
        "Slug", "Nombre", "Tier", "Revenue USD",
        "Margen %", "Adopcion Web %",
    ]
    table.align["Nombre"] = "l"
    table.align["Slug"] = "l"

    for profile in INDUSTRIES.values():
        table.add_row([
            profile.slug,
            profile.name_es,
            profile.tier,
            f"${profile.avg_revenue_usd:,}",
            f"{profile.gross_margin_pct:.0%}",
            f"{profile.website_adoption_pct:.0%}",
        ])

    print(table)


if __name__ == "__main__":
    main()
