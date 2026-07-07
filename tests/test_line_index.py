import fitz

from annotate_pdf_from_remarks.line_index import _keep_margin_columns, build_line_index


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


def test_margin_frac_can_be_loosened_without_pulling_in_noise(sample_pdf_path):
    doc = fitz.open(sample_pdf_path)
    try:
        # A much wider net should still resolve to the same, correct
        # column: auto-detection (not margin_frac) does the real work.
        index = build_line_index(doc, margin_frac=0.45)
    finally:
        doc.close()

    assert set(index.keys()) == set(range(1, 11))


def test_keep_margin_columns_drops_low_frequency_bins():
    # (page_index, y0, number, bbox) tuples: a dense, real column at
    # x1=46, plus a single stray candidate far off at x1=300.
    candidates = [(0, float(y), y, (40.0, float(y), 46.0, float(y) + 6)) for y in range(1, 11)]
    candidates.append((0, 50.0, 999, (294.0, 50.0, 300.0, 56.0)))

    kept = _keep_margin_columns(
        candidates, bin_size=2.0, min_ratio=0.5, min_candidates=5
    )

    assert 999 not in {c[2] for c in kept}
    assert {c[2] for c in kept} == set(range(1, 11))


def test_max_forward_jump_can_be_tightened(sample_pdf_path):
    doc = fitz.open(sample_pdf_path)
    try:
        # A very small jump budget should still accept the real +1 steps.
        index = build_line_index(doc, max_forward_jump=1)
    finally:
        doc.close()

    assert set(index.keys()) == set(range(1, 11))
