from pathlib import Path

import pytest

from cv_renderer.render import render, render_cover_letter


def test_render_general_creates_html():
    out = render("general")
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "Professional Experience" in html
    assert "Your Name" in html


def test_render_ai_engineer_skill_category_order():
    out = render("ai-engineer")
    html = out.read_text(encoding="utf-8")
    expected_order = [
        "AI and LLM Systems",
        "ML and Evaluation",
        "Backend and API",
        "Infra and DevOps",
    ]
    positions = [html.index(cat) for cat in expected_order]
    assert positions == sorted(positions)
    assert "Data Engineering" not in html


def test_render_lang_override_uses_turkish_labels():
    out = render("general", lang="tr")
    html = out.read_text(encoding="utf-8")
    assert 'lang="tr"' in html
    assert "Profesyonel Deneyim" in html


def test_render_missing_profile_raises():
    with pytest.raises(FileNotFoundError):
        render("nonexistent-profile")


def _letter(tmp_path: Path, *paragraphs: str) -> Path:
    import yaml

    path = tmp_path / "letter.yaml"
    path.write_text(yaml.safe_dump({"paragraphs": list(paragraphs)}), encoding="utf-8")
    return path


def test_render_cover_letter_reuses_the_cv_header(tmp_path: Path):
    # Same identity block as the CV — name/title/contact come from the profile,
    # never from the letter file, so the two documents for one application
    # always agree on who is applying and for what title.
    letter = _letter(tmp_path, "First paragraph.", "Second paragraph.")
    out = render_cover_letter("ai-engineer", letter)
    html = out.read_text(encoding="utf-8")
    assert "Your Name" in html
    assert "First paragraph." in html
    assert "Second paragraph." in html
    assert "Dear " not in html  # no formal letterhead — just the header + body


def test_render_cover_letter_paragraphs_stay_separate(tmp_path: Path):
    letter = _letter(tmp_path, "First paragraph.", "Second paragraph.", "Third.")
    out = render_cover_letter("ai-engineer", letter)
    html = out.read_text(encoding="utf-8")
    # Each list item becomes its own <p>, not one run-on block.
    assert html.count("<p>First paragraph.</p>") == 1
    assert html.count("<p>Second paragraph.</p>") == 1
    assert html.count("<p>Third.</p>") == 1


def test_render_cover_letter_collapses_internal_line_breaks(tmp_path: Path):
    # A paragraph hand-wrapped with a YAML block scalar must not render broken.
    letter = _letter(tmp_path, "One line\nwrapped across\ntwo more.")
    out = render_cover_letter("ai-engineer", letter)
    html = out.read_text(encoding="utf-8")
    assert "One line wrapped across two more." in html


def test_render_cover_letter_missing_profile_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        render_cover_letter("nonexistent-profile", _letter(tmp_path, "Text."))


def test_render_cover_letter_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        render_cover_letter("ai-engineer", tmp_path / "gone.yaml")


def test_render_cover_letter_output_path_says_cover_letter(tmp_path: Path):
    out = render_cover_letter("ai-engineer", _letter(tmp_path, "Text."))
    assert out.name.endswith("_Cover_Letter.html")
