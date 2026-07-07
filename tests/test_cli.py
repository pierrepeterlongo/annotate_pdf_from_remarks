import getpass

import fitz

from annotate_pdf_from_remarks.cli import main


def test_author_and_date_default_when_not_given(sample_pdf_path, tmp_path):
    remarks_path = tmp_path / "remarks.md"
    remarks_path.write_text("l3: a remark\n\nl9999: an unresolvable remark\n")
    output_path = str(tmp_path / "out.pdf")

    exit_code = main(
        [
            "--pdf", sample_pdf_path,
            "--remarks", str(remarks_path),
            "--output", output_path,
        ]
    )

    assert exit_code == 1  # the unresolvable remark is reported as a failure
    doc = fitz.open(output_path)
    page = doc[0]
    annots = list(page.annots())

    report_box = next(a for a in annots if a.type[1] == "FreeText")
    assert f"Author: {getpass.getuser()}" in report_box.info["content"]
    assert "Date: " in report_box.info["content"]

    comment = next(a for a in annots if a.type[1] == "Text")
    assert comment.info.get("title") == getpass.getuser()


def test_author_and_date_can_be_overridden(sample_pdf_path, tmp_path):
    remarks_path = tmp_path / "remarks.md"
    remarks_path.write_text("l9999: an unresolvable remark\n")
    output_path = str(tmp_path / "out.pdf")

    main(
        [
            "--pdf", sample_pdf_path,
            "--remarks", str(remarks_path),
            "--output", output_path,
            "--author", "Jane Doe",
            "--date", "2026-01-01",
        ]
    )

    doc = fitz.open(output_path)
    page = doc[0]
    report_box = next(a for a in page.annots() if a.type[1] == "FreeText")
    assert "Author: Jane Doe" in report_box.info["content"]
    assert "Date: 2026-01-01" in report_box.info["content"]
