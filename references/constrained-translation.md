# Target language different from the corpus

Use when the author will write in a language they have (almost) no texts in. Free translation by a model
imports the model's style; constrained translation keeps the author's structure.

## 1. Anchor text ★
Ask the author to write 300-500 words in the target language **without AI or translators**, ideally a text whose
original exists in the corpus (an abstract, a summary of a chapter). Speed over polish. Save it untouched in
`raw/<target>/`.

## 2. Decide the accent ★
Ask: "Your own accent (your structure, long sentences, natural calques) with correct grammar, or neutral native
prose with your structure?" Most authors who ask for a signature want the first.

## 3. Read the anchor against its original
List in the target-language file of the personal skill:
- **keep** (style): sentence length vs original, argument order, glosses in parentheses, punctuation habits,
  gerund/participle chains, Latinate vocabulary that is also correct in the target language;
- **fix** (speed): grammar, articles, verb patterns, spelling, calques a target reader would not understand
  (give the correction for each);
- **map**: the author's recurring constructions → their target-language rendering;
- remove default anti-patterns that collide with the map.
Correct the anchor following these rules; show 2 sentences to the author before correcting the rest.

## 4. Constrained translation of 4-6 examples
Rules: one sentence = one sentence; same paragraphs; same `; :` and parentheses; no added connectives,
adjectives or summaries; use the map. Save as `<section>_<name>.txt` and run:

`$PY scripts/check_translation.py <translations_dir> <examples_dir>`

Fix every NO (or explain it: abbreviations can fool the sentence counter).

## 5. Structural baseline
`$PY scripts/stylometry.py baseline <corrected anchor + translations> --lang <target> -o baseline/<target>.json`
Usually 3-5 blocks: tell the author it is indicative. Function-word metrics and Delta are meaningless on a
translation; the structural ones (sentence length, punctuation) are what it is for.
Every real text the author later writes in the target language should be added and the baseline rebuilt.
