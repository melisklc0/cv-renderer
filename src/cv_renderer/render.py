from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Callable

import jinja2
import yaml

from cv_renderer.filter import apply_profile
from cv_renderer.lint import exit_code, format_json, format_report, lint
from cv_renderer.loader import _USER_DATA, load_cv, load_labels, load_profile
from cv_renderer.models import CoverLetterContent

# templates/ and examples/ ship inside the package so the installed wheel is
# self-contained (they used to live at the repo root).
_PACKAGE = Path(__file__).parent
_TEMPLATES = _PACKAGE / "templates"
_OUT = Path(os.environ["CV_OUT_DIR"]) if "CV_OUT_DIR" in os.environ else _USER_DATA / "out"
_EXAMPLES = _PACKAGE / "examples"


def _make_fmtdate(months: list[str], present_label: str) -> Callable[[str | int], str]:

    def fmtdate(d: str | int) -> str:
        s = str(d)
        if s.lower() == "present":
            return present_label
        if "-" in s:
            year, month = s.split("-", 1)
            try:
                return f"{months[int(month) - 1]} {year}"
            except (ValueError, IndexError):
                return s
        return s

    return fmtdate


def _to_title_slug(s: str) -> str:
    return "_".join(w.title() for w in s.replace("-", " ").replace("/", " ").split())


def _resolve_out_path(profile_name: str, full_name: str, lang: str, kind: str = "CV") -> Path:
    # Directories mirror the full profile path (out/companies/spotify/), but the
    # filename drops the "companies/" grouping — it doesn't belong in a CV filename.
    profile_dir = _OUT / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    slug_source = profile_name.removeprefix("companies/")
    base = f"{_to_title_slug(full_name)}_{_to_title_slug(slug_source)}_{lang.upper()}_{kind}"
    path = profile_dir / f"{base}.html"
    if path.exists():
        v = 2
        while (profile_dir / f"{base}_v{v}.html").exists():
            v += 1
        path = profile_dir / f"{base}_v{v}.html"
    return path


def render(
    profile_name: str,
    lang: str | None = None,
    export_pdf: bool = False,
    template: str | None = None,
) -> Path:
    profile = load_profile(profile_name)
    if lang:
        profile.lang = lang
    if template:
        profile.template = template

    cv = load_cv(profile.lang)
    labels = load_labels(profile.lang)
    context = apply_profile(cv, profile, labels)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES)),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    env.filters["fmtdate"] = _make_fmtdate(
        context["labels"]["months"], context["labels"]["present"]
    )

    jinja_template = env.get_template(f"{profile.template}.html.j2")
    html = jinja_template.render(**context)

    # Name comes from the rendered context, not the base data, so a profile's
    # name_override renames the file too — a CV and its filename should match.
    out_html = _resolve_out_path(profile_name, context["meta"]["name"], profile.lang)
    out_html.write_text(html, encoding="utf-8")

    if export_pdf:
        from cv_renderer.exports import export_pdf as do_export

        pdf_out = do_export(out_html)
        return pdf_out

    return out_html


def load_cover_letter(path: Path) -> CoverLetterContent:
    if not path.exists():
        raise FileNotFoundError(f"cover letter file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return CoverLetterContent.model_validate(data)


def render_cover_letter(
    profile_name: str,
    cover_letter_path: Path,
    lang: str | None = None,
    export_pdf: bool = False,
) -> Path:
    """Render a cover letter using the same header (name/title/contact) as the CV
    for this profile — one application, one consistent identity block.

    `cover_letter_path` is a small YAML file (`CoverLetterContent`: a
    `paragraphs` list) — no name, no "Dear ..." block, no "Sincerely": the
    template supplies all of that from the profile/base data, exactly like the
    CV's header is never something a profile writes itself.
    """
    profile = load_profile(profile_name)
    if lang:
        profile.lang = lang

    cv = load_cv(profile.lang)
    labels = load_labels(profile.lang)
    # Reused wholesale for `meta` (name/title/location/contact) — the rest of the
    # context (experience, skills...) is computed and simply unused here.
    context = apply_profile(cv, profile, labels)
    content = load_cover_letter(cover_letter_path)
    paragraphs = [" ".join(p.split()) for p in content.paragraphs if p.strip()]

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES)),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    jinja_template = env.get_template("cover_letter.html.j2")
    html = jinja_template.render(
        meta=context["meta"],
        font_family=context["font_family"],
        font_sizes=context["font_sizes"],
        lang=profile.lang,
        paragraphs=paragraphs,
    )

    out_html = _resolve_out_path(
        profile_name, context["meta"]["name"], profile.lang, kind="Cover_Letter"
    )
    out_html.write_text(html, encoding="utf-8")

    if export_pdf:
        from cv_renderer.exports import export_pdf as do_export

        return do_export(out_html)
    return out_html


def init() -> None:
    if _USER_DATA.exists():
        print(f"Already exists: {_USER_DATA}")
        print("Delete it first if you want to reinitialize.")
        return
    shutil.copytree(_EXAMPLES, _USER_DATA)
    print(f"Created {_USER_DATA} from examples/")
    print("Fill in your information, then run:")
    print("  cv-renderer --profile general")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render CV from profile")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init", help="Create user-data/ from examples/")

    parser.add_argument("--profile", "-p", help="Profile name (e.g. ai-engineer)")
    parser.add_argument("--lang", help="Override language: en or tr")
    parser.add_argument("--template", "-t", help="Template name override (e.g. two-column)")
    parser.add_argument(
        "--cover-letter",
        metavar="YAML_PATH",
        help="Render a cover letter instead of a CV. YAML_PATH is a small file "
        "with a `paragraphs:` list — the header comes from --profile, same "
        "identity block as the CV.",
    )
    parser.add_argument("--export", choices=["pdf"], help="Also export to PDF")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    parser.add_argument("--lint", action="store_true", help="Validate CV data without rendering")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Lint report format (json is machine-readable, for external callers)",
    )
    args = parser.parse_args()

    if args.command == "init":
        init()
        return

    if args.list:
        profiles_dir = _USER_DATA / "profiles"
        for p in sorted(profiles_dir.glob("**/*.yaml")):
            print(p.relative_to(profiles_dir).with_suffix(""))
        return

    if args.lint:
        findings = lint(args.profile)
        print(format_json(findings) if args.format == "json" else format_report(findings))
        # 0 = clean, 1 = errors, 2 = warnings only — callers can branch on this.
        raise SystemExit(exit_code(findings))

    if not args.profile:
        parser.error("--profile is required (or use --list to see options)")

    try:
        if args.cover_letter:
            out = render_cover_letter(
                args.profile,
                Path(args.cover_letter),
                lang=args.lang,
                export_pdf=args.export == "pdf",
            )
        else:
            out = render(
                args.profile,
                lang=args.lang,
                export_pdf=args.export == "pdf",
                template=args.template,
            )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise SystemExit(1)
    print(f"Rendered: {out}")


if __name__ == "__main__":
    main()
