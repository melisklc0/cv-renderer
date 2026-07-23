# Answering Pre-Screening Questions

Reference for writing answers to the pre-screening / application questionnaires that
appear *before* the first interview — the short forms and open-text prompts on job
portals. This is about **how to answer as a candidate**, not about CV formatting or ATS
parsing (see `xyz-format-in-resumes.md` and `harvard-resume-writing-guide.md` for the CV
itself).


## Two things a questionnaire is doing

- **Filtering (knockouts).** Binary, pass/fail. Work authorization, language level, salary
  band, notice period, timezone. No points for eloquence — just clear the bar or get cut.
  Answer these with precision and zero hedging.
- **Evaluation.** The open-ended questions. Ranked, comparative. This is where the answer's
  structure, specificity, and quantified evidence decide whether you advance. Treat every
  evaluation answer as a competitive writing sample, not a form field.

Know which type you're answering before you write. Padding a knockout wastes the reader's
time; under-answering an evaluation question reads as shallow expertise.


## How long should the answer be

Reviewers spend ~30–60 seconds on a first pass. Lead with the substance; cut every
warm-up phrase ("That's a great question…", "I would say that…").

| Prompt type | Target length | Notes |
|---|---|---|
| Short logistical/experiential form field | 50–100 words | A few tight sentences. Answer the core, stop. |
| Formal scenario / "selection criteria" | 300–400 words | Under 300 reads as insufficient depth; over ~1 page reads as inability to synthesize. |
| Open intro / summary / cover-letter prompt | 250–400 words, 3–4 paragraphs | Scale by seniority (below). |

When a hard word limit is enforced, write to within **10–15% of the maximum** — use the
space, don't leave it on the table, but don't trip the limit.

**Cover-letter-style prompt, by career stage:**
- Early-career: 150–250 words — adaptability, foundational skills, mission alignment.
- Mid-career technical: 250–350 words — 2–3 quantified achievements mapped to the JD.
- Senior/architecture: 300–400 words — room for systemic narrative, still under one page.


## Written STAR (the default structure for evaluation answers)

STAR works in writing even better than in interviews, because you control the pacing. Hold
these proportions:

| Component | Share | What goes here |
|---|---|---|
| **Situation** | 10–15% | Context + the specific problem, objectively. No company history. |
| **Task** | ~10% | Your specific mandate. "What was expected of *you*." |
| **Action** | 50–60% | The core. Concrete methods, tools, logic. Active verbs. Separate *your* contribution from the team's. |
| **Result** | 20–25% | Quantified outcome (%, hours saved, error rate). Optionally a one-line systemic lesson. |

The Action section is where you're actually scored — spend the words there, not on setup.


## The seven question archetypes

Each archetype extracts one specific signal. Answer to the hidden intent, not the surface
wording.

### 1. Behavioral profiling — "Tell us about yourself / your work style"
**Intent:** self-awareness and fit, not a résumé recital.
**Answer:** ~100–150 words. Open with a core identity line ("Data operations specialist
focused on resilient automated pipelines"), then 2–3 work-style traits that matter for
*this* role (methodological rigor, proactive async communication, edge-case discipline),
each anchored to a brief real success. Show the trait pays off; don't just claim it.

### 2. Project ownership — "A project you're proud of. Your role? Solo or team?"
**Intent:** real depth vs. borrowed credit; where your boundary was.
**Answer:** Name the substantive technical challenge (legacy data migration, third-party
API rate limits, conflicting stakeholder requirements — not a superficial hurdle). Draw the
line between team output and *your* locus of control ("as part of the product team, I owned
the ETL pipeline / the API integration logic"). Show persistence and a systematic approach,
end on a quantified result. Balanced credit is a green flag; inflated solo claims are a
red flag.

### 3. Anomaly detection — "You spotted a wrong number in a report. How did you trace and fix it?"
**Intent:** technical troubleshooting **and** stakeholder diplomacy at once. For data /
BI / reconciliation roles this is often the most important question.
**Answer:** Start at the moment you caught it (detail orientation). In the Action, walk an
auditable trace — SQL logic, API endpoints, transformation models, raw JSON/CSV payloads —
to the exact corruption point. Resolve it *without blaming* a colleague or team; align
everyone on a single source of truth. In the Result, go past the one-off fix to a systemic
safeguard (parity tests, validation thresholds, data-governance rules) that stops recurrence.

### 4. AI literacy — "How do you use AI tools? A time one gave you wrong output and you caught it."
**Intent:** a trap for people who treat AI as an infallible oracle. They want a director of
AI, not a passive consumer.
**Answer:** Specific, pragmatic use cases (boilerplate, structured extraction from
unstructured text, automating reconciliation, prompt-driven prototyping). Then the
differentiator: a concrete instance where a tool produced wrong data / flawed code / an
invalid conclusion, and the exact audit that caught it — cross-referencing primary sources,
unit tests on generated code, logic validation before production. Message: AI is a
multiplier, human verification is the non-negotiable arbiter.

### 5. Intrinsic motivation — "A skill/tool you learned recently on your own. Why?"
**Intent:** autonomous, continuous learning and what actually drives you.
**Answer:** Pick one specific, relevant technology (a data-orchestration tool, a cloud
pattern, an ML library) — not something an employer mandated, not vague "interest." Then
dig into the *why*: a real bottleneck you wanted to solve ("our manual reporting was
unsustainable, so I automated it"). Self-directed projects, certifications, or open-source
contributions are strong green flags.

### 6. Hard-skills validation — "Your experience level with SQL, JS/Apps Script, REST APIs"
**Intent:** applied depth behind résumé claims; can you operate autonomously in the stack.
**Answer:** No vague "I'm good at SQL." Give concrete production examples:
- **SQL:** window functions, complex multi-table joins, query optimization for load.
- **Scripting/automation:** the workflows you built — inputs, transformation logic, outputs.
- **REST APIs:** auth protocols, pagination, parsing JSON/XML, graceful rate-limit handling.

### 7. Logistical knockouts — language, hours, salary, notice period
**Intent:** binary gate. Precision, transparency, brevity.
- **Language / schedule:** confirm capability plainly if the role needs it (advanced written
  English, US-timezone/async). Inflating it guarantees a worse rejection later.
- **Salary:** never "Negotiable" — filters screen against the band and reviewers need a
  number for ROI. Give a specific, market-researched figure or a tight range, with currency.
- **Notice period:** be honest; it signals reliability and respects their timeline.


## Tone and presentation

- **Show, don't tell.** Give evidence that forces the reviewer to *conclude* you're good,
  instead of declaring it. Generic corporate clichés and obviously AI-generated,
  personality-free text are easy to spot and damage credibility.
- **Own weaknesses without defensiveness.** If asked about a failure or a gap, take full
  ownership, don't disparage past employers, and state the corrective action you took. That
  reads as a growth mindset.
- **Proofread ruthlessly.** A single typo in an otherwise strong answer shouldn't sink you
  and shouldn't panic you — but clean, error-free text signals conscientiousness, which
  matters doubly for remote/async roles.
- **Use the optional fields.** Portfolio / GitHub / project links are marked optional but
  are high-value: they convert claims into proof. Link clean, documented work.


## The profile you're building across all answers

The answers aren't independent — together they should project one coherent professional:

- **Analytical mind** — structured answers, precise vocabulary, root-cause focus.
- **Empirical operator** — quantified metrics in every Result.
- **Autonomous learner** — self-directed upskilling, self-auditing of AI/automation output.
- **Collaborative diplomat** — fair credit in team stories, non-adversarial conflict/anomaly
  resolution.
