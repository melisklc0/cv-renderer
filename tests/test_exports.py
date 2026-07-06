from cv_renderer.exports import export_pdf
from cv_renderer.render import render


def test_export_pdf_produces_a_real_pdf_file():
    html_path = render("general")
    pdf_path = export_pdf(html_path)

    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.read_bytes()[:5] == b"%PDF-"


def test_render_export_pdf_flag_returns_pdf_path():
    pdf_path = render("general", export_pdf=True)
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.exists()
