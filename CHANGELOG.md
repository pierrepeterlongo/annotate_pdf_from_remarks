# Changelog

## 0.1.4 — 2026-07-07

- The first-page report box now shows the raw, verbatim remarks-file
  line(s) that were skipped or could not be anchored -- not where they
  appear or why -- since that is what needs fixing. `remarks_parser`
  entries and warnings now carry that original source text (`raw`).
- Long raw lines wrap automatically (the PDF renderer already did this;
  now relied upon on purpose). The box is sized to what it actually
  contains, and overflows onto extra inserted pages, right after the
  first page, if it does not all fit on one.
- API change: `annotate.build_report_text` / `add_report_annotation` are
  replaced by `build_report_header`, `collect_report_entries`, and
  `add_report_annotations` (plural). `remarks_parser.parse_remarks`'s
  `warnings` are now dicts (`{"line": int, "raw": str}`) instead of
  pre-formatted strings.

## 0.1.3 — 2026-07-07

- `line_index`: the margin column is now auto-detected from the candidates
  themselves (clustering on their right edge, since numbering packages
  right-align the printed number) instead of relying solely on
  `--margin-frac` to pin it down precisely. `--margin-frac` is now just a
  coarse, rarely-tuned initial net; on the real test manuscript the index
  now comes out identical (1485 lines) for `--margin-frac` anywhere from
  0.15 to 0.45, instead of silently degrading as the value widens.
- `tests/test_data/build_sample_pdf.py`: the synthetic fixture now
  right-aligns its margin numbers, matching real `lineno` output (the
  previous left-aligned fixture could not have caught the above).

## 0.1.2 — 2026-07-07

- When any remarks-file line fails to parse, or any remark's anchor can't be
  resolved, that report is now also written as a visible, bordered box (a
  PDF FreeText annotation) on the first page of the output PDF, in addition
  to being printed on stderr. Nothing appears when the run is fully clean.
- `--author` and `--date` now default to the current OS login
  (`getpass.getuser()`) and today's date (ISO 8601) when not given, instead
  of being left blank.
- New `--date` option.

## 0.1.1 — 2026-07-07

Bug fixes found while running the tool on a real ~1500-line-numbered thesis.

- `line_index.build_line_index`: replaced the greedy monotonic walk with a
  proper longest-increasing-subsequence search. The greedy version could be
  permanently thrown off sequence by a single early false-positive digit
  span caught in the margin band (e.g. a citation or footnote number),
  silently losing every subsequent line number after that point. On the
  test manuscript this recovered 58 previously-missing line numbers.
- `remarks_parser`: the `find:"...":` syntax now tolerates whitespace after
  `find:` (`find: "...":` is accepted, not just `find:"...":`).
- `remarks_parser`: the `lNNN:` line-anchor syntax now accepts a plain space
  instead of a colon (`l366 remark text`), while still requiring at least
  one separator character so plain text is never mistaken for an anchor.

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
