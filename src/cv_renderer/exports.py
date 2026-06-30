from __future__ import annotations

from pathlib import Path


def export_pdf(html_path: Path) -> Path:
    from playwright.sync_api import sync_playwright

    pdf_path = html_path.with_suffix(".pdf")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri())
        page.emulate_media(media="print")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
        )
        browser.close()

    return pdf_path
