# annotate-pdf-from-remarks

Turn a plain-text list of review remarks into native PDF comment
annotations, placed automatically next to the line, figure, or heading they
refer to.

Version: **0.1.0** (see [CHANGELOG.md](CHANGELOG.md)).

## Requirement: the PDF must carry printed line numbers

This tool locates most remarks by their **printed margin line number** — the
small number LaTeX's [`lineno`](https://ctan.org/pkg/lineno) package prints
next to every line when the document is compiled with:

```latex
\usepackage{lineno}
...
\begin{document}
\linenumbers
```

Line numbers must increase monotonically through the document (the
`lineno` default: no reset per page or per chapter). If the PDF has no
printed line numbers, `l<N>:` anchors cannot be resolved — use `find:"..."`
anchors instead (see below), which only require the literal text to be
searchable in the PDF (i.e. not a scanned image).

## Installation

Requires Python ≥ 3.9.

```bash
git clone <this-repository> annotate_pdf_from_remarks
cd annotate_pdf_from_remarks
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install .
```

For development (to also run the test suite):

```bash
pip install -e ".[test]"
pytest
```

## Usage

```bash
annotate-pdf-from-remarks \
  --pdf manuscript.pdf \
  --remarks remarks.md \
  --output manuscript_annotated.pdf \
  --author "Jane Doe"
```

This writes `manuscript_annotated.pdf`, a copy of `manuscript.pdf` with one
native PDF comment (sticky-note) annotation per remark, readable in any PDF
viewer (Preview, Acrobat, Foxit, `evince`, ...).

`--author` and `--date` are optional: if not given, they default to the
current OS login (`getpass.getuser()`) and today's date (ISO 8601),
respectively.

If anything was skipped — a remarks-file line that failed to parse, or a
remark whose anchor could not be resolved in the PDF — it is, in addition
to being printed on stderr, also written into a visible, bordered box
(a PDF FreeText annotation) on the **first page** of the output PDF, along
with the author and date. This box only appears when there is something to
report; a fully clean run adds no such box.

Run `annotate-pdf-from-remarks --help` for all options, notably:

- `--dump-index FILE`: write the detected `{line_number: [page, bbox]}` map
  to a JSON file, to debug why a given `l<N>:` anchor did not resolve.
- `--margin-frac` / `--max-forward-jump`: tune the margin-detection heuristic
  (see "How line-number detection works" below) if your layout is unusual
  (e.g. very wide margins, or a document that legitimately jumps by more
  than 500 in its line numbering across a single gap).

The command prints a summary (line numbers detected, annotations placed)
and exits with a non-zero status if any remark could not be parsed or
anchored — those cases are always reported on stderr, never silently
dropped.

## Remarks file syntax

One remark per entry, in a plain-text/Markdown file:

```
## Chapter One

l87: this sentence is unclear
	the definition should come first

find:"Figure 1.2":the caption is too generic

find:"Figure 1.2",page=9,occurrence=1:this is the second, duplicate caption
```

- **`l<N>: text`** — anchors the remark to printed margin line number `N`
  (case-insensitive `l`/`L`; the colon can be replaced by a plain space,
  e.g. `l87 this sentence is unclear`, but at least one separator character
  is required).
- **`find:"literal text":text`** — anchors the remark to the first place in
  the document where `literal text` appears verbatim (matching is
  case-insensitive). Use this for figures, section headings, definitions,
  or anything not tied to a specific line number. Whitespace after `find:`
  is tolerated (`find: "literal text": text` also works), but the quotes
  and the final `:` before the remark text are mandatory.
  - `find:"literal text",page=P:text` restricts the search to (0-indexed)
    page `P`.
  - `find:"literal text",page=P,occurrence=K:text` picks the `K`-th
    (0-indexed) match on that page (or in the whole document if `page` is
    omitted), for text that appears more than once.
- **`## Chapter name`** — a cosmetic label attached (as the annotation's
  "subject") to every remark that follows, until the next `##` line. Not an
  anchor.
- A line starting with **whitespace** continues the previous remark (its
  text is appended on a new line) — use this to wrap a long remark or add a
  second point about the same anchor.
- Blank lines separate remarks.
- Any other line is reported as an unrecognized-syntax warning and skipped
  — it is never silently merged into the previous remark or dropped without
  a trace.

## How line-number detection works

PDFs carry no semantic tag for "this is a line number", so detection is
heuristic (see `src/annotate_pdf_from_remarks/line_index.py` for the exact
algorithm):

1. Collect every text line made of a single span whose text is only digits
   and which sits in the outer margin (leftmost/rightmost `--margin-frac` of
   the page width — both edges are checked, to handle mirrored margins in
   double-sided layouts).
2. Read those candidates in page/vertical order and keep only the ones that
   form a strictly increasing sequence, tolerating gaps (e.g. across a
   full-page figure) but rejecting any jump larger than `--max-forward-jump`
   or any non-increasing value — this discards footnote markers, equation
   numbers, or other small digits that happen to sit in the margin band.

This is a best-effort heuristic, not a guarantee: always check the CLI's
summary output (and, if anchors go missing, `--dump-index`) after a run.

## Supported platforms

Pure Python, no shelling out to external binaries (no LaTeX/`pdflatex`
needed to *run* the tool — only to *produce* a line-numbered PDF in the
first place, if you don't already have one). Runs anywhere Python ≥ 3.9 and
the [PyMuPDF](https://pypi.org/project/pymupdf/) wheel are available:
Linux (x86_64/arm64), macOS (Intel/Apple Silicon), and Windows (x64).

## Tests

A minimal test suite lives under `tests/`. It generates its own tiny
synthetic PDF at test time (`tests/test_data/build_sample_pdf.py`, via
PyMuPDF) so it needs no LaTeX installation and no checked-in binary
fixture:

```bash
pip install -e ".[test]"
pytest
```

## License

[GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later).
