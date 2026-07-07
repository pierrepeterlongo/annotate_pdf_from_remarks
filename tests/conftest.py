import importlib.util
from pathlib import Path

import pytest

_BUILDER_PATH = Path(__file__).parent / "test_data" / "build_sample_pdf.py"
_spec = importlib.util.spec_from_file_location("build_sample_pdf", _BUILDER_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
build_sample_pdf = _module.build_sample_pdf


@pytest.fixture
def sample_pdf_path(tmp_path):
    path = str(tmp_path / "sample.pdf")
    build_sample_pdf(path)
    return path
