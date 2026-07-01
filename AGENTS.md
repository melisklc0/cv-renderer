# AGENTS.md

You are working on cv-renderer: a profile-driven CV renderer that produces tailored HTML and PDF exports from a single YAML data source.

## How to Work

- Read `user-data/data/base_en.yaml` before touching any CV content or generating profiles — the live data is the source of truth for tags, bullets, and skill categories.
- Before writing or editing bullets, read `AGENTS.md` and the two files under `docs/references/`.
- Keep changes scoped. A profile change should not touch the template; a bullet edit should not touch filter logic.

## Before Changing Common Areas

- **Data files** (`base_en.yaml`, `base_tr.yaml`): structural keys and tags are always English, even in `base_tr.yaml`. Never add a tag that doesn't belong to the vocabulary without checking with the user first.
- **Filter logic** (`src/cv_renderer/filter.py`): changes here affect every profile. Inspect existing behavior before modifying.
- **Template** (`templates/main.html.j2`): visual-only changes. No content or data logic belongs here.
- **Profile schema** (`src/cv_renderer/models.py`): adding a field requires updating examples and docs.

## Critical Rules for CV Content

- Every bullet must follow the XYZ formula. Read `docs/references/xyz-format-in-resumes.md`.
- Every bullet must follow Harvard OCS language rules. Read `docs/references/harvard-resume-writing-guide.md`.
- No personal pronouns, no passive voice, no vague quantifiers in any bullet.
- Tags are the only interface between data and profiles. A bullet gets all tags that truthfully apply — multiple tags on one bullet is correct. Do not invent tags outside the current vocabulary unless the user asks.
- Skill items support the same tagging as bullets (`items: [{text, tags}, ...]`), not just the category-level `tags`. Leave an item untagged when it's generic (always shown); tag it when it should only surface for profiles focused on that tag.
- `user-data/` contains personal data. Never commit it to a public repo.

## Profile Generation

- Produce valid YAML matching the `Profile` schema in `src/cv_renderer/models.py`.
- Save company-specific profiles to `user-data/profiles/companies/<company>.yaml`.
- Do not add fields outside the schema.
- Company-specific wording (a summary pitch tailored to one job posting) belongs in that profile's `title_override` / `about_override` fields, never patched into `base_en.yaml`/`base_tr.yaml`. The base files stay the single, company-agnostic source of truth; only tag-based selection and per-application overrides live in profiles.
- Overrides are still real CV content: same XYZ/Harvard rules, no invented facts, and written natively in the profile's `lang` — never a literal translation from the other language file.
- Tag filtering only selects among existing bullets and includes/excludes whole entries — it cannot reframe an accomplishment. When a job or project is genuinely relevant to the target posting but its base bullets are framed the wrong way (e.g. an AI-tagged project whose data-access-security work matters to a data-engineering posting), rewrite those bullets in `experience_overrides` / `project_overrides` (keyed by `company` / project `name`) rather than editing the base data or forcing tags that don't truthfully apply. An override also forces the entry to appear even if its tags would otherwise exclude it — use this only when something in it is honestly relevant; if nothing is, leave it out and let tag filtering drop it.

## Checks

```bash
uv run ruff check .
uv run ruff format .
```

## References

Read when relevant:

```
AGENTS.md
docs/references/xyz-format-in-resumes.md
docs/references/harvard-resume-writing-guide.md
docs/roadmap.md
```
