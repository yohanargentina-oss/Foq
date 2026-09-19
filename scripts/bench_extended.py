"""
Bench étendu Foq : N cas externes vérifiés JAMAIS vus à l'entraînement par l'adaptateur.

Propreté anti-contamination : le pool exclut, par hachage (contexte, question), les 280
items du handoff « from-agent-dataset-avance.md » qui ont servi à l'entraînement de la
v1 (adaptateur de production). Le reste du mega-jeu vérifié (2 077 - 280 ≈ 1 797) est
donc vierge pour la v1 — c'est de là qu'on échantillonne.

Sortie : docs/assets/data_extended.json + docs/assets/chart_extended.png
Rejeu : démarrer le serveur 8B (start_foq_8b_server.cmd avec LORA_PATH), puis
        py -3 scripts/bench_extended.py --base-url http://127.0.0.1:8090
"""

import sys
import os
import json
import hashlib
import random
import argparse
import time

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq.engine import FoqEngine
from foq.schemas import ClassificationChoice

HANDOFF = os.path.join("data", "_external", "dataset_avance.jsonl")
MEGA = os.path.join("data", "_mega_merged.jsonl")


def main():
    parser = argparse.ArgumentParser(description="Bench étendu sur cas externes vierges pour la v1.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out", default="data_extended.json")
    args = parser.parse_args()
    rng = random.Random(args.seed)

    # 1. Exclusion : ce que la v1 a vu à l'entraînement (handoff 300 items)
    exclus = set()
    for line in open(HANDOFF, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        h = hashlib.md5((d["contexte"].strip() + "|" + d["question"].strip()).encode("utf-8")).hexdigest()
        exclus.add(h)
    print(f"[*] Exclusion de {len(exclus)} items vus à l'entraînement v1.")

    # 2. Pool candidat : mega-jeu vérifié, hors exclusions
    pool = []
    for line in open(MEGA, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        h = hashlib.md5((d["contexte"].strip() + "|" + d["question"].strip()).encode("utf-8")).hexdigest()
        if h in exclus:
            continue
        pool.append(d)
    print(f"[*] Pool vierge pour la v1 : {len(pool)} items.")

    # 3. Échantillonnage stratifié par catégorie
    par_cat = {}
    for d in pool:
        par_cat.setdefault(d["categorie"], []).append(d)
    echantillon = []
    cats = sorted(par_cat)
    part = args.n // len(cats)
    reste = args.n - part * len(cats)
    for i, cat in enumerate(cats):
        k = part + (1 if i < reste else 0)
        candidats = par_cat[cat][:]
        rng.shuffle(candidats)
        echantillon.extend(candidats[:k])
    rng.shuffle(echantillon)
    print(f"[*] Échantillon : {len(echantillon)} items sur {len(cats)} catégories.")

    # 4. Exécution
    engine = FoqEngine(base_url=args.base_url, profile_path="calibration_profile_8b_lora.json")
    if not engine.is_server_ready():
        print(f"[!] Serveur indisponible sur {args.base_url}")
        return
    ok, total, lat = 0, 0, []
    par_cat_res = {}
    cases = []
    t0 = time.perf_counter()
    for i, d in enumerate(echantillon, 1):
        options = [str(o) for o in d["options"]]
        rng.shuffle(options)
        correct = d["options"][d["index_correct"]]
        schema = ClassificationChoice(name=f"ext{i}", question=d["question"], categories=options)
        r = engine.decide(d["contexte"], schema, calibrate=True)
        lab = r.get("decision_label")
        bon = (lab == correct)
        ok += bon
        total += 1
        lat.append(r.get("latency_ms", 0))
        st = par_cat_res.setdefault(d["categorie"], [0, 0])
        st[0] += bon
        st[1] += 1
        cases.append({
            "id": hashlib.md5((d["contexte"].strip() + "|" + d["question"].strip()).encode("utf-8")).hexdigest(),
            "categorie": d["categorie"],
            "correct": bool(bon),
            "confidence": r.get("confidence", 0.0),
            "patched": r.get("patched_by"),
        })
        if i % 50 == 0:
            vit = i / (time.perf_counter() - t0)
            print(f"    {i}/{len(echantillon)} — {ok} bons ({ok/i*100:.1f} %) — {vit:.0f} déc/s", flush=True)
    dt = time.perf_counter() - t0
    lat.sort()
    score = ok / max(1, total) * 100

    print("\n=== BENCH ÉTENDU (cas jamais entraînés) ===")
    print(f"  Score global : {ok}/{total} ({score:.1f} %)")
    p50 = lat[len(lat)//2]
    print(f"  Latence P50  : {p50:.0f} ms   (débit moyen {total/dt:.0f} déc/s)")
    for cat in sorted(par_cat_res):
        c, t = par_cat_res[cat]
        print(f"    {cat:<32} {c:>3}/{t:<3} ({c/t*100:.0f} %)")

    # 5. Artefacts
    out = {
        "n": total, "correct": ok, "score_pct": round(score, 2),
        "latency_p50_ms": round(p50, 1),
        "per_category": {c: {"correct": v[0], "total": v[1]} for c, v in sorted(par_cat_res.items())},
        "note": "Cas externes vérifiés à l'aveugle, jamais vus par l'adaptateur v1 de production.",
    }
    out["cases"] = cases
    with open(os.path.join("docs", "assets", args.out), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[+] docs/assets/{args.out} écrit ({len(cases)} cas détaillés).")
    engine.close()


if __name__ == "__main__":
    main()
