"""Command line entry point for the safe Yoku Tea Video Factory MVP."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yoku.claims_guard import check_claims
from yoku.exceptions import YokuError
from yoku.product_catalog import ProductCatalog
from yoku.review_package import create_review_package
from yoku.script_builder import build_script
from yoku.template_catalog import TemplateCatalog

def build_parser():
    parser = argparse.ArgumentParser(description="Yoku Tea: пакет сценария для ручной проверки")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="сформировать безопасный черновик")
    generate.add_argument("--product", required=True)
    generate.add_argument("--template", required=True)
    generate.add_argument("--output-dir", type=Path, default=ROOT / "output")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        product = ProductCatalog(ROOT / "data" / "products").load(args.product)
        template = TemplateCatalog(ROOT / "data" / "templates").load(args.template)
        result = build_script(product, template)
        report = check_claims(result["script"], product)
        if report["status"] == "FAIL":
            print("Claims Guard: FAIL")
            for error in report["errors"]:
                print(f'- {error["message"]}')
            return 1
        folder = create_review_package(args.output_dir, product, template, result, report)
        print(folder)
        return 0
    except YokuError as error:
        print(f"Ошибка: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
