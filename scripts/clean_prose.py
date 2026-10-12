#!/usr/bin/env python3
"""Keep only prose paragraphs; optionally normalize typing slips.

Usage:
    python scripts/clean_prose.py INPUT_DIR_OR_FILE OUTPUT_DIR [--fix-typing] [--drop-pattern REGEX ...]

Drops: ALL-CAPS headings, short headings without final punctuation, list items, figure references,
paragraphs dominated by code or symbols, and any paragraph matching --drop-pattern (e.g. a recurring
header such as "^Lecture notes").
--fix-typing: space before , . ; :  -> removed; comma glued to the next word -> spaced; E' -> È.
Use it when the author decided that typing slips are not part of the style to imitate.
Prints, per file, how many words were kept and dropped by category: check that "prose" is most of it.
"""
import argparse
import re
from collections import Counter
from pathlib import Path

RE_LIST = re.compile(r"^([-•●▪*→]|\d{1,2}[.)]|[a-z]\))\s")
RE_FIGURE = re.compile(r"\b(fig(ure|ura)?\.?|image|immagine|slide|table|tabella)\b", re.I)


def category(p: str, drop_patterns) -> str:
    words = p.split()
    if any(r.search(p) for r in drop_patterns) and len(words) < 15:
        return "header"
    if p.isupper():
        return "caps"
    if RE_LIST.match(p):
        return "list"
    if RE_FIGURE.search(p) and len(words) < 25:
        return "figure"
    if len(words) < 12 and not re.search(r"[.!?]$", p):
        return "heading"
    alpha = sum(1 for w in words if re.fullmatch(r"[^\W\d_]+[.,;:!?)]*", w))
    if alpha / len(words) < 0.75:
        return "code/symbols"
    return "prose"


def fix_typing(p: str) -> str:
    p = re.sub(r"(?<=[\w”\"'’)]) +([,.;:])(?=\s|$)", r"\1", p)  # "word ." / "(a) ." -> "word." / "(a)."
    p = re.sub(r"(?<=\S) ,(?=[^\W\d_])", ", ", p)              # "x ,word" -> "x, word"
    p = re.sub(r"\bE'", "È", p)
    return re.sub(r" {2,}", " ", p).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--fix-typing", action="store_true")
    ap.add_argument("--drop-pattern", action="append", default=[], help="regex of short header paragraphs to drop")
    args = ap.parse_args()
    drop_patterns = [re.compile(r, re.I) for r in args.drop_pattern]
    args.output.mkdir(parents=True, exist_ok=True)

    total = Counter()
    files = [args.input] if args.input.is_file() else sorted(args.input.glob("*.txt"))
    for f in files:
        counts, kept = Counter(), []
        for p in re.split(r"\n\s*\n", f.read_text(encoding="utf-8")):
            p = p.strip()
            if not p:
                continue
            c = category(p, drop_patterns)
            counts[c] += len(p.split())
            if c == "prose":
                kept.append(fix_typing(p) if args.fix_typing else p)
        (args.output / f.name).write_text("\n\n".join(kept) + "\n", encoding="utf-8")
        total.update(counts)
        dropped = ", ".join(f"{k} {v}" for k, v in counts.items() if k != "prose")
        print(f"{f.name[:34]:34} kept {counts['prose']:6}  dropped: {dropped or '-'}")
    print(f"\nTOTAL kept {total['prose']} words; dropped {sum(total.values()) - total['prose']}")


if __name__ == "__main__":
    main()
