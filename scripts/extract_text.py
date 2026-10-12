#!/usr/bin/env python3
"""Extract clean plain text from pdf/docx/odt/rtf/txt/md -> .txt (paragraphs separated by a blank line).

Usage:
    python scripts/extract_text.py INPUT_DIR_OR_FILE OUTPUT_DIR [--keep-citations]

Requires `pdftotext` (poppler-utils) and `pandoc` on PATH. No manual conversion needed.
Prefer docx/odt over pdf when both exist: paragraph boundaries in PDFs are reconstructed heuristically.
"""
import argparse
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

EXTENSIONS = {".pdf", ".docx", ".odt", ".txt", ".md", ".rtf", ".doc"}

# citations: [12], [3-5], [1,4]  and  (Smith et al., 2019) / (Smith and Jones 2020; Lee, 2018)
RE_CIT_NUM = re.compile(r"\s?\[\d+(?:\s*[-–,]\s*\d+)*\]")
RE_CIT_AUTHOR = re.compile(
    r"\s?\((?:[A-ZÀ-Ý][\w'’\-]+(?:\s+(?:et al\.?|e|and|&|und|y|et)\s*[A-ZÀ-Ý]?[\w'’\-]*)*,?\s+\d{4}[a-z]?(?:;\s*)?)+\)"
)


def pdf_to_text(path: Path) -> str:
    # -raw keeps content-stream order; without it, justified text can come out as scattered words
    out = subprocess.run(["pdftotext", "-raw", "-enc", "UTF-8", str(path), "-"],
                         capture_output=True, text=True, check=True).stdout
    pages = out.split("\f")

    # running headers/footers: lines at the top or bottom of a page, repeated on many pages
    def edges(lines):
        return lines[:2] + lines[-2:]

    page_lines = [[r.strip() for r in p.splitlines() if r.strip()] for p in pages]
    counts = Counter()
    for lines in page_lines:
        counts.update(set(re.sub(r"\d+", "#", r) for r in edges(lines) if len(r) < 80))
    threshold = max(3, int(len(pages) * 0.3))
    repeated = {r for r, n in counts.items() if n >= threshold}

    blocks = []
    for p, lines in zip(pages, page_lines):
        drop = {r for r in edges(lines) if re.sub(r"\d+", "#", r) in repeated or re.fullmatch(r"\d{1,4}", r)}
        blocks.append("\n".join(r for r in p.splitlines() if r.strip() not in drop))
    text = "\n".join(blocks)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # end-of-line hyphenation
    # superscript note numbers glued to a word: "symptom1." "literature24;" (not PC1, TUBA4A, χ2)
    text = re.sub(r"(?<=[a-zà-ù\)])\d{1,3}(?:[,–-]\d{1,3})*(?=[\s.,;:]|$)", "", text, flags=re.M)
    return join_pdf_lines(text)


def join_pdf_lines(text: str) -> str:
    """In a PDF every visual line is a text line: rebuild paragraphs."""
    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        lines = [r.strip() for r in block.splitlines() if r.strip()]
        if not lines:
            continue
        typical = sorted(len(r) for r in lines)[len(lines) // 2]
        current = []
        for r in lines:
            current.append(r)
            # a short line that closes a sentence = end of paragraph
            if re.search(r"[.!?:]$", r) and len(r) < 0.7 * typical:
                paragraphs.append(" ".join(current))
                current = []
        if current:
            paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def document_to_text(path: Path) -> str:
    out = subprocess.run(["pandoc", str(path), "-t", "plain", "--wrap=none"],
                         capture_output=True, text=True, check=True).stdout
    return "\n".join(r for r in out.splitlines() if not re.fullmatch(r"\s*[-+=|: ]{4,}\s*", r))  # table borders


def clean(text: str, keep_citations: bool) -> str:
    text = text.replace("­", "").replace("’", "'").replace(" ", " ")
    if not keep_citations:
        text = RE_CIT_NUM.sub("", text)
        text = RE_CIT_AUTHOR.sub("", text)
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    return "\n\n".join(p for p in paragraphs if p) + "\n"


def extract(path: Path, keep_citations: bool) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw = pdf_to_text(path)
    elif suffix in {".txt", ".md"}:
        raw = path.read_text(encoding="utf-8", errors="replace")
    else:
        raw = document_to_text(path)
    return clean(raw, keep_citations)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="file or folder")
    ap.add_argument("output", type=Path, help="destination folder")
    ap.add_argument("--keep-citations", action="store_true", help="do not strip [n] and (Author, year)")
    args = ap.parse_args()

    files = [args.input] if args.input.is_file() else sorted(
        f for f in args.input.rglob("*") if f.suffix.lower() in EXTENSIONS)
    if not files:
        sys.exit(f"No supported files in {args.input}")

    args.output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    for f in files:
        try:
            text = extract(f, args.keep_citations)
        except subprocess.CalledProcessError as e:
            print(f"ERROR {f.name}: {e.stderr.strip()[:200]}", file=sys.stderr)
            continue
        dest = args.output / (f.stem.strip() + ".txt")
        if dest.exists() and dest.stat().st_mtime > started:  # same name, different extension
            dest = args.output / f"{f.stem.strip()}_{f.suffix.lstrip('.').lower()}.txt"
        dest.write_text(text, encoding="utf-8")
        print(f"{f.name} -> {dest}  ({len(text.split())} words, {text.count(chr(10) * 2) + 1} paragraphs)")


if __name__ == "__main__":
    main()
