"""Resolve parsed remarks to PDF locations and write them as PDF comments."""

import fitz


class AnchorResolutionError(Exception):
    """Raised when a remark's anchor cannot be located in the PDF."""


def _search_all_pages(doc, needle):
    matches = []
    for page_index in range(doc.page_count):
        for rect in doc[page_index].search_for(needle):
            matches.append((page_index, rect))
    return matches


def resolve_anchor(doc, line_index, remark):
    """Return ``(page_index, fitz.Point)`` for one parsed remark dict."""
    if "line" in remark:
        number = remark["line"]
        if number not in line_index:
            raise AnchorResolutionError(
                f"printed line {number} not found in the line index"
            )
        page_index, bbox = line_index[number]
        return page_index, fitz.Point(bbox[2] + 6, bbox[1] - 1)

    needle = remark["find"]
    occurrence = remark["occurrence"]
    if remark["page"] is not None:
        rects = doc[remark["page"]].search_for(needle)
        if occurrence >= len(rects):
            raise AnchorResolutionError(
                f"text {needle!r} occurrence {occurrence} not found on "
                f"page {remark['page']} ({len(rects)} match(es) found)"
            )
        return remark["page"], fitz.Point(
            max(rects[occurrence].x0 - 20, 10), rects[occurrence].y0
        )

    matches = _search_all_pages(doc, needle)
    if occurrence >= len(matches):
        raise AnchorResolutionError(
            f"text {needle!r} occurrence {occurrence} not found anywhere "
            f"in the document ({len(matches)} match(es) found)"
        )
    page_index, rect = matches[occurrence]
    return page_index, fitz.Point(max(rect.x0 - 20, 10), rect.y0)


def annotate_pdf(doc, line_index, remarks, author=None):
    """Add one PDF text (comment) annotation per resolved remark.

    Returns ``(placed, failures)`` where ``failures`` is a list of
    ``(remark, reason)`` pairs for remarks whose anchor could not be
    resolved. Annotations are added directly on ``doc`` (call ``doc.save``
    afterwards).
    """
    placed = 0
    failures = []
    for remark in remarks:
        try:
            page_index, point = resolve_anchor(doc, line_index, remark)
        except AnchorResolutionError as exc:
            failures.append((remark, str(exc)))
            continue
        page = doc[page_index]
        annot = page.add_text_annot(point, remark["remark"], icon="Comment")
        info = {}
        if author:
            info["title"] = author
        if remark.get("chapter"):
            info["subject"] = remark["chapter"]
        if info:
            annot.set_info(**info)
        annot.update()
        placed += 1
    return placed, failures
