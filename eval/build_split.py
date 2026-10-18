"""
Build the two held-out sets used for calibration and for the public exam.

Source pool: data/_mega_merged.jsonl (2,500 French 3-option questions, 13 categories)
minus every item the production adapter (v1) was trained on
(data/_external/dataset_avance.jsonl), matched on (context | question).

The pool is split in two, deterministically (md5 of the item), stratified by category:
  - eval/data/calib_val.jsonl  : used ONLY to fit the temperature
  - eval/data/exam_test.jsonl  : never used for any fitting; ECE, needs_review and the
                                 public exam score are measured here.
Option order is shuffled once (seeded by the item hash) and frozen in the files,
so every run sees exactly the same prompts.

Also prints a contamination report against the training items (exact question
reuse and near-duplicate contexts), because both sets come from the same generators.

    python eval/build_split.py
"""

import hashlib
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEGA = os.path.join(ROOT, "data", "_mega_merged.jsonl")
TRAIN_V1 = os.path.join(ROOT, "data", "_external", "dataset_avance.jsonl")
OUT = os.path.join(ROOT, "eval", "data")


def key(d):
    return hashlib.md5((d["contexte"].strip() + "|" + d["question"].strip()).encode("utf-8")).hexdigest()


def tokens(s):
    return set(re.findall(r"[a-zà-ÿ]+", s.lower()))


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    train = load(TRAIN_V1)
    train_keys = {key(d) for d in train}
    train_questions = {d["question"].strip() for d in train}
    train_ctx_tokens = [tokens(d["contexte"]) for d in train]

    pool, seen, excluded = [], set(), 0
    for d in load(MEGA):
        k = key(d)
        if k in train_keys:
            excluded += 1
            continue
        if k in seen:
            continue
        seen.add(k)
        pool.append(d)

    by_cat = defaultdict(list)
    for d in pool:
        by_cat[d["categorie"]].append(d)

    val, test = [], []
    for cat in sorted(by_cat):
        items = sorted(by_cat[cat], key=key)  # deterministic order by hash
        for i, d in enumerate(items):
            k = key(d)
            rng = random.Random(int(k[:8], 16))
            order = [0, 1, 2]
            rng.shuffle(order)
            options = [d["options"][j] for j in order]
            rec = {
                "id": k,
                "category": cat,
                "context": d["contexte"],
                "question": d["question"],
                "options": options,
                "answer_idx": order.index(d["index_correct"]),
            }
            (val if i % 2 == 0 else test).append(rec)

    os.makedirs(OUT, exist_ok=True)
    for name, rows in (("calib_val.jsonl", val), ("exam_test.jsonl", test)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Contamination report (same generators as training: say it, do not hide it)
    def report(rows):
        same_q = sum(r["question"].strip() in train_questions for r in rows)
        near = 0
        for r in rows:
            t = tokens(r["context"])
            if any(len(t & u) / max(1, len(t | u)) >= 0.8 for u in train_ctx_tokens):
                near += 1
        return same_q, near

    print(f"Pool: {len(pool)} items (mega set {len(load(MEGA))}, {excluded} found among the "
          f"{len(train_keys)} v1 training items and removed, duplicates removed)")
    for name, rows in (("calib_val", val), ("exam_test", test)):
        same_q, near = report(rows)
        pos = Counter(r["answer_idx"] for r in rows)
        print(f"{name}: {len(rows)} items | answer position A/B/C = {pos[0]}/{pos[1]}/{pos[2]} | "
              f"question text also in training: {same_q} ({same_q/len(rows)*100:.0f} %) | "
              f"context near-duplicate (Jaccard >= 0.8) of a training item: {near} ({near/len(rows)*100:.0f} %)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
