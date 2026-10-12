# writing-signature

A Claude Code skill that turns **your own** past writing into a personal skill that writes like you.

You give it your texts (theses, reports, notes, essays, in pdf/docx/odt/txt/md). It guides Claude through
extracting them, setting aside the passages you did not write, measuring your prose, writing a style profile
with real quotes, picking your best excerpts, and generating `~/.claude/skills/write-like-<you>/`. From then on,
"write this like me" uses your profile, your examples and a numeric checker that flags drafts drifting away
from your voice.

It is about **your voice**, not about passing as human. It works only with texts you wrote, and it reminds you
to disclose AI assistance where rules require it.

## What you get

```
~/.claude/skills/write-like-<you>/
  SKILL.md                    # when and how to write like you
  references/profile.md       # your rhythm, argument moves, openings, glosses, vocabulary, with quotes
  references/antipatterns.md  # AI tics you never use, plus phrases that are yours even if detectors flag them
  references/quirks.md        # your habits vs peers; typing slips you chose not to reproduce
  references/examples/        # 6-12 excerpts of your own prose
  references/target-language.md  # optional: your voice in a language you have little text in
  baseline/*.json             # numbers the checker compares drafts against
```

## Install

```bash
git clone https://github.com/<user>/writing-signature ~/.claude/skills/writing-signature
bash ~/.claude/skills/writing-signature/scripts/setup.sh en      # or: en it
```
Needs Python 3.10+, `pandoc` and `pdftotext` (poppler-utils). Restart Claude Code, then ask:
*"Build my writing signature from the files in ~/my-texts"*.

Your texts stay in `~/writing-signature-workspace/` on your machine. Nothing in this repo touches the network
except the setup step that downloads Python packages and language models.

## The process

1. **Intake**: who you are, which languages, what you will write, which sources, how much of each was AI-assisted or edited by others.
2. **Extract** text from every file.
3. **Screen** mixed sources: Claude flags passages that look AI-written or co-written, **you decide**.
4. **Clean** and split by section.
5. **Control group** (optional): same-genre texts by other people, to learn what is yours and not just the genre's.
6. **Quirks**: your habits vs peers; you decide whether typing slips are reproduced (usually not).
7. **Baselines**: sentence rhythm, punctuation, connectives, voice, hedging.
8. **Profile** with quotes, 9. **examples**, 10. optional **target-language layer**, 11. **generate** the skill.
12. **Validate**: a draft on a new topic, checked and revised, then a blind test with you.

Stops marked ★ in `SKILL.md` are your decisions; Claude asks and records them.

## What the checker trusts

Measured while building the first signature (details in `references/lessons.md`):

| Signal | Author | AI drafts on the same topics |
|---|---|---|
| sentence-length coefficient of variation | 0.52 ± 0.14 | 0.19-0.21 |
| commas per 1000 words | 42 ± 14 | 88-101 |
| parentheses per 1000 words | 11 ± 9 | 0 |
| connectives the author never uses | 0 | several per text |

Burrows' Delta, a classic authorship measure, did **not** separate the author from nine peers writing on the
same subjects, so it is reported as information only. `stylometry.py separate` tells you which metrics carry
your signature against your own control group.

## Languages

English and Italian are configured. Adding a language = one entry in `LANGUAGES` in `scripts/stylometry.py`
(spaCy model, connectives, hedges, nominal suffixes, passive dependency labels) plus an
`references/antipatterns-<lang>.md`.

## Scripts

| script | does |
|---|---|
| `extract_text.py` | pdf/docx/odt/rtf/txt/md → plain text; strips citations, running headers, page numbers |
| `clean_prose.py` | keeps prose paragraphs; optional typing-slip normalisation; reports what it dropped |
| `stylometry.py` | `baseline`, `compare`, `separate` (author vs control), `quirks` |
| `sample.py` | stratified paragraph samples for the qualitative profile |
| `check_translation.py` | verifies a constrained translation kept sentences and punctuation |

Each has `--help`.

## Limits

- Under ~20,000 words the numbers are indicative; under 250 words a single draft's z-scores are noisy.
- The profile is only as good as the screening: AI-written passages left in the corpus become "your" style.
- Topic shapes vocabulary; the signature is most convincing on subjects close to your corpus.

## License

MIT
