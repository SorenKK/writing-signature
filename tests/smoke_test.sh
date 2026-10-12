#!/usr/bin/env bash
# Smoke test: every script runs end to end on synthetic text (no personal data).
# Usage: bash tests/smoke_test.sh [PYTHON]   (default: .venv/bin/python)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${1:-$ROOT/.venv/bin/python}"
T="$ROOT/tests/tmp"
rm -rf "$T" && mkdir -p "$T"/{raw/a,raw/b,ext,clean/a,clean/b,ex/notes,tr}

# synthetic corpus: two "authors" with different sentence rhythm
"$PY" - "$T" <<'EOF'
import random, sys, pathlib
random.seed(1)
t = pathlib.Path(sys.argv[1])
words = ("the sample data model signal patient group analysis result method value process cell "
         "protein study effect level response change pattern system").split()
def sent(lo, hi):
    w = [random.choice(words) for _ in range(random.randint(lo, hi))]
    if len(w) > 12: w.insert(len(w) // 2, "(see table)")
    return " ".join(w).capitalize() + random.choice([".", ".", ";", "."]).replace(";", ".")
for author, (lo, hi) in {"a": (6, 45), "b": (14, 18)}.items():
    for i in range(4):
        pars = [" ".join(sent(lo, hi) for _ in range(random.randint(3, 6))) for _ in range(12)]
        (t / "raw" / author / f"doc{i}.txt").write_text("\n\n".join(pars))
EOF
command -v pandoc >/dev/null && pandoc "$T/raw/a/doc0.txt" -o "$T/raw/a/doc0_copy.docx"

"$PY" "$ROOT/scripts/extract_text.py" "$T/raw/a" "$T/ext" >/dev/null
"$PY" "$ROOT/scripts/clean_prose.py" "$T/ext" "$T/clean/a" --fix-typing >/dev/null
cp "$T"/raw/b/*.txt "$T/clean/b/"
"$PY" "$ROOT/scripts/stylometry.py" baseline "$T/clean/a" --lang en -o "$T/base.json" 2>/dev/null
"$PY" "$ROOT/scripts/stylometry.py" compare "$T/clean/b/doc0.txt" "$T/base.json" \
      --antipatterns "$ROOT/references/antipatterns-en.md" > "$T/compare.md"
grep -q "sent_cv \*" "$T/compare.md" || { echo "FAIL: compare did not flag uniform sentence length"; exit 1; }
"$PY" "$ROOT/scripts/stylometry.py" separate "$T/clean/a" "$T/clean/b" --lang en > "$T/separate.md"
grep -q "Cohen" "$T/separate.md"
"$PY" "$ROOT/scripts/stylometry.py" quirks "$T/clean/a" "$T/clean/b" > /dev/null
"$PY" "$ROOT/scripts/sample.py" "$T/clean" -n 2 -o "$T/samples.md" --min 20 > /dev/null
head -c 600 "$T/clean/a/doc1.txt" > "$T/ex/notes/one.txt"
cp "$T/ex/notes/one.txt" "$T/tr/notes_one.txt"
"$PY" "$ROOT/scripts/check_translation.py" "$T/tr" "$T/ex" > /dev/null
echo "smoke test OK"
