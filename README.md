# writing-signature

**Teach Claude to write like you, from your own texts.**

`writing-signature` is a [Claude Code](https://claude.com/claude-code) skill. You point it at things you have
written (a thesis, reports, essays, notes, in pdf/docx/odt/txt/md) and it guides Claude through building a
second, personal skill, `write-like-<you>`. From then on, asking *"write this like me"* produces text with your
sentence rhythm, your way of building an argument, your vocabulary, and a numeric check that catches drafts
drifting away from your voice.

> It is about **your voice**, built only from **texts you wrote**. It is not a tool for imitating other people,
> and the personal skill it creates reminds you to disclose AI assistance wherever rules require it.

---

## Contents

- [What you end up with](#what-you-end-up-with)
- [Requirements](#requirements)
- [Install](#install)
- [Tutorial: build your signature](#tutorial-build-your-signature)
- [Using your personal skill](#using-your-personal-skill)
- [Writing in a language you have few texts in](#writing-in-a-language-you-have-few-texts-in)
- [How the checker works](#how-the-checker-works)
- [Privacy](#privacy)
- [Troubleshooting](#troubleshooting)
- [Reference: scripts](#reference-scripts)
- [Adding a language](#adding-a-language)
- [Limits](#limits)
- [Repository layout](#repository-layout)

---

## What you end up with

```
~/.claude/skills/write-like-<you>/
├── SKILL.md                       when and how Claude writes like you
├── references/
│   ├── profile.md                 your rhythm, argument moves, openings, asides, vocabulary, with quotes
│   ├── antipatterns.md            AI tics you never use + phrases that are yours even if detectors flag them
│   ├── quirks.md                  your habits vs other writers; typing slips you chose not to copy
│   ├── examples/                  6-12 excerpts of your own best prose
│   └── target-language.md         optional: your voice in another language
└── baseline/*.json                the numbers drafts are checked against
```

Your original texts never go into that folder. They stay in a private workspace on your machine.

## Requirements

- **Claude Code** (CLI, desktop or IDE extension).
- **Python 3.10+**. [`uv`](https://github.com/astral-sh/uv) is used if present, otherwise `venv` + `pip`.
- **pandoc** and **pdftotext** (poppler-utils) to read docx/odt/pdf:
  - Debian/Ubuntu: `sudo apt install pandoc poppler-utils`
  - macOS: `brew install pandoc poppler`
- **Your texts**: ideally **20,000+ words** you wrote yourself. 5,000 words is enough for a qualitative profile,
  not for reliable numbers. Several genres or sources are welcome.
- Disk: ~50 MB for English, ~550 MB with Italian (spaCy language models).

## Install

```bash
git clone https://github.com/SorenKK/writing-signature ~/.claude/skills/writing-signature
bash ~/.claude/skills/writing-signature/scripts/setup.sh en        # languages of your texts: en, it, or "en it"
```

The setup script creates `.venv/` inside the skill folder, installs spaCy and numpy, and downloads the language
models. It ends with `Ready. PY=...`.

Optional check that everything runs (synthetic text, about a minute):

```bash
bash ~/.claude/skills/writing-signature/tests/smoke_test.sh
# -> smoke test OK
```

**Restart Claude Code** so it picks up the new skill. Typing `/` should now list `writing-signature`.

---

## Tutorial: build your signature

The whole process is a conversation with Claude, usually one to two hours depending on how much text you have.
Claude runs the scripts; you answer questions at the points marked ★. Every answer is written to
`decisions.md` in your workspace, so you can stop and continue another day.

### Step 0: Collect your texts

Put everything in one folder, one subfolder per source:

```
~/my-texts/
├── thesis/        thesis.pdf
├── reports/       q1-report.docx, q2-report.docx
└── notes/         lecture-01.odt, lecture-02.odt, ...
```

Good sources: anything you wrote carefully and alone. Mixed sources (partly AI-assisted, edited by a supervisor or
co-authors) are fine: you will mark them in step 1 and Claude will help you separate the parts.

If a document exists as both docx and pdf, keep the docx: paragraphs survive better.

### Step 1: Start ★

In Claude Code:

```
/writing-signature
Build my writing signature from the files in ~/my-texts
```

Claude asks you:

- your name and a short slug (the skill will be `write-like-<slug>`);
- the language of your texts and the language(s) you will write in;
- **what you will write with it** (emails, essays, reports, articles, teaching material...);
- for each source, **how much was AI-assisted or edited by others**. Be honest here: it is the single most
  important answer for the quality of the result.

### Step 2: Extraction

Claude converts every file to plain text in `~/writing-signature-workspace/<slug>/extracted/` and shows word
counts per file. It strips citations, page numbers and running headers, and reads a few paragraphs of each file
to make sure the text came out right.

### Step 3: Screening mixed sources ★

For every source you did not mark as 100% yours, Claude reads it in full and gives you a table like:

| id | where | evidence | decision |
|---|---|---|---|
| H1 | "To build the model we considered..." | textbook register, no typos unlike the rest | |
| M1 | "Further studies are needed to..." | common academic formula | |

You fill the last column: **EXCLUDE** or **KEEP**. Claude flags generously; many "medium" items turn out to be
your normal phrasing. Those go to an *allowed* list so the personal skill never removes them from your drafts.

### Step 4: Cleaning

Claude keeps only prose: headings, lists, tables, code, figure captions and quoted material are removed, and
long structured documents are split by section. A summary shows what was dropped from each file.

### Step 5: Control group (optional, recommended)

If you have texts **by other people** in the same genre and on similar topics (a classmate's notes, a
colleague's report), add them as a control. They answer the question *"is this my style, or just the style of
the genre?"*. They are only used for comparison and are never copied into your skill.

### Step 6: Quirks ★

Claude measures your habits against the control group. You will see something like:

| quirk (per 1000 words) | you | others |
|---|---|---|
| space before , . ; : | 8.1 | 1.3 |
| comma glued to next word | 3.2 | 0.2 |

Typing slips like these are usually **not** wanted in polished text; you decide. Style habits (a pet phrase, a
way of quoting terms, a construction you use five times more than others) are kept as part of your signature.

### Step 7: Baselines

Claude measures your prose: sentence-length distribution, punctuation, connectives, voice, hedging, and more,
for all sources together and for each source. With a control group it also shows **which measures actually set
you apart** from other writers.

### Step 8: Your profile

Claude reads samples and full sections and writes `profile.md`: how your sentences grow, how you open
paragraphs, how you build an argument, how you use asides, your recurring words, what you never do. Every claim
comes with a quote from your texts. **Read it**: if something does not sound like you, say so; it is your voice.

### Step 9: Examples

Claude picks 6-12 excerpts of 300-500 words from passages that are certainly yours, covering the genres you
said you will write.

### Step 10: Another language ★ (only if needed)

See [Writing in a language you have few texts in](#writing-in-a-language-you-have-few-texts-in).

### Step 11: Your skill is generated

Claude creates `~/.claude/skills/write-like-<slug>/` from the template. **Restart Claude Code.**

### Step 12: Validation ★

1. Claude writes a short text on a topic **not** in your corpus, checks it, revises it, and shows you the numbers
   before and after.
2. **Blind test**: three texts on the same topic: one of yours that the skill never saw, one by the skill, one by
   plain Claude. Rank them. If you spot the skill's text at once, tell Claude what gave it away; the profile is
   updated.

---

## Using your personal skill

Just ask:

```
Write the introduction of this report like me, from these notes: ...
Rewrite this email in my style.
/write-like-<slug> a 300-word summary of the attached paper
```

What happens behind the scenes: Claude reads your profile, anti-patterns and quirks, reads one or two of your
excerpts closest to the genre, writes a draft, saves it, runs the checker, and revises until the draft is inside
your range. A typical check looks like this:

```
## Deviations (|z| >= 2.0); * = reliable metric
| sent_initial_connective * | 0.33 | 0.07 ± 0.07 | +3.8 |
| sent_cv *                 | 0.21 | 0.52 ± 0.14 | -2.3 |

## Connectives
- FOREIGN "in conclusion": 3.4/1000 words, never used in the corpus

## Anti-patterns found
- "it is important to note" x1
```

Here the draft had sentences that were all the same length and too many sentences opening with a connective,
which is the most common problem of a first draft. After one revision, every reliable metric was within one SD.

**Keep it growing**: when you write something new that you are happy with, add it to your workspace and ask
Claude to *"update my writing signature with this text"*. Baselines and examples get better with more text.

**Keep `writing-signature` installed**: your personal skill calls its scripts.

---

## Writing in a language you have few texts in

Common case: your texts are in Italian, but you need to write in English. A free translation of your corpus
would carry the translator's style, not yours. Instead:

1. **Anchor text ★**: you write 300-500 words in the target language **without AI or translators**, ideally a
   text whose original is in your corpus (a summary, an abstract). Twenty minutes, speed over polish.
2. **Your accent ★**: choose between *your own accent with correct grammar* (your sentence length, your order of
   ideas, natural calques) and *neutral native prose with your structure*.
3. Claude reads the anchor against the original and lists what is **style** (keep), what is **speed** (fix, with
   corrections) and a **map** of your recurring constructions into the target language.
4. 4-6 of your examples are translated **sentence by sentence with the same punctuation**, and
   `check_translation.py` verifies it. These become the examples and a structural baseline for that language.
5. Every real text you later write in that language makes this layer more yours.

---

## How the checker works

`stylometry.py` splits your corpus into blocks of 500 words and measures each one. A draft is compared with the
mean and spread of your blocks. Measured while building the first signature (one author, Italian corpus, plus
nine peers writing on the same subjects as a control):

| signal | author | AI drafts on the same topics |
|---|---|---|
| sentence-length variation (CV) | 0.52 ± 0.14 | 0.19-0.21 |
| commas per 1000 words | 42 ± 14 | 88-101 |
| parentheses per 1000 words | 11 ± 9 | 0 |
| connectives the author never uses | 0 | several per text |

**Burrows' Delta**, a classic authorship measure based on function words, did **not** separate the author from
the nine peers, so it is shown for information only. Run `stylometry.py separate` with your own control group to
see which measures carry your signature. Details: [`references/lessons.md`](references/lessons.md).

---

## Privacy

- Your texts, extracted text, samples and decisions live in `~/writing-signature-workspace/<slug>/`.
- The personal skill contains your profile, short excerpts of your prose and numeric baselines: **treat it as
  personal data**; do not publish it unless you want to.
- Control-group texts belong to other people: they stay in the workspace and are never copied into a skill.
- Nothing here sends data anywhere. The only network access is `setup.sh` downloading Python packages and models.
  (Claude itself reads the texts during the conversation, like any file you show it.)
- `.gitignore` blocks pdf/docx/odt and workspace folders from being committed to this repo by accident.

---

## Troubleshooting

| problem | fix |
|---|---|
| `Missing model: python -m spacy download ...` | `bash scripts/setup.sh <lang>` |
| extracted PDF has very few words | scanned PDF: run OCR first (e.g. `ocrmypdf`) or use the docx |
| `WARNING: only N blocks` | under ~2,500 words per baseline; numbers are indicative, add text |
| `separate` says it needs ≥3 files | each side needs 3+ files of 500+ words |
| `check_translation.py` says NO on a correct file | an abbreviation ("E. coli", "Dr.") was read as a sentence end; read the pair |
| the skill does not appear after install | restart Claude Code; check `~/.claude/skills/writing-signature/SKILL.md` exists |

---

## Reference: scripts

All scripts take `--help`. Run them with the skill's Python: `PY=~/.claude/skills/writing-signature/.venv/bin/python`.

| script | what it does |
|---|---|
| `extract_text.py IN OUT` | pdf/docx/odt/rtf/txt/md → plain text; strips citations, headers, page numbers; never overwrites same-name files |
| `clean_prose.py IN OUT [--fix-typing] [--drop-pattern RE]` | keeps prose paragraphs, reports what it dropped; optional typing-slip normalisation |
| `stylometry.py baseline DIR... --lang xx -o FILE` | builds a baseline (metrics per 500-word block, connective counts, Delta model) |
| `stylometry.py compare DRAFT BASELINE [--antipatterns MD]` | deviations, foreign/overused connectives, Delta, anti-pattern hits |
| `stylometry.py separate AUTHOR CONTROL --lang xx` | effect size of every metric author vs control; leave-one-out Delta |
| `stylometry.py quirks AUTHOR [CONTROL]` | typing-slip rates |
| `sample.py DIR -n N -o FILE` | stratified paragraph samples for the profile |
| `check_translation.py TRANSLATIONS ORIGINALS` | verifies sentence count, paragraphs, `; :` and parentheses are preserved |

---

## Adding a language

1. Add an entry to `LANGUAGES` in `scripts/stylometry.py`: spaCy model name, connectives, hedging lemmas and
   forms, modal verbs, nominal suffixes, passive dependency labels (see the `en` and `it` entries).
2. Add the model to the `MODEL` map in `scripts/setup.sh`.
3. Add `references/antipatterns-<lang>.md` with a `## Anti-patterns` section of quoted phrases.

Pull requests with new languages are welcome.

---

## Limits

- Under ~20,000 words the numbers are indicative; for a single draft under 250 words, trust the profile more
  than the z-scores.
- The profile is only as good as the screening: AI-written passages left in the corpus become "your" style.
- Vocabulary follows topic: the signature is most convincing on subjects close to your corpus.
- It imitates how you write, not what you know: facts, data and citations in a draft still need checking.

---

## Repository layout

```
writing-signature/
├── SKILL.md                       the meta-skill: phases and decision points
├── references/
│   ├── method.md                  detailed steps for each phase
│   ├── lessons.md                 what worked and what did not in a real build
│   ├── ai-screening.md            strong vs weak signals for AI-written passages
│   ├── constrained-translation.md target-language protocol
│   └── antipatterns-en.md, antipatterns-it.md
├── scripts/                       extract_text, clean_prose, stylometry, sample, check_translation, setup.sh
├── templates/personal-skill/      the skeleton of write-like-<you>
└── tests/smoke_test.sh
```

## License

MIT © 2026 Francesco Orilio
