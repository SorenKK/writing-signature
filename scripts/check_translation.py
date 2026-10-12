#!/usr/bin/env python3
"""Check that a constrained translation preserves the structure of the original.

Usage:
    python scripts/check_translation.py TRANSLATIONS_DIR ORIGINALS_DIR [--ratio 0.85 1.3]

Each <section>_<name>.txt in TRANSLATIONS_DIR is compared with ORIGINALS_DIR/<section>/<name>.txt.
Constraints: one original sentence = one translated sentence, same paragraphs, same ; : and
parentheses, word-count ratio inside the allowed range. Exit code 1 if any file fails.
Sentence splitting is approximate: a mismatch can come from an abbreviation; read the pair before rewriting.
"""
import argparse
import re
import sys
from pathlib import Path

RE_SENTENCE_END = re.compile(r"(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<!\bal)(?<!\betc)[.!?]\s+(?=[A-ZÀ-Ý\"“«(])")


def structure(text: str) -> dict:
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    return {
        "paragraphs": len(paragraphs),
        "sentences": sum(len(RE_SENTENCE_END.split(p.strip())) for p in paragraphs),
        ";": text.count(";"),
        ":": text.count(":"),
        "(": text.count("("),
        "words": len(text.split()),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("translations", type=Path)
    ap.add_argument("originals", type=Path)
    ap.add_argument("--ratio", type=float, nargs=2, default=(0.85, 1.3),
                    help="allowed translated/original word ratio (default 0.85 1.3)")
    args = ap.parse_args()

    failures = 0
    for f in sorted(args.translations.glob("*.txt")):
        section, name = f.stem.split("_", 1)
        orig = args.originals / section / f"{name}.txt"
        if not orig.exists():
            print(f"??  {f.name}: original {orig} not found")
            failures += 1
            continue
        a, b = structure(orig.read_text(encoding="utf-8")), structure(f.read_text(encoding="utf-8"))
        problems = [f"{k} orig {a[k]} / transl {b[k]}" for k in ("paragraphs", "sentences", ";", ":", "(") if a[k] != b[k]]
        r = b["words"] / a["words"]
        if not args.ratio[0] <= r <= args.ratio[1]:
            problems.append(f"word ratio {r:.2f}")
        failures += bool(problems)
        print(f"{'OK ' if not problems else 'NO '} {f.name:45} sentences {b['sentences']:3}  ratio {r:.2f}  {'; '.join(problems)}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
