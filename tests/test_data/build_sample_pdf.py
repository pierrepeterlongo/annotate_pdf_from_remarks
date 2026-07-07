"""Build a small synthetic, line-numbered PDF used as a test fixture.

Generated purely in Python via PyMuPDF so the test suite needs no LaTeX
toolchain and stays fully cross-platform. Margin numbers are right-aligned
against a fixed right edge, mirroring how LaTeX's ``lineno`` package
actually typesets them (single- and multi-digit numbers share the same
right edge, not the same left edge).
"""

import fitz

MARGIN_RIGHT = 46
BODY_X = 90
LINE_FONTSIZE = 6
BODY_FONTSIZE = 10
FONTNAME = "helv"


def _insert_right_aligned_number(page, text, y):
    width = fitz.get_text_length(text, fontname=FONTNAME, fontsize=LINE_FONTSIZE)
    page.insert_text((MARGIN_RIGHT - width, y), text, fontsize=LINE_FONTSIZE, fontname=FONTNAME)


def build_sample_pdf(path):
    doc = fitz.open()

    page0 = doc.new_page(width=595, height=842)
    page0.insert_text((200, 50), "Sample Document", fontsize=16)
    for i, n in enumerate([1, 2, 3, 4, 5]):
        y = 100 + i * 20
        _insert_right_aligned_number(page0, str(n), y)
        page0.insert_text((BODY_X, y), f"This is body line {n}.", fontsize=BODY_FONTSIZE)
    # Noise: a wildly out-of-sequence number sitting in the same margin
    # column (e.g. a footnote marker), which the monotonic filter must
    # reject even though column detection alone cannot.
    _insert_right_aligned_number(page0, "9999", 220)
    # Noise: a backward-jumping duplicate, also to be rejected.
    _insert_right_aligned_number(page0, "3", 240)

    page1 = doc.new_page(width=595, height=842)
    for i, n in enumerate([6, 7, 8, 9, 10]):
        y = 100 + i * 20
        _insert_right_aligned_number(page1, str(n), y)
        text = "the quick brown fox" if n == 10 else f"This is body line {n}."
        page1.insert_text((BODY_X, y), text, fontsize=BODY_FONTSIZE)
    page1.insert_text((BODY_X, 260), "Figure 1.2 - Sample figure caption.", fontsize=BODY_FONTSIZE)
    page1.insert_text((BODY_X, 280), "Figure 1.2 - Sample figure caption.", fontsize=BODY_FONTSIZE)

    doc.save(path)
    doc.close()
