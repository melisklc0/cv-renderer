import pytest

from cv_renderer.loader import load_cv, load_labels, load_profile, load_tags
from cv_renderer.models import CVData, Profile


def test_load_cv_en():
    cv = load_cv("en")
    assert isinstance(cv, CVData)


def test_load_cv_tr():
    cv = load_cv("tr")
    assert isinstance(cv, CVData)


def test_load_profile_general():
    profile = load_profile("general")
    assert isinstance(profile, Profile)
    assert profile.name == "General"


def test_load_profile_ai_engineer():
    profile = load_profile("ai-engineer")
    assert profile.focus_tags == ["ai", "llm", "ml"]


def test_load_profile_missing_raises():
    with pytest.raises(FileNotFoundError, match="not found"):
        load_profile("does-not-exist")


def test_load_labels_en_keys():
    labels = load_labels("en")
    assert {"months", "about", "experience", "present"} <= labels.keys()


def test_load_tags_matches_vocabulary_in_use():
    tags = load_tags()
    used_in_example_data = {"ai", "llm", "ml", "data", "backend", "devops", "always"}
    assert used_in_example_data <= tags.keys()


def test_missing_user_data_root_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("cv_renderer.loader._USER_DATA", tmp_path / "nonexistent")
    with pytest.raises(FileNotFoundError, match="CV data directory not found"):
        load_cv("en")
