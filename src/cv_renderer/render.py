from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Callable

import jinja2

from cv_renderer.filter import apply_profile
from cv_renderer.loader import _USER_DATA, load_cv, load_labels, load_profile

_ROOT = Path(__file__).parent.parent.parent
_TEMPLATES = _ROOT / "templates"
_OUT = _ROOT / "out"
_EXAMPLES = _ROOT / "examples"

def _make_fmtdate(months: list[str], present_label: str) -> Callable:

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


def render(profile_name: str, lang: str | None = None, export_pdf: bool = False, template: str | None = None) -> Path:
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
    env.filters["fmtdate"] = _make_fmtdate(context["labels"]["months"], context["labels"]["present"])

    template = env.get_template(f"{profile.template}.html.j2")
    html = template.render(**context)

    _OUT.mkdir(exist_ok=True)
    slug = profile_name.replace("/", "-")
    out_html = _OUT / f"{slug}.html"
    out_html.write_text(html, encoding="utf-8")

    if export_pdf:
        from cv_renderer.exports import export_pdf as do_export
        pdf_out = do_export(out_html)
        return pdf_out

    return out_html


def init() -> None:
    if _USER_DATA.exists():
        print(f"Already exists: {_USER_DATA}")
        print("Delete it first if you want to reinitialize.")
        return
    shutil.copytree(_EXAMPLES, _USER_DATA)
    print(f"Created {_USER_DATA} from examples/")
    print("Fill in your information, then run:")
    print("  uv run python render.py --profile general")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render CV from profile")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init", help="Create user-data/ from examples/")

    parser.add_argument("--profile", "-p", help="Profile name (e.g. ai-engineer)")
    parser.add_argument("--lang", help="Override language: en or tr")
    parser.add_argument("--template", "-t", help="Template name override (e.g. two-column)")
    parser.add_argument("--export", choices=["pdf"], help="Also export to PDF")
    parser.add_argument("--list", action="store_true", help="List available profiles")
    args = parser.parse_args()

    if args.command == "init":
        init()
        return

    if args.list:
        profiles_dir = _USER_DATA / "profiles"
        for p in sorted(profiles_dir.glob("**/*.yaml")):
            print(p.relative_to(profiles_dir).with_suffix(""))
        return

    if not args.profile:
        parser.error("--profile is required (or use --list to see options)")

    out = render(args.profile, lang=args.lang, export_pdf=args.export == "pdf", template=args.template)
    print(f"Rendered: {out}")


if __name__ == "__main__":
    main()
