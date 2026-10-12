---
name: writing-signature
description: Use when someone wants Claude to learn their own writing voice from their past texts and produce a personal skill that writes like them, or wants to rebuild, extend, or validate such a personal writing-style skill.
---

# Writing Signature

Build a **personal writing skill** (`write-like-<name>`) from an author's own texts: a style profile, real excerpts,
a numeric baseline, and a draft checker. The author's voice is the target, not "sounding human".

**Only the author's own texts.** Never build a signature of someone else from their writing.

## Before starting

- Setup once: `bash <this skill>/scripts/setup.sh` (venv + spaCy models; needs `pandoc`, `pdftotext`).
  Python for every script below: `PY=<this skill>/.venv/bin/python`.
- Workspace (private, never inside this repo): `~/writing-signature-workspace/<slug>/`.
  Record every decision the author makes in `<workspace>/decisions.md` (date, question, answer).
- Read `references/method.md` for the detailed steps and `references/lessons.md` before any analysis.

## Phases (stop at every ★ and ask the author)

| # | Phase | Output |
|---|---|---|
| 1 | ★ Intake: name, languages (corpus / target), genres they will write, which sources, AI share of each source | `decisions.md` |
| 2 | Extract: `$PY scripts/extract_text.py raw/<source> extracted/<source>` | plain text |
| 3 | ★ Provenance screening of mixed sources (`references/ai-screening.md`): flag passages, author decides | excluded passages |
| 4 | Clean and split by section/register (`scripts/clean_prose.py`, manual split for long structured documents) | `clean/<source>/...` |
| 5 | Control group (optional, recommended): same-genre texts by other people, cleaned **the same way** | `control/` |
| 6 | ★ Quirks: `stylometry.py quirks`; author decides whether typing slips are reproduced | `decisions.md` |
| 7 | Baselines: combined + per source (`stylometry.py baseline`); with control, run `separate` | `baseline/*.json` |
| 8 | Profile: `scripts/sample.py`, read samples + baselines, fill `templates/personal-skill/references/profile.md` | profile |
| 9 | Examples: 6-12 excerpts of 300-500 words, only from passages certainly written by the author | `references/examples/` |
| 10 | ★ Target language differs from corpus: anchor text + constrained translation (`references/constrained-translation.md`) | target-language layer |
| 11 | Generate the personal skill from `templates/personal-skill/` into `~/.claude/skills/write-like-<slug>/` | personal skill |
| 12 | ★ Validate: draft on a new topic → `compare` → revise; blind test with the author | `validation.md` |

## Quick reference: what the checker can trust

| Reliable (use to revise) | Informative only |
|---|---|
| sentence-length CV and SD, p90 | Burrows' Delta (often fails to separate an author from peers on shared topics) |
| commas and parentheses per 1000 words | single z-scores on drafts < 250 words |
| sentence-initial connectives; FOREIGN connectives | metrics a `separate` run shows with \|d\| < 0.5 |
| anti-pattern hits | |

## Common mistakes

- Treating ordinary formulas of the genre ("further studies are needed") as AI markers: ask before banning them.
- Building the baseline before removing AI-written or co-author passages.
- Comparing a cleaned author corpus with an uncleaned control: paragraph metrics become meaningless.
- Trusting PDF text without checking: a missing word may be an extraction artifact, not the author's habit.
- Calling the first draft done: first drafts usually have uniform sentence length (CV ~0.2 vs human ~0.5).
- Writing the personal skill's description as a workflow summary instead of trigger conditions.
