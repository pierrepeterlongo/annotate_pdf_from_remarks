from pathlib import Path

import fitz

from annotate_pdf_from_remarks.annotate import annotate_pdf
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
