"""Build a mapping from printed margin line numbers to their PDF location.

This targets PDFs typeset with a line-numbering package such as the LaTeX
``lineno`` package (``\\usepackage{lineno}`` + ``\\linenumbers``), where every
text line carries a small number printed in the page margin. The numbering is
assumed to increase monotonically across the whole document (no per-page or
per-chapter reset), which is the default ``lineno`` behaviour.

Detection is heuristic, since PDFs carry no semantic tag for "this span is a
line number":

1. Candidate spans are collected on every page: a text line made of a single
   span, whose text is only digits, and whose horizontal position falls in
   the outer margin (the leftmost or rightmost fraction of the page width,
   to account for mirrored margins on odd/even pages in double-sided
   layouts).
2. Candidates are then read in page/vertical order, and the longest
   strictly increasing subsequence of numbers is extracted from them (gaps
   are allowed, e.g. across full-page figures, and a jump between two
   consecutive kept numbers is only allowed up to ``max_forward_jump``).
   Using the *longest* such subsequence -- rather than greedily accepting
   the first strictly-increasing candidate found -- matters because the
   margin band inevitably also catches noise (footnote markers, equation
   numbers, citation numbers, exponents, ...): a single early false
   positive would otherwise desynchronise a naive greedy walk from the
   true numbering for the rest of the document.

The result is a plain ``dict`` so it can be cached to JSON between runs.
"""

import fitz


def build_line_index(doc, margin_frac=0.15, max_forward_jump=500):
    """Return ``{line_number: (page_index, bbox)}`` for a line-numbered PDF.

    Parameters
    ----------
    doc : fitz.Document
        An already-opened PDF.
    margin_frac : float
        Fraction of the page width, from each edge, considered "margin".
        Candidate line numbers must start (left margin) or end (right
        margin) within this band.
    max_forward_jump : int
        Maximum accepted increase between two consecutive accepted line
        numbers. Bounds how large a gap (e.g. a full-page figure) the
        monotonic filter tolerates before still discarding wildly
        out-of-sequence noise.
    """
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

    candidates.sort(key=lambda c: (c[0], c[1]))
    numbers = [c[2] for c in candidates]
    chain = _longest_increasing_chain(numbers, max_forward_jump)

    return {
        numbers[i]: (candidates[i][0], candidates[i][3]) for i in chain
    }


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


def build_line_index_from_path(pdf_path, margin_frac=0.15, max_forward_jump=500):
    """Convenience wrapper: open ``pdf_path`` and build its line index."""
    doc = fitz.open(pdf_path)
    try:
        return build_line_index(
            doc, margin_frac=margin_frac, max_forward_jump=max_forward_jump
        )
    finally:
        doc.close()
