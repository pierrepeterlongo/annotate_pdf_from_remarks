"""Parse a remarks file into a list of anchored remarks.

Supported syntax, one remark per logical entry:

``l87: some remark``
    Anchors the remark to printed margin line number 87 (case-insensitive
    ``l``/``L``).

``find:"Figure 1.2":some remark``
    Anchors the remark to the first occurrence, anywhere in the document, of
    the literal text ``Figure 1.2``.

``find:"Figure 1.2",page=9:some remark``
    Same, but restricted to (0-indexed) page 9.

``find:"Figure 1.2",page=9,occurrence=1:some remark``
    Same, but the second (0-indexed ``occurrence=1``) match on that page.

``## Chapter name``
    Not a remark: labels every remark that follows (until the next ``##``
    line) with that chapter name, stored in the ``chapter`` field for
    traceability. Purely cosmetic.

A line that starts with whitespace continues the previous remark's text
(joined with a newline), which lets a remark span several lines. Blank lines
are ignored. Any other non-blank line that does not match one of the two
anchor syntaxes above is reported as a warning and skipped, rather than
silently dropped or silently merged into the previous remark.
"""

import re

_LINE_ANCHOR_RE = re.compile(r"^[lL](\d+)\s*:\s*(.*)$")
_FIND_ANCHOR_RE = re.compile(
    r'^find:"(?P<text>(?:[^"\\]|\\.)*)"'
    r"(?:,\s*page=(?P<page>\d+))?"
    r"(?:,\s*occurrence=(?P<occurrence>\d+))?"
    r"\s*:\s*(?P<remark>.*)$"
)
_CHAPTER_RE = re.compile(r"^#{1,6}\s*(.+?)\s*$")


def _unescape(text):
    return text.replace('\\"', '"').replace("\\\\", "\\")


def parse_remarks(text):
    """Parse remarks-file content. Returns ``(remarks, warnings)``.

    Each entry in ``remarks`` is a dict with keys ``chapter`` and ``remark``,
    plus either ``line`` (int) for a line-number anchor, or ``find``,
    ``page`` (``None`` or int) and ``occurrence`` (int, default 0) for a
    text-search anchor.
    """
    remarks = []
    warnings = []
    chapter = None
    current = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            current = None
            continue

        if raw_line[0].isspace() and current is not None:
            current["remark"] += "\n" + raw_line.strip()
            continue

        chapter_match = _CHAPTER_RE.match(raw_line)
        if chapter_match:
            chapter = chapter_match.group(1)
            current = None
            continue

        line_match = _LINE_ANCHOR_RE.match(raw_line)
        if line_match:
            current = {
                "chapter": chapter,
                "line": int(line_match.group(1)),
                "remark": line_match.group(2).strip(),
            }
            remarks.append(current)
            continue

        find_match = _FIND_ANCHOR_RE.match(raw_line)
        if find_match:
            current = {
                "chapter": chapter,
                "find": _unescape(find_match.group("text")),
                "page": (
                    int(find_match.group("page"))
                    if find_match.group("page") is not None
                    else None
                ),
                "occurrence": (
                    int(find_match.group("occurrence"))
                    if find_match.group("occurrence") is not None
                    else 0
                ),
                "remark": find_match.group("remark").strip(),
            }
            remarks.append(current)
            continue

        warnings.append(f"line {lineno}: unrecognized syntax, skipped: {raw_line!r}")
        current = None

    return remarks, warnings


def parse_remarks_file(path):
    """Convenience wrapper: read ``path`` and parse its content."""
    with open(path, encoding="utf-8") as f:
        return parse_remarks(f.read())
