"""Annotate a line-numbered PDF with review remarks written in a small,
line-number-aware Markdown format."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("annotate-pdf-from-remarks")
except PackageNotFoundError:
    # Running from a source checkout that was never installed (not even
    # via `pip install -e .`): pyproject.toml's [project].version is the
    # single source of truth, but there is no installed distribution to
    # read it from.
    __version__ = "0.0.0+unknown"
