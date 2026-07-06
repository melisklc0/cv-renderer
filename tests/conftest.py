from pathlib import Path

import pytest

from cv_renderer.loader import _EXAMPLES, load_cv, load_labels, load_profile

# examples/ now ships inside the package (src/cv_renderer/examples).
EXAMPLES = Path(_EXAMPLES)


@pytest.fixture(autouse=True)
def isolate_cv_data(tmp_path, monkeypatch):
    """Force every test to read from examples/ and write to a throwaway tmp
    dir, never touching the real (gitignored) user-data/."""
    monkeypatch.setattr("cv_renderer.loader._USER_DATA", EXAMPLES)
    monkeypatch.setattr("cv_renderer.render._USER_DATA", EXAMPLES)
    monkeypatch.setattr("cv_renderer.render._OUT", tmp_path / "out")


@pytest.fixture
def example_cv():
    return load_cv("en")


@pytest.fixture
def example_profile():
    def _load(name: str = "general"):
        return load_profile(name)

    return _load


@pytest.fixture
def example_labels():
    def _load(lang: str = "en"):
        return load_labels(lang)

    return _load
