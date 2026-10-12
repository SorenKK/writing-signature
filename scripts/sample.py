#!/usr/bin/env python3
"""Pick representative paragraphs for the qualitative style analysis.

Usage:
    python scripts/sample.py CORPUS_DIR -n 8 -o samples.md [--min 80] [--max 250]

Stratified by subfolder (section/register) and round-robin across files, preferring paragraphs of
typical length so the reader does not see only edge cases. Long-paragraph writers may need --max 400.
"""
import argparse
import random
import re
from collections import defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus", type=Path)
    ap.add_argument("-n", type=int, default=8, help="paragraphs per subfolder (default 8)")
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--min", type=int, default=80)
    ap.add_argument("--max", type=int, default=250)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)

    by_section = defaultdict(list)
    for f in sorted(args.corpus.rglob("*")):
        if f.suffix not in {".txt", ".md"}:
            continue
        section = f.parent.relative_to(args.corpus).as_posix() or "."
        for p in re.split(r"\n\s*\n", f.read_text(encoding="utf-8")):
            p = re.sub(r"\s+", " ", p).strip()
            if args.min <= len(p.split()) <= args.max:
                by_section[section].append((f.name, p))

    out = [f"# Samples from {args.corpus}\n"]
    for section, paragraphs in sorted(by_section.items()):
        by_file = defaultdict(list)
        for name, p in paragraphs:
            by_file[name].append(p)
        for lst in by_file.values():
            random.shuffle(lst)
        picked = []
        while len(picked) < args.n and any(by_file.values()):
            for name in list(by_file):
                if by_file[name] and len(picked) < args.n:
                    picked.append((name, by_file[name].pop()))
        out.append(f"\n## {section} ({len(picked)} of {len(paragraphs)})\n")
        for i, (name, p) in enumerate(picked, 1):
            out.append(f"\n### {section}-{i} [{name}]\n\n{p}\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(out), encoding="utf-8")
    print(f"{args.output}: " + ", ".join(f"{s}={len(v)}" for s, v in sorted(by_section.items())))


if __name__ == "__main__":
    main()
