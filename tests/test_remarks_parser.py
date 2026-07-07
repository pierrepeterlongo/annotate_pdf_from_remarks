from annotate_pdf_from_remarks.remarks_parser import parse_remarks


def test_line_anchor_with_continuation_and_chapter_label():
    text = """
## Chapter One

l3: this line could be phrased more precisely
\tcontinuation of the same remark
"""
    remarks, warnings = parse_remarks(text)

    assert warnings == []
    assert len(remarks) == 1
    assert remarks[0]["line"] == 3
    assert remarks[0]["chapter"] == "Chapter One"
    assert remarks[0]["remark"] == (
        "this line could be phrased more precisely\n"
        "continuation of the same remark"
    )


def test_find_anchor_with_page_and_occurrence():
    text = 'find:"Figure 1.2",page=9,occurrence=1:remove the duplicate caption'
    remarks, warnings = parse_remarks(text)

    assert warnings == []
    assert len(remarks) == 1
    remark = remarks[0]
    assert remark["find"] == "Figure 1.2"
    assert remark["page"] == 9
    assert remark["occurrence"] == 1
    assert remark["remark"] == "remove the duplicate caption"


def test_find_anchor_defaults_page_and_occurrence():
    text = 'find:"Figure 1.2":the caption is too general'
    remarks, _warnings = parse_remarks(text)

    assert remarks[0]["page"] is None
    assert remarks[0]["occurrence"] == 0


def test_unrecognized_line_is_reported_not_dropped_silently():
    text = "this line has no anchor prefix"
    remarks, warnings = parse_remarks(text)

    assert remarks == []
    assert len(warnings) == 1
    assert "unrecognized syntax" in warnings[0]


def test_blank_line_ends_a_continuation_block():
    text = "l1: first remark\n\n\tstray continuation with no preceding remark"
    remarks, warnings = parse_remarks(text)

    assert len(remarks) == 1
    assert remarks[0]["remark"] == "first remark"
    assert len(warnings) == 1
