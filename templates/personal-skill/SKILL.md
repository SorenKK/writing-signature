---
name: write-like-{{SLUG}}
description: Use when {{NAME}} asks to write or rewrite text "like me", "in my style", "as I would write it", or to make a draft sound like their own voice, in {{LANGUAGES}}.
---

# Write like {{NAME}}

Target: how {{NAME}} writes when they want to write well ({{GENRES}}). Sources: {{SOURCES}}.
{{TARGET_LANGUAGE_LINE}}

## Procedure

1. Read `references/profile.md`, `references/antipatterns.md`, `references/quirks.md`.
   {{TARGET_LANGUAGE_READ}}
2. Read 1-2 excerpts in `references/examples/` closest to the requested genre. Imitate rhythm and moves, not
   content. Excerpts may contain the author's typing slips: do not copy them unless `quirks.md` says so.
3. Write the draft. Priorities, in order:
{{PRIORITIES}}
4. Save the draft to a file and check it:
   ```
   PY={{PYTHON}}
   $PY {{META_SKILL_DIR}}/scripts/stylometry.py compare draft.txt {{SKILL_DIR}}/baseline/combined.json --antipatterns {{SKILL_DIR}}/references/antipatterns.md
   ```
{{EXTRA_BASELINES}}
   Revise, in order: anti-pattern hits and FOREIGN connectives; deviations on metrics marked `*`; other
   deviations only if the genre does not explain them. Delta is informative only. Under 250 words, trust the
   profile more than the numbers. A first draft usually has too-uniform sentence length: expect to revise.
5. Re-read asking "would {{NAME}} have written this?". Deliver the text without style commentary unless asked.

## Never

- Reproduce typing slips that `quirks.md` marks as "do not reproduce".
- Remove phrases listed as **allowed** in `antipatterns.md`: they are the author's.
- Split long sentences "for clarity", add summary closings, or use the em dash.
- For texts the author will submit (school, journals, employers), remind them to follow the applicable rules on
  disclosing AI assistance.
