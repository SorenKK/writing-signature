# Lessons (found while building a real signature; read before analysing)

## Metrics
- **Burrows' Delta did not separate the author from 9 peers writing on the same course** (leave-one-out author
  0.73 vs peers 0.72). Function-word frequencies follow topic and community. Keep Delta informative; check with
  `separate` before trusting it for a new author.
- **What separated the author's text from AI drafts**: sentence-length variability (CV 0.52 ± 0.14 vs AI 0.19-0.21;
  SD 13 vs 4-5), comma rate (42/1000 vs 88-101), parentheses (11/1000 vs 0), connectives never used by the
  author ("in conclusione", "furthermore", "notably"), anti-pattern phrases. Same picture in English.
- **The first draft written by following a style profile still had AI rhythm** (CV 0.21, 33% of sentences opening
  with a connective vs 7% for the author). One revision guided by `compare` brought every reliable metric within
  1 SD. The check is not optional.
- `separate` on a cleaned author corpus vs an uncleaned control showed huge paragraph-length "differences" that were
  only cleaning artefacts. Clean both sides identically.

## Provenance
- Formulas that generic AI detectors flag ("it is crucial", "further studies are needed", "could suggest") were the
  author's own. Ask before banning; keep a list of allowed phrases.
- Strong AI signals in a mixed document were different in kind: a register shift to textbook explanation, a
  chart description in generic terms, a whole section built on a fixed template ("Another perspective... Another
  interesting analysis... A final potential path"), and zero typos where the rest has some.
- Authorship metadata in files (creator / last modified by) is a hint, not proof. Typing-quirk fingerprints were
  not decisive per file either. When unsure, exclude: losing a few thousand words costs less than a wrong voice.

## Extraction
- `pdftotext` without `-raw` turned justified text into one word per line and dropped short words ("a"); an early
  reading attributed the missing words to the author. Verify a "habit" against the original file before recording it.
- spaCy's Italian parser ends sentences after ':' and splits data lists into 2-word "sentences" (p10 = 2 words).
  `stylometry.py` blocks boundaries after `: ; ,` and common abbreviations.
- Files with the same name and different extensions overwrote each other in a first version; check duplicates.
- Lecture notes mixed prose with code and bullet lists; `clean_prose.py` reports what it drops so you can see it.

## Target language
- The author had no texts in the target language. A 266-word anchor written by the author in 20 minutes was
  enough to see what transfers (long sentences, parenthetical glosses, the same argument order, gerund chains)
  and what is speed (missing articles, wrong calques). The author chose "my accent, correct grammar".
- Constrained translation (one sentence = one sentence, same punctuation) passed `check_translation.py` after
  two fixes; the mismatches were a dropped redundant gloss and an abbreviation ("E. Coli") the checker read as
  a sentence end.
- A verb the author uses constantly ("evidenziare" → "highlight") was on the default English anti-pattern list:
  remove default bans that collide with the author's own map.
