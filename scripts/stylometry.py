#!/usr/bin/env python3
"""Stylometric baseline of an author's corpus, draft comparison, and validation helpers.

Usage:
    # baseline (one or more folders; language: it | en, see LANGUAGES to add more)
    python scripts/stylometry.py baseline CORPUS_DIR [CORPUS_DIR ...] --lang en -o baseline/combined.json

    # compare a draft with a baseline (language is read from the baseline)
    python scripts/stylometry.py compare draft.txt baseline/combined.json [--antipatterns FILE]

    # which metrics separate the author from other writers (needs a control folder)
    python scripts/stylometry.py separate AUTHOR_DIR CONTROL_DIR --lang en

    # typing-quirk rates, author vs control
    python scripts/stylometry.py quirks AUTHOR_DIR [CONTROL_DIR]

Input: .txt/.md, paragraphs separated by a blank line. Metrics are computed on blocks of ~N words
(default 500) so baseline mean and SD are comparable with a draft of similar length.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import spacy
from spacy.language import Language

LANGUAGES = {
    "en": {
        "model": "en_core_web_md",
        "connectives": [
            "however", "therefore", "thus", "hence", "moreover", "furthermore", "in addition",
            "additionally", "indeed", "instead", "in particular", "specifically", "for example",
            "for instance", "i.e.", "e.g.", "namely", "consequently", "nevertheless",
            "nonetheless", "although", "though", "whereas", "while", "since", "because",
            "finally", "first", "firstly", "secondly", "in conclusion", "in summary",
            "overall", "notably", "importantly", "regarding", "as for", "compared to",
            "on the other hand", "in contrast", "similarly", "likewise", "not only", "but also",
            "then", "so", "ultimately", "crucially", "interestingly",
        ],
        "hedge_lemmas": {"suggest", "seem", "appear", "hypothesize", "speculate"},
        "hedge_forms": {"possibly", "probably", "likely", "potentially", "presumably", "plausibly",
                        "plausible", "possible", "partially", "perhaps", "putatively"},
        "hedge_modals": {"may", "might", "could"},
        "nominal_suffixes": ("tion", "tions", "sion", "sions", "ment", "ments", "ness", "ity",
                             "ities", "ance", "ances", "ence", "ences"),
        "passive_deps": {"auxpass", "aux:pass"},
    },
    "it": {
        "model": "it_core_news_lg",
        "connectives": [
            "tuttavia", "pertanto", "quindi", "dunque", "inoltre", "infatti", "invece",
            "comunque", "d'altra parte", "d'altro canto", "in particolare", "ad esempio",
            "per esempio", "in altre parole", "di conseguenza", "ciononostante", "nonostante",
            "sebbene", "benché", "poiché", "in quanto", "dato che", "visto che", "anche se",
            "in effetti", "cioè", "ovvero", "ossia", "infine", "in primo luogo",
            "in secondo luogo", "al contrario", "allo stesso modo", "oltre a ciò",
            "in conclusione", "in sintesi", "in definitiva", "a tal fine", "per questo",
            "per questo motivo", "a questo proposito", "in realtà", "così", "pure",
            "non solo", "ma anche", "mentre", "eppure", "allora",
        ],
        "hedge_lemmas": {"sembrare", "suggerire", "ipotizzare", "apparire", "supporre"},
        "hedge_forms": {"probabilmente", "verosimilmente", "presumibilmente", "potenzialmente",
                        "plausibile", "plausibilmente", "possibile", "possibilmente", "eventualmente",
                        "tendenzialmente", "parzialmente", "ipoteticamente"},
        "hedge_modals": {"potere"},
        "nominal_suffixes": ("zione", "sione", "mento", "menti", "zioni", "sioni",
                             "tà", "ezza", "ezze", "enza", "enze", "anza", "anze", "ura", "ure"),
        "passive_deps": {"aux:pass", "expl:pass"},
    },
}
N_MFW = 150
RELIABLE = ["sent_cv", "sent_sd", "sent_p90", "comma_per1000", "paren_per1000", "sent_initial_connective"]
L = {}
RE_CONN = {}


def set_language(lang: str):
    if lang not in LANGUAGES:
        sys.exit(f"Unsupported language '{lang}'. Add it to LANGUAGES in {__file__}.")
    L.clear()
    L.update(LANGUAGES[lang], lang=lang)
    RE_CONN.clear()
    RE_CONN.update({c: re.compile(r"(?<![\w'])" + re.escape(c) + r"(?![\w'])") for c in L["connectives"]})


# ---------------------------------------------------------------- input

def read_paragraphs(paths) -> list[str]:
    if isinstance(paths, Path):
        paths = [paths]
    files = []
    for p in paths:
        files += [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.suffix in {".txt", ".md"})
    if not files:
        sys.exit(f"No .txt/.md in {', '.join(map(str, paths))}")
    paragraphs = []
    for f in files:
        for p in re.split(r"\n\s*\n", f.read_text(encoding="utf-8").replace("’", "'")):
            p = re.sub(r"\s+", " ", p).strip()
            if p and (len(p.split()) >= 12 or re.search(r"[.!?]$", p)):  # skip headings
                paragraphs.append(p)
    return paragraphs


def blocks(paragraphs: list[str], size: int) -> list[list[str]]:
    out, current, n = [], [], 0
    for p in paragraphs:
        current.append(p)
        n += len(p.split())
        if n >= size:
            out.append(current)
            current, n = [], 0
    if current and (n >= size / 2 or not out):
        out.append(current)
    return out


NO_BOUNDARY_AFTER = {":", ";", ",", "i.e.", "e.g.", "al.", "vs.", "Fig.", "fig.", "etc.", "ecc.", "cfr.", "es."}


@Language.component("sentence_guard")
def sentence_guard(doc):
    """Parsers often end a sentence after ':' and split data lists into fragments: prevent it."""
    for tok in doc[1:]:
        if doc[tok.i - 1].text in NO_BOUNDARY_AFTER:
            tok.is_sent_start = False
    return doc


def load_nlp():
    try:
        nlp = spacy.load(L["model"], disable=["ner"])
    except OSError:
        sys.exit(f"Missing model: python -m spacy download {L['model']}")
    nlp.add_pipe("sentence_guard", before="parser")
    nlp.max_length = 5_000_000
    return nlp


# ---------------------------------------------------------------- metrics

def per1000(x, words):
    return 1000 * x / words if words else 0.0


def block_metrics(docs) -> tuple[dict, list[int], Counter]:
    text = " ".join(d.text for d in docs).lower()
    tokens = [t for d in docs for t in d]
    words = [t for t in tokens if t.is_alpha]
    n = len(words)
    sents = [s for d in docs for s in d.sents if any(t.is_alpha for t in s)]
    sent_len = [sum(t.is_alpha for t in s) for s in sents]
    par_words = [sum(t.is_alpha for t in d) for d in docs]
    par_sents = [sum(1 for s in d.sents if any(t.is_alpha for t in s)) for d in docs]

    verbs = [t for t in tokens if t.pos_ in {"VERB", "AUX"}]
    finite = [t for t in verbs if "Fin" in t.morph.get("VerbForm")]
    nouns = [t for t in tokens if t.pos_ == "NOUN"]
    passives = sum(1 for t in tokens if t.dep_ in L["passive_deps"])
    impersonal = sum(1 for t in tokens if t.dep_ == "expl:impers")
    if L["lang"] == "en":  # person lives in the pronoun, conditional in the modal
        we = sum(1 for t in tokens if t.lower_ in {"we", "us", "our", "ours"})
        i_ = sum(1 for t in tokens if t.lower_ in {"i", "me", "my", "mine"})
        cond = sum(1 for t in tokens if t.lower_ in {"would", "could", "might", "should"})
        modals = sum(1 for t in tokens if t.lower_ in L["hedge_modals"])
    else:
        we = sum(1 for t in finite if t.morph.get("Person") == ["1"] and t.morph.get("Number") == ["Plur"])
        i_ = sum(1 for t in finite if t.morph.get("Person") == ["1"] and t.morph.get("Number") == ["Sing"])
        cond = sum(1 for t in verbs if "Cnd" in t.morph.get("Mood"))
        modals = sum(1 for t in verbs if t.lemma_ in L["hedge_modals"] and "Cnd" in t.morph.get("Mood"))
    nominal = sum(1 for t in nouns if t.lemma_.lower().endswith(L["nominal_suffixes"]))
    hedge = modals + sum(1 for t in tokens if t.lemma_.lower() in L["hedge_lemmas"] or t.lower_ in L["hedge_forms"])
    conn = {c: len(r.findall(text)) for c, r in RE_CONN.items()}
    initial = sum(1 for s in sents if any(r.match(s.text.lower().lstrip("«\"“( ")) for r in RE_CONN.values()))

    sl = np.array(sent_len) if sent_len else np.array([0])
    m = {
        "sent_mean": float(sl.mean()),
        "sent_sd": float(sl.std()),
        "sent_cv": float(sl.std() / sl.mean()) if sl.mean() else 0.0,
        "sent_p10": float(np.percentile(sl, 10)),
        "sent_p50": float(np.percentile(sl, 50)),
        "sent_p90": float(np.percentile(sl, 90)),
        "short_sent_share": float(np.mean(sl <= 10)),
        "long_sent_share": float(np.mean(sl >= 40)),
        "par_words_mean": float(np.mean(par_words)),
        "par_sents_mean": float(np.mean(par_sents)),
        "semicolon_per1000": per1000(text.count(";"), n),
        "colon_per1000": per1000(text.count(":"), n),
        "paren_per1000": per1000(text.count("("), n),
        "dash_aside_per1000": per1000(len(re.findall(r" [–—-] ", text)) + text.count("—"), n),
        "comma_per1000": per1000(text.count(","), n),
        "commas_per_sent": text.count(",") / len(sents) if sents else 0.0,
        "question_per1000": per1000(text.count("?"), n),
        "quote_per1000": per1000(len(re.findall(r"[«\"“]", text)), n),
        "passive_share": passives / len(finite) if finite else 0.0,
        "impersonal_per1000": per1000(impersonal, n),
        "first_plural_per1000": per1000(we, n),
        "first_singular_per1000": per1000(i_, n),
        "conditional_per1000": per1000(cond, n),
        "nominalization_share": nominal / len(nouns) if nouns else 0.0,
        "hedging_per1000": per1000(hedge, n),
        "connectives_per1000": per1000(sum(conn.values()), n),
        "sent_initial_connective": initial / len(sents) if sents else 0.0,
        **{f"conn:{c}": per1000(k, n) for c, k in conn.items()},
    }
    return m, sent_len, Counter(t.lower_ for t in words)


def analyze(nlp, paragraphs, size):
    docs = dict(zip(paragraphs, nlp.pipe(paragraphs, batch_size=64)))
    return [block_metrics([docs[p] for p in b]) for b in blocks(paragraphs, size)]


def rel_freq(counts: Counter, vocab: list[str]) -> np.ndarray:
    tot = sum(counts.values()) or 1
    return np.array([counts[w] / tot for w in vocab])


def delta(counts: Counter, mfw, mu, sd) -> float:
    return float(np.mean(np.abs((rel_freq(counts, mfw) - mu) / sd)))


def mfw_model(results):
    total = Counter()
    for r in results:
        total.update(r[2])
    mfw = [w for w, _ in total.most_common(N_MFW)]
    M = np.array([rel_freq(r[2], mfw) for r in results])
    sd = M.std(0)
    sd[sd == 0] = 1e-9
    return mfw, M.mean(0), sd, total


# ---------------------------------------------------------------- commands

def cmd_baseline(args):
    set_language(args.lang)
    nlp = load_nlp()
    paragraphs = read_paragraphs(args.corpus)
    res = analyze(nlp, paragraphs, args.block)
    if len(res) < 5:
        print(f"WARNING: only {len(res)} blocks; SDs are fragile, treat z-scores as indicative", file=sys.stderr)
    scal = {k: {"mean": float(np.mean([r[0][k] for r in res])), "sd": float(np.std([r[0][k] for r in res]))}
            for k in res[0][0]}
    sents = [x for r in res for x in r[1]]
    mfw, mu, sd, total = mfw_model(res)
    block_deltas = [delta(r[2], mfw, mu, sd) for r in res]
    out = {
        "corpus": [str(c) for c in args.corpus],
        "lang": args.lang,
        "model": L["model"],
        "block_words": args.block,
        "n_blocks": len(res),
        "n_words": int(sum(total.values())),
        "n_sents": len(sents),
        "sent_distribution": {f"p{q}": float(np.percentile(sents, q)) for q in (5, 10, 25, 50, 75, 90, 95)},
        "metrics": scal,
        "mfw": {"words": mfw, "mean": mu.tolist(), "sd": sd.tolist()},
        "connective_counts": {c: int(sum(len(r.findall(p.lower())) for p in paragraphs)) for c, r in RE_CONN.items()},
        "block_delta": {"mean": float(np.mean(block_deltas)), "p95": float(np.percentile(block_deltas, 95))},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    d = out["sent_distribution"]
    print(f"Baseline: {args.output}  ({out['n_words']} words, {len(res)} blocks, {len(sents)} sentences)")
    print(f"Sentence length p10/p50/p90: {d['p10']:.0f}/{d['p50']:.0f}/{d['p90']:.0f} words")


def antipatterns(path: Path) -> list[str]:
    """Quoted phrases in the '## Anti-patterns' section of a markdown file. Without that heading, only
    bullet lines are read (so prose such as an 'allowed phrases' note is never treated as a ban).
    Entries containing '...' are skipped (they describe a construction, not a literal string)."""
    if not path or not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").replace("“", '"').replace("”", '"').splitlines()
    start = [i for i, r in enumerate(lines) if r.lower().startswith("## anti-pattern")]
    if start:
        end = next((i for i in range(start[0] + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        lines = lines[start[0] + 1:end]
    else:
        lines = [r for r in lines if r.lstrip().startswith("-")]
    found = [q for r in lines for q in re.findall(r'"([^"]+)"', r)]
    return [q.lower().replace("’", "'") for q in found if "..." not in q]


def cmd_compare(args):
    base = json.loads(args.baseline.read_text(encoding="utf-8"))
    set_language(base.get("lang", "en"))
    nlp = load_nlp()
    paragraphs = read_paragraphs(args.draft)
    m, sl, counts = block_metrics(list(nlp.pipe(paragraphs)))
    n_words = sum(counts.values())

    rows = []
    for k, v in m.items():
        b = base["metrics"].get(k)
        if b is None:
            continue
        z = (v - b["mean"]) / b["sd"] if b["sd"] > 1e-9 else (0.0 if abs(v - b["mean"]) < 1e-9 else float("inf"))
        rows.append((k, v, b["mean"], b["sd"], z))

    print(f"# Compare: {args.draft.name} vs {args.baseline.name}")
    print(f"Draft: {n_words} words, {len(sl)} sentences. Baseline blocks: {base['block_words']} words.")
    if n_words < base["block_words"] / 2:
        print("WARNING: draft much shorter than baseline blocks; z-scores are noisy.")

    print(f"\n## Deviations (|z| >= {args.threshold:.1f}); * = reliable metric\n")
    print("| metric | draft | baseline (mean ± sd) | z |\n|---|---|---|---|")
    out = [r for r in rows if abs(r[4]) >= args.threshold and not r[0].startswith("conn:")]
    out.sort(key=lambda r: (r[0] not in RELIABLE, -abs(r[4]) if np.isfinite(r[4]) else -1e9))
    for k, v, mu, sd, z in out:
        zs = f"{z:+.1f}" if np.isfinite(z) else "inf (constant in corpus)"
        print(f"| {k}{' *' if k in RELIABLE else ''} | {v:.2f} | {mu:.2f} ± {sd:.2f} | {zs} |")
    if not out:
        print("| none | | | |")

    occ = base.get("connective_counts", {})
    foreign = [(k[5:], v) for k, v, *_ in rows if k.startswith("conn:") and v > 0 and occ.get(k[5:], 1) == 0]
    over = [(k[5:], v, mu) for k, v, mu, sd, z in rows
            if k.startswith("conn:") and occ.get(k[5:], 1) > 0 and v * n_words / 1000 >= 2 and v >= 3 * max(mu, 0.5)]
    if foreign or over:
        print("\n## Connectives")
        for c, v in foreign:
            print(f"- FOREIGN \"{c}\": {v:.1f}/1000 words, never used in the corpus")
        for c, v, mu in over:
            print(f"- OVERUSED \"{c}\": {v:.1f}/1000 vs {mu:.1f}/1000")

    mfw = base["mfw"]["words"]
    dd = delta(counts, mfw, np.array(base["mfw"]["mean"]), np.array(base["mfw"]["sd"]))
    ref = base["block_delta"]
    print(f"\n## Burrows' Delta (MFW={len(mfw)}): {dd:.2f} | corpus blocks mean {ref['mean']:.2f}, p95 {ref['p95']:.2f}")
    print("(informative only: on shared topics it rarely separates one author from peers; run `separate` to check)")

    text = " ".join(paragraphs).lower().replace("’", "'")
    hits = [(a, len(re.findall(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text))) for a in antipatterns(args.antipatterns)]
    hits = [(a, k) for a, k in hits if k]
    if "—" in text:
        hits.append(("— (em dash)", text.count("—")))
    if hits:
        print("\n## Anti-patterns found\n")
        for a, k in hits:
            print(f"- \"{a}\" x{k}")


def per_file_results(nlp, folder: Path, size: int):
    files = [f for f in sorted(folder.rglob("*")) if f.suffix in {".txt", ".md"}]
    return {f.name: analyze(nlp, read_paragraphs(f), size) for f in files if len(f.read_text().split()) >= size}


def cmd_separate(args):
    """Effect size of each metric, author files vs control files, plus leave-one-out Delta."""
    set_language(args.lang)
    nlp = load_nlp()
    own = per_file_results(nlp, args.author, args.block)
    ctrl = per_file_results(nlp, args.control, args.block)
    if len(own) < 3 or len(ctrl) < 3:
        sys.exit(f"Need >=3 files of >= {args.block} words on each side (author {len(own)}, control {len(ctrl)}).")
    mean = lambda res, k: float(np.mean([r[0][k] for r in res]))
    keys = [k for k in next(iter(own.values()))[0][0] if not k.startswith("conn:")]
    print(f"# Separation: {len(own)} author files vs {len(ctrl)} control files\n")
    print("| metric | author | control | Cohen's d |\n|---|---|---|---|")
    table = []
    for k in keys:
        a = np.array([mean(r, k) for r in own.values()])
        c = np.array([mean(r, k) for r in ctrl.values()])
        pooled = np.sqrt((a.var(ddof=1) + c.var(ddof=1)) / 2) or 1e-9
        table.append((k, a.mean(), c.mean(), (a.mean() - c.mean()) / pooled))
    for k, a, c, d in sorted(table, key=lambda r: -abs(r[3])):
        print(f"| {k}{' *' if abs(d) >= 0.8 else ''} | {a:.2f} | {c:.2f} | {d:+.2f} |")
    print("\n* |d| >= 0.8: large difference, this metric carries the author's signature.")

    d_own, d_ctrl = [], []
    for name, res in own.items():
        rest = [r for n, rr in own.items() if n != name for r in rr]
        mfw, mu, sd, _ = mfw_model(rest)
        d_own += [delta(r[2], mfw, mu, sd) for r in res]
    mfw, mu, sd, _ = mfw_model([r for rr in own.values() for r in rr])
    d_ctrl = [delta(r[2], mfw, mu, sd) for rr in ctrl.values() for r in rr]
    print(f"\nBurrows' Delta vs author corpus: author (leave-one-out) {np.mean(d_own):.3f}, control {np.mean(d_ctrl):.3f}")
    print("Delta is useful only if the author value is clearly LOWER than the control value.")


QUIRKS = {
    "space before , . ; :": r"\w [,.;:](?=\s|\w)",
    "comma glued to next word": r" ,\w",
    "missing space after , . ;": r"[a-zà-ù][,;.](?=[A-Za-zÀ-ÿ]{3})",
    "double space": r"\S  +\S",
    "E' instead of È": r"\bE'",
    "lowercase sentence start": r"[.!?] [a-zà-ù]",
    "repeated punctuation (!! ?? ..)": r"[!?]{2,}|(?<!\.)\.\.(?!\.)",
}


def cmd_quirks(args):
    def rates(folder):
        text = " ".join(f.read_text(encoding="utf-8") for f in folder.rglob("*") if f.suffix in {".txt", ".md"})
        w = len(text.split()) / 1000 or 1
        return {k: len(re.findall(p, text)) / w for k, p in QUIRKS.items()}
    a = rates(args.author)
    c = rates(args.control) if args.control else None
    print("| quirk (per 1000 words) | author |" + (" control |" if c else "") + "\n|---|---|" + ("---|" if c else ""))
    for k in QUIRKS:
        mark = " <- author" if c and a[k] > 2 * max(c[k], 0.05) and a[k] > 0.15 else ""
        print(f"| {k} | {a[k]:.2f} |" + (f" {c[k]:.2f} |" if c else "") + mark)
    print("\nThese are typing slips, not style. Ask the author whether to reproduce them (usually: no).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("baseline", help="build a baseline from one or more folders")
    b.add_argument("corpus", type=Path, nargs="+")
    b.add_argument("-o", "--output", type=Path, required=True)
    b.add_argument("--block", type=int, default=500, help="words per block (default 500)")
    b.add_argument("--lang", choices=sorted(LANGUAGES), default="en")
    b.set_defaults(func=cmd_baseline)

    c = sub.add_parser("compare", help="compare a draft with a baseline")
    c.add_argument("draft", type=Path)
    c.add_argument("baseline", type=Path)
    c.add_argument("--threshold", type=float, default=2.0)
    c.add_argument("--antipatterns", type=Path, help="markdown file with a '## Anti-patterns' section of quoted phrases")
    c.set_defaults(func=cmd_compare)

    s = sub.add_parser("separate", help="which metrics separate the author from a control group")
    s.add_argument("author", type=Path)
    s.add_argument("control", type=Path)
    s.add_argument("--lang", choices=sorted(LANGUAGES), default="en")
    s.add_argument("--block", type=int, default=500)
    s.set_defaults(func=cmd_separate)

    q = sub.add_parser("quirks", help="typing-quirk rates, author vs optional control")
    q.add_argument("author", type=Path)
    q.add_argument("control", type=Path, nargs="?")
    q.set_defaults(func=cmd_quirks)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
