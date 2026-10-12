# Method: building a writing signature, step by step

Workspace layout (private; created in phase 1):

```
~/writing-signature-workspace/<slug>/
  decisions.md            # every author decision, dated
  raw/<source>/           # original files as given (pdf, docx, odt, txt, md)
  extracted/<source>/     # extract_text.py output
  clean/<source>/<section>/  # prose only; sections are optional
  control/raw|extracted|clean/  # other authors, same genre (optional)
  samples/                # sample.py output
  baseline/               # copied into the personal skill at phase 11
```

## 1. Intake ★

Ask, and write the answers in `decisions.md`:
- name and slug (`write-like-<slug>`);
- corpus language(s) and target language(s);
- what they will write with it (emails, essays, reports, articles, fiction, teaching material...): this decides
  the sections of the profile and which examples to keep;
- sources (e.g. "thesis", "lecture notes", "blog") and, for each, **how much was written with AI or edited by
  others** (supervisor, co-authors, editors). "100% mine" sources are the reference for the human voice.
- Aim for ≥ 20,000 words total; 5,000 is a usable minimum for the qualitative profile, not for numbers.

## 2. Extract

`$PY scripts/extract_text.py <workspace>/raw/<source> <workspace>/extracted/<source>`
- Check the word counts printed per file. A very low count means a scanned PDF or a broken file.
- Same name with different extensions does not overwrite (`name_odt.txt`); check whether they are duplicates
  (identical text) and keep one.
- Read 2-3 paragraphs of each extracted file before going on.

## 3. Provenance screening ★ (only sources that are not 100% the author's)

Follow `ai-screening.md`. Produce a table of suspected passages with evidence and let the author decide
EXCLUDE / KEEP for each. If the author says a flagged formula is theirs, record it: it goes into the
"allowed" list of the personal skill, never into anti-patterns.

## 4. Clean and split

- Long structured documents (thesis, report): split by section manually, removing the excluded passages,
  tables, lists of data, translated quotes, abstracts that only repeat the text.
- Notes and short documents: `$PY scripts/clean_prose.py extracted/<source> clean/<source> [--fix-typing] [--drop-pattern REGEX]`.
  Use `--fix-typing` only after the decision in phase 6. Check the "dropped" summary: prose should be > 85%.
- Exclude material that is not prose the author would show (code-heavy notes, bullet summaries).

## 5. Control group (optional, recommended)

Texts by other people in the same genre and topic (classmates' notes, colleagues' reports). Clean them with
**exactly the same steps** as the author's corpus. Never publish or copy them into the personal skill.
File metadata (author fields) is weak evidence of authorship: ask the author when in doubt; exclude if unsure.

## 6. Quirks ★

`$PY scripts/stylometry.py quirks clean/ control/clean/` (or on `extracted/` to see slips before cleaning).
Typing slips (space before punctuation, glued commas) are usually not wanted in polished text: ask.
Style quirks (pet phrases, quoting habits, constructions used far more than peers) are part of the signature:
list them in the profile with rates vs control.

## 7. Baselines

```
$PY scripts/stylometry.py baseline clean/<sourceA> clean/<sourceB> --lang <xx> -o baseline/combined.json
$PY scripts/stylometry.py baseline clean/<sourceA> --lang <xx> -o baseline/<sourceA>.json
$PY scripts/stylometry.py separate clean/<sourceA> control/clean --lang <xx>     # if a control exists
```
Fewer than 5 blocks → warn the author that z-scores are indicative. Note which metrics have |d| ≥ 0.8 in
`separate`: they are this author's strongest numeric signature.

## 8. Profile

`$PY scripts/sample.py clean/<source> -n 10 -o samples/<source>.md` (raise `--max` for long-paragraph writers).
Read samples AND full sections. Fill `templates/personal-skill/references/profile.md`; every claim needs a quoted
example from the corpus and, when available, a number from the baseline. Questions to answer:
1. Sentence rhythm: length distribution, how long sentences grow (subordinates, participles, lists, asides).
2. Paragraph openings: subject, data, circumstance, connective?
3. How an argument is built (claim → evidence → caveat? concession first?).
4. Asides and glosses: parentheses, "i.e.", definitions, translations of terms.
5. Recurring words and constructions; what they use LESS than peers.
6. Uncertainty: how much hedging, on what.
7. Person and voice: I / we / impersonal / passive, by genre.
8. Differences between sources/registers (one profile, differences listed, unless the author wants separate voices).
9. What they never do.

## 9. Examples

6-12 excerpts of 300-500 words, covering the genres the author will write, only from passages certainly theirs.
Keep original wording (typing slips may stay; the skill is told not to copy them).

## 10. Target language different from the corpus ★

Follow `constrained-translation.md`: anchor text written by the author, decisions on accent/imprint,
constructions map, constrained translation of 4-6 examples, `check_translation.py`, structural baseline.

## 11. Generate the personal skill

Copy `templates/personal-skill/` to `~/.claude/skills/write-like-<slug>/`, replace every `{{PLACEHOLDER}}`,
copy `baseline/`, `references/examples/`, the filled `profile.md`, `quirks.md`, `antipatterns.md`
(defaults from `references/antipatterns-<lang>.md` minus the author's allowed phrases), and the target-language
file if any. Scripts are referenced from this meta-skill (single copy). Run `grep -r "{{" ` on the result: no hits.

## 12. Validate ★

1. Write a 300-500 word draft on a topic NOT in the corpus, following the personal skill.
2. `compare` it against `combined.json`; revise reliable-metric deviations, FOREIGN connectives, anti-patterns.
3. Record before/after numbers in `<workspace>/validation.md`.
4. Blind test: the author's own unseen text, the skill's draft, plain Claude's draft on the same topic. Ask the
   author (or a colleague) to rank them. If the skill's draft is spotted at once, ask what gave it away and
   update the profile.
