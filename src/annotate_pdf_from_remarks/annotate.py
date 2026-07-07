"""Resolve parsed remarks to PDF locations and write them as PDF comments."""

import datetime
import math

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


def build_report_header(author=None, date=None):
    """Build the header block of the on-page report (see
    :func:`add_report_annotations`): title, author, date. No mention of
    warnings/failures counts -- those are conveyed by the raw lines
    themselves, added separately via ``collect_report_entries``.
    """
    if date is None:
        date = datetime.date.today().isoformat()
    lines = [
        "Annotation report -- the remarks-file lines below could not be "
        "placed as PDF comments:"
    ]
    if author:
        lines.append(f"Author: {author}")
    lines.append(f"Date: {date}")
    return "\n".join(lines)


def collect_report_entries(warnings, failures):
    """Verbatim remarks-file text for everything that did not make it into a
    PDF annotation: lines that failed to parse, and remarks whose anchor
    could not be resolved. Each entry is the original source text as-is
    (continuation lines included) -- no line number, no reason, just the
    raw line(s), since that is what the manuscript's author needs to see
    and fix.
    """
    entries = [warning["raw"] for warning in warnings]
    entries.extend(remark["raw"] for remark, _reason in failures)
    return entries


def _estimate_wrapped_line_count(text, fontsize, fontname, max_width):
    """Estimate how many visual (wrapped) lines ``text`` will occupy once
    laid out in a box of width ``max_width`` -- used only to size/paginate
    the report box; actual word-wrapping is done by the PDF renderer."""
    total = 0
    for physical_line in text.split("\n"):
        if not physical_line:
            total += 1
            continue
        width = fitz.get_text_length(physical_line, fontname=fontname, fontsize=fontsize)
        total += max(1, math.ceil(width / max_width))
    return total


def add_report_annotations(
    doc,
    header,
    entries,
    page_index=0,
    margin=36,
    line_height=11,
    fontsize=8,
    fontname="helv",
):
    """Write ``header`` followed by ``entries`` (one raw remarks-file entry
    per paragraph, long lines wrapped automatically by the PDF renderer)
    into one or more bordered, filled-in text boxes (PDF FreeText
    annotations), starting on ``doc[page_index]``.

    Each box is sized to what it actually contains, up to the page height.
    If everything does not fit on a single page, extra blank pages are
    inserted right after ``page_index`` to hold the rest.

    Returns the list of created annotations. Does nothing (returns ``[]``)
    if ``entries`` is empty.
    """
    if not entries:
        return []

    base_page = doc[page_index]
    box_width = base_page.rect.width - 2 * margin
    page_height = base_page.rect.height
    max_lines_per_box = max(1, int((page_height - 2 * margin) // line_height))

    pages_content = []
    current_blocks = []
    current_count = 0

    def push(block_text, block_line_count):
        nonlocal current_blocks, current_count
        if current_blocks and current_count + block_line_count > max_lines_per_box:
            pages_content.append(current_blocks)
            current_blocks = []
            current_count = 0
        current_blocks.append(block_text)
        current_count += block_line_count

    push(header, _estimate_wrapped_line_count(header, fontsize, fontname, box_width))
    for entry in entries:
        # +1 for the blank separator line before the next block.
        line_count = _estimate_wrapped_line_count(entry, fontsize, fontname, box_width) + 1
        push(entry, line_count)
    if current_blocks:
        pages_content.append(current_blocks)

    annots = []
    insert_at = page_index + 1
    for i, blocks in enumerate(pages_content):
        text = "\n\n".join(blocks)
        line_count = _estimate_wrapped_line_count(text, fontsize, fontname, box_width)
        height = min(line_count * line_height + margin, page_height - 2 * margin)

        target_page = base_page if i == 0 else doc.new_page(
            pno=insert_at, width=base_page.rect.width, height=base_page.rect.height
        )
        if i > 0:
            insert_at += 1

        rect = fitz.Rect(margin, margin, margin + box_width, margin + height)
        annot = target_page.add_freetext_annot(
            rect,
            text,
            fontsize=fontsize,
            fontname=fontname,
            text_color=(0, 0, 0),
            fill_color=(1, 1, 0.75),
            border_width=1,
            align=0,
        )
        annot.update()
        annots.append(annot)

    return annots
