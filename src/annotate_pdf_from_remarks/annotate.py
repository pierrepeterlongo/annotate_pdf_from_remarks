"""Resolve parsed remarks to PDF locations and write them as PDF comments."""

import datetime

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


def build_report_text(warnings, failures, author=None, date=None):
    """Build the text of the on-page report summarising everything that did
    NOT make it into a PDF annotation: remarks-file lines that failed to
    parse, and remarks whose anchor could not be resolved in the PDF.

    Returns ``None`` if there is nothing to report.
    """
    if not warnings and not failures:
        return None

    if date is None:
        date = datetime.date.today().isoformat()

    lines = ["Annotation report"]
    if author:
        lines.append(f"Author: {author}")
    lines.append(f"Date: {date}")

    if warnings:
        lines.append("")
        lines.append(f"{len(warnings)} remarks-file line(s) skipped (unrecognized syntax):")
        lines.extend(f"- {warning}" for warning in warnings)

    if failures:
        lines.append("")
        lines.append(f"{len(failures)} remark(s) could not be anchored in the PDF:")
        lines.extend(
            f"- {reason} (remark: {remark['remark'][:80]!r})"
            for remark, reason in failures
        )

    return "\n".join(lines)


def add_report_annotation(doc, text, page_index=0, margin=36, line_height=11, fontsize=8):
    """Add ``text`` as a bordered, filled-in text box directly on
    ``doc[page_index]`` (a PDF FreeText annotation) -- unlike the
    per-remark comments, its content is visible without clicking anything.
    """
    page = doc[page_index]
    n_lines = text.count("\n") + 1
    width = page.rect.width - 2 * margin
    height = min(n_lines * line_height + 2 * margin, page.rect.height - 2 * margin)
    rect = fitz.Rect(margin, margin, margin + width, margin + height)

    annot = page.add_freetext_annot(
        rect,
        text,
        fontsize=fontsize,
        text_color=(0, 0, 0),
        fill_color=(1, 1, 0.75),
        border_width=1,
        align=0,
    )
    annot.update()
    return annot
