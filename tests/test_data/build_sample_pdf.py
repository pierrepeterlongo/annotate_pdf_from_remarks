"""Build a small synthetic, line-numbered PDF used as a test fixture.

Generated purely in Python via PyMuPDF so the test suite needs no LaTeX
toolchain and stays fully cross-platform.
"""

import fitz

MARGIN_X = 40
BODY_X = 90
LINE_FONTSIZE = 6
BODY_FONTSIZE = 10


def build_sample_pdf(path):
    doc = fitz.open()

    page0 = doc.new_page(width=595, height=842)
    page0.insert_text((200, 50), "Sample Document", fontsize=16)
    for i, n in enumerate([1, 2, 3, 4, 5]):
        y = 100 + i * 20
        page0.insert_text((MARGIN_X, y), str(n), fontsize=LINE_FONTSIZE)
        page0.insert_text((BODY_X, y), f"This is body line {n}.", fontsize=BODY_FONTSIZE)
    # Noise: a wildly out-of-sequence number sitting in the margin band
    # (e.g. a footnote marker), which the monotonic filter must reject.
    page0.insert_text((MARGIN_X, 220), "9999", fontsize=LINE_FONTSIZE)
    # Noise: a backward-jumping duplicate, also to be rejected.
    page0.insert_text((MARGIN_X, 240), "3", fontsize=LINE_FONTSIZE)

    page1 = doc.new_page(width=595, height=842)
    for i, n in enumerate([6, 7, 8, 9, 10]):
        y = 100 + i * 20
        page1.insert_text((MARGIN_X, y), str(n), fontsize=LINE_FONTSIZE)
        text = "the quick brown fox" if n == 10 else f"This is body line {n}."
        page1.insert_text((BODY_X, y), text, fontsize=BODY_FONTSIZE)
    page1.insert_text((BODY_X, 260), "Figure 1.2 - Sample figure caption.", fontsize=BODY_FONTSIZE)
    page1.insert_text((BODY_X, 280), "Figure 1.2 - Sample figure caption.", fontsize=BODY_FONTSIZE)

    doc.save(path)
    doc.close()
