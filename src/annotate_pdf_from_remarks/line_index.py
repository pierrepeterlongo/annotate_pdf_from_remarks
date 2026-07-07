"""Build a mapping from printed margin line numbers to their PDF location.

This targets PDFs typeset with a line-numbering package such as the LaTeX
``lineno`` package (``\\usepackage{lineno}`` + ``\\linenumbers``), where every
text line carries a small number printed in the page margin. The numbering is
assumed to increase monotonically across the whole document (no per-page or
per-chapter reset), which is the default ``lineno`` behaviour.

Detection is heuristic, since PDFs carry no semantic tag for "this span is a
line number":

1. A first, deliberately loose pass collects every text line made of a
   single span, whose text is only digits, and whose horizontal position
   falls in the outer margin (the leftmost or rightmost ``margin_frac`` of
   the page width, to account for mirrored margins on odd/even pages in
   double-sided layouts). This is just a coarse net, wide enough to catch
   the real numbering column even on an unusually wide margin.
2. The real margin column(s) are then auto-detected among that first pass:
   a genuine line-number column prints on (almost) every line of the
   document, so its position recurs far more often than any other digit
   that happens to land in the margin band (a citation number, a footnote
   marker, ...). The clustering key is the span's *right* edge (``x1``),
   not its left edge: line-numbering packages typically right-align the
   number (so single- and multi-digit numbers share the same right edge),
   which means ``x0`` drifts with the digit count while ``x1`` stays put.
   Candidates are grouped into narrow ``x1`` bins, and only the bin(s)
   whose frequency is within ``column_min_ratio`` of the most frequent bin
   are kept -- this also naturally keeps two bins when odd/even pages
   mirror the column.
3. Candidates are then read in page/vertical order, and the longest
   strictly increasing subsequence of numbers is extracted from them (gaps
   are allowed, e.g. across full-page figures, and a jump between two
   consecutive kept numbers is only allowed up to ``max_forward_jump``).
   Using the *longest* such subsequence -- rather than greedily accepting
   the first strictly-increasing candidate found -- matters because step 2
   still lets through some noise sitting in the same column (e.g. a page
   number reused at the same x-position): a single early false positive
   would otherwise desynchronise a naive greedy walk from the true
   numbering for the rest of the document.

The result is a plain ``dict`` so it can be cached to JSON between runs.
"""

from collections import Counter

import fitz


def build_line_index(
    doc,
    margin_frac=0.2,
    max_forward_jump=500,
    column_bin_size=2.0,
    column_min_ratio=0.5,
    min_candidates_for_clustering=5,
):
    """Return ``{line_number: (page_index, bbox)}`` for a line-numbered PDF.

    Parameters
    ----------
    doc : fitz.Document
        An already-opened PDF.
    margin_frac : float
        Fraction of the page width, from each edge, initially considered
        "margin" when collecting candidates (see step 1 above). Only needs
        widening if the real numbering column sits further from the edge
        than this; the precise column position is auto-detected afterwards
        (step 2), so this does not need to be tuned tightly.
    max_forward_jump : int
        Maximum accepted increase between two consecutive accepted line
        numbers. Bounds how large a gap (e.g. a full-page figure) the
        monotonic filter tolerates before still discarding wildly
        out-of-sequence noise.
    column_bin_size : float
        Bin width, in PDF points, used to group candidates by their right
        edge (``x1``) when auto-detecting the margin column(s).
    column_min_ratio : float
        A bin is kept as a genuine margin column if its candidate count is
        at least this fraction of the most populated bin's count.
    min_candidates_for_clustering : int
        Below this many raw candidates, column auto-detection is skipped
        (too little data to distinguish a real column from noise) and all
        raw candidates are kept.
    """
    candidates = _collect_raw_candidates(doc, margin_frac)
    candidates = _keep_margin_columns(
        candidates, column_bin_size, column_min_ratio, min_candidates_for_clustering
    )

    candidates.sort(key=lambda c: (c[0], c[1]))
    numbers = [c[2] for c in candidates]
    chain = _longest_increasing_chain(numbers, max_forward_jump)

    return {
        numbers[i]: (candidates[i][0], candidates[i][3]) for i in chain
    }


def _collect_raw_candidates(doc, margin_frac):
    candidates = []
    for page_index in range(doc.page_count):
        page = doc[page_index]
        width = page.rect.width
        left_limit = margin_frac * width
        right_limit = (1 - margin_frac) * width
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line["spans"]
                if len(spans) != 1:
                    continue
                span = spans[0]
                text = span["text"].strip()
                if not text.isdigit():
                    continue
                x0, y0, x1, _ = span["bbox"]
                in_left_margin = x0 <= left_limit
                in_right_margin = x1 >= right_limit
                if not (in_left_margin or in_right_margin):
                    continue
                candidates.append((page_index, y0, int(text), span["bbox"]))
    return candidates


def _keep_margin_columns(candidates, bin_size, min_ratio, min_candidates):
    """Filter ``candidates`` down to those sitting in an auto-detected
    margin column (see module docstring, step 2)."""
    if len(candidates) < min_candidates:
        return candidates

    def bin_of(candidate):
        x1 = candidate[3][2]
        return round(x1 / bin_size)

    counts = Counter(bin_of(c) for c in candidates)
    max_count = max(counts.values())
    kept_bins = {b for b, count in counts.items() if count >= max_count * min_ratio}
    return [c for c in candidates if bin_of(c) in kept_bins]


def _longest_increasing_chain(numbers, max_forward_jump):
    """Indices of the longest strictly increasing subsequence of ``numbers``,
    keeping the sequence's original order and rejecting steps larger than
    ``max_forward_jump``. O(n^2), which is fine for the few thousand margin
    candidates a typical document produces."""
    n = len(numbers)
    best_len = [1] * n
    predecessor = [-1] * n
    for j in range(n):
        for i in range(j):
            if numbers[i] < numbers[j] <= numbers[i] + max_forward_jump:
                if best_len[i] + 1 > best_len[j]:
                    best_len[j] = best_len[i] + 1
                    predecessor[j] = i

    if n == 0:
        return []
    end = max(range(n), key=lambda k: best_len[k])
    chain = []
    while end != -1:
        chain.append(end)
        end = predecessor[end]
    chain.reverse()
    return chain


def build_line_index_from_path(pdf_path, **kwargs):
    """Convenience wrapper: open ``pdf_path`` and build its line index.
    Keyword arguments are forwarded to :func:`build_line_index`."""
    doc = fitz.open(pdf_path)
    try:
        return build_line_index(doc, **kwargs)
    finally:
        doc.close()
