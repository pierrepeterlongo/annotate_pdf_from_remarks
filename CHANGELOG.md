# Changelog

## 0.1.0 — 2026-07-07

Initial release.

- Generic detection of printed margin line numbers in a PDF (`lineno`-style
  numbering), via a monotonic-sequence heuristic.
- Small remarks-file syntax: `lNNN: remark`, `find:"text",page=P,occurrence=K:
  remark`, `## Chapter` labels, indentation-based continuation lines.
- `annotate-pdf-from-remarks` CLI producing a copy of the PDF with one native
  PDF comment annotation per resolved remark.
- Unrecognized remark lines and unresolved anchors are reported, never
  silently dropped.
