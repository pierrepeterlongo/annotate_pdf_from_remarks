from pathlib import Path

import fitz

from annotate_pdf_from_remarks.annotate import (
    add_report_annotation,
    annotate_pdf,
    build_report_text,
)
from annotate_pdf_from_remarks.line_index import build_line_index
from annotate_pdf_from_remarks.remarks_parser import parse_remarks_file

EXAMPLE_REMARKS = Path(__file__).parent / "test_data" / "example_remarks.md"


def test_end_to_end_annotation(sample_pdf_path, tmp_path):
    remarks, warnings = parse_remarks_file(EXAMPLE_REMARKS)
    assert len(warnings) == 1  # the deliberately anchor-less last line

    doc = fitz.open(sample_pdf_path)
    line_index = build_line_index(doc)

    placed, failures = annotate_pdf(doc, line_index, remarks, author="Test Author")
    assert failures == []
    assert placed == len(remarks) == 4

    output_path = str(tmp_path / "annotated.pdf")
    doc.save(output_path)
    doc.close()

    reopened = fitz.open(output_path)
    all_annots = [a for page in reopened for a in page.annots()]
    assert len(all_annots) == 4

    contents = {a.info["content"] for a in all_annots}
    assert (
        "this line could be phrased more precisely\n"
        "continuation of the same remark, still about line 3"
    ) in contents
    assert any(a.info.get("title") == "Test Author" for a in all_annots)
    assert any(a.info.get("subject") == "Chapter One" for a in all_annots)


def test_unresolvable_anchor_is_reported_not_raised(sample_pdf_path):
    doc = fitz.open(sample_pdf_path)
    line_index = build_line_index(doc)

    remarks = [{"chapter": None, "line": 9999, "remark": "does not exist"}]
    placed, failures = annotate_pdf(doc, line_index, remarks)

    assert placed == 0
    assert len(failures) == 1
    assert failures[0][0] is remarks[0]
    doc.close()


def test_build_report_text_is_none_when_nothing_to_report():
    assert build_report_text([], [], author="Test Author") is None


def test_report_annotation_shows_author_date_warnings_and_failures(sample_pdf_path, tmp_path):
    warnings = ["line 5: unrecognized syntax, skipped: 'garbled input'"]
    failures = [({"remark": "some remark"}, "printed line 9999 not found in the line index")]

    text = build_report_text(warnings, failures, author="Test Author", date="2026-07-07")
    assert "Author: Test Author" in text
    assert "Date: 2026-07-07" in text
    assert "garbled input" in text
    assert "printed line 9999 not found" in text

    doc = fitz.open(sample_pdf_path)
    add_report_annotation(doc, text)
    output_path = str(tmp_path / "report.pdf")
    doc.save(output_path)
    doc.close()

    reopened = fitz.open(output_path)
    first_page = reopened[0]  # keep a live reference: annots are unbound once the page is GC'd
    first_page_annots = list(first_page.annots())
    assert len(first_page_annots) == 1
    assert first_page_annots[0].type[1] == "FreeText"
    assert "Test Author" in first_page_annots[0].info["content"]
