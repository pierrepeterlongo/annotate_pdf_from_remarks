import fitz

from annotate_pdf_from_remarks.line_index import build_line_index


def test_detects_monotonic_margin_numbers_and_rejects_noise(sample_pdf_path):
    doc = fitz.open(sample_pdf_path)
    try:
        index = build_line_index(doc)
    finally:
        doc.close()

    assert set(index.keys()) == set(range(1, 11))
    assert 9999 not in index

    page_index, bbox = index[10]
    assert page_index == 1
    assert bbox[0] < 50  # left-margin x position


def test_max_forward_jump_can_be_tightened(sample_pdf_path):
    doc = fitz.open(sample_pdf_path)
    try:
        # A very small jump budget should still accept the real +1 steps.
        index = build_line_index(doc, max_forward_jump=1)
    finally:
        doc.close()

    assert set(index.keys()) == set(range(1, 11))
