"""Command-line entry point: annotate-pdf-from-remarks."""

import argparse
import datetime
import getpass
import json
import sys

import fitz

from annotate_pdf_from_remarks import __version__
from annotate_pdf_from_remarks.annotate import (
    add_report_annotation,
    annotate_pdf,
    build_report_text,
)
from annotate_pdf_from_remarks.line_index import build_line_index
from annotate_pdf_from_remarks.remarks_parser import parse_remarks_file


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="annotate-pdf-from-remarks",
        description=(
            "Add PDF comment annotations to a line-numbered PDF, from a "
            "plain-text remarks file (see README for the remarks syntax)."
        ),
    )
    parser.add_argument(
        "--pdf", required=True, help="Path to the input, line-numbered PDF."
    )
    parser.add_argument(
        "--remarks", required=True, help="Path to the remarks file."
    )
    parser.add_argument(
        "--output", required=True, help="Path to write the annotated PDF."
    )
    parser.add_argument(
        "--author",
        default=None,
        help=(
            "Author name recorded on each PDF annotation. Defaults to the "
            "current OS login if not given."
        ),
    )
    parser.add_argument(
        "--date",
        default=None,
        help=(
            "Date recorded on the first-page report box (any format you "
            "like). Defaults to today's date (ISO 8601) if not given."
        ),
    )
    parser.add_argument(
        "--margin-frac",
        type=float,
        default=0.15,
        help=(
            "Fraction of the page width, from each edge, considered "
            "margin when detecting printed line numbers (default: 0.15)."
        ),
    )
    parser.add_argument(
        "--max-forward-jump",
        type=int,
        default=500,
        help=(
            "Maximum accepted jump between consecutive detected line "
            "numbers (default: 500)."
        ),
    )
    parser.add_argument(
        "--dump-index",
        default=None,
        help=(
            "Optional path to dump the detected line-number index as JSON, "
            "for debugging anchor resolution."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.author is None:
        args.author = getpass.getuser()
    if args.date is None:
        args.date = datetime.date.today().isoformat()

    doc = fitz.open(args.pdf)
    line_index = build_line_index(
        doc,
        margin_frac=args.margin_frac,
        max_forward_jump=args.max_forward_jump,
    )

    if args.dump_index:
        with open(args.dump_index, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in line_index.items()}, f, indent=2)

    remarks, warnings = parse_remarks_file(args.remarks)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    placed, failures = annotate_pdf(doc, line_index, remarks, author=args.author)

    report_text = build_report_text(
        warnings, failures, author=args.author, date=args.date
    )
    if report_text:
        add_report_annotation(doc, report_text)

    doc.save(args.output, garbage=4, deflate=True)

    print(f"{len(line_index)} printed line numbers detected in {args.pdf}")
    print(f"{placed} annotation(s) placed in {args.output}")
    if failures:
        print(f"{len(failures)} remark(s) could NOT be anchored:", file=sys.stderr)
        for remark, reason in failures:
            print(f"  - {reason} (remark: {remark['remark'][:80]!r})", file=sys.stderr)
    if report_text:
        print(
            "A report of the above was also added as a visible box on the "
            "first page of the output PDF."
        )

    return 1 if (failures or warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
