# Screening a mixed source for AI-written or other-author passages

Goal: exclude what the author did not write, without excluding their own voice. Output a table; the author decides.

## Read the whole source first
Number the paragraphs and read all of it. Note the author's baseline in this document: typos, recurring
constructions, typical sentence length, how they cite figures and data.

## Strong signals (flag the passage)
- Register shift: a textbook/tutorial explanation inside an otherwise technical text ("X is one of the most
  commonly used models... it works by...").
- Generic description of a figure ("the distribution suggests that observations start with low dispersion and
  widen..., indicating the presence of potential patterns").
- A section built on a fixed template ("Another perspective... Another interesting analysis... A final
  potential path...") with a generic closing ("quality of life", "new avenues").
- Clean prose with zero slips in a document where the rest has them.
- Known AI phrasing for the language (see `antipatterns-<lang>.md`), several in the same passage.

## Weak signals (do NOT flag alone; ask)
- Standard formulas of the genre ("further studies are needed", "it is fundamental", "could suggest").
- Connective-led lists, self-promotional openings ("This study represents a novel approach").
- Single hedges or single em dashes.

## Not AI but exclude anyway
Translated or quoted text, criteria copied from guidelines, lists of numbers, abstracts that only repeat the
text, passages rewritten by supervisors or co-authors (ask the author which).

## Output (put it in the workspace, e.g. `extracted/<source>/screening.md`)

| id | where (first words) | evidence | decision |
|---|---|---|---|
| H1 | "To build the model we considered..." | textbook register, no slips, "a very useful feature" | |

High suspicion first, then medium. After the author answers, record allowed phrases (medium-suspicion items they
claim) in `decisions.md`; they go to the personal skill's allowed list.
