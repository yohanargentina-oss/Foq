"""
Import d'un fichier de données d'entraînement externe (handoff from-agent-*.md)
vers le format LoRA Foq, avec vérification à l'aveugle par un modèle juge.

- Valide le schéma JSONL externe : {"contexte", "question", "options"[3], "index_correct", "categorie"}.
- Convertit chaque item en prompt Foq EXACT via ClassificationChoice (options mélangées).
- Si --verify-url est fourni : le juge (ex. 27B CRACK) résout chaque item à l'aveugle ;
  seuls les items où le juge retrouve la réponse attendue sont conservés.
  Les désaccords sont listés (items ambigus ou mal étiquetés) et écartés.
- Fusionne avec data/lora_dataset.jsonl et reconstitue un découpage train/eval (5 %).
"""

import sys
import os
import json
import random
import hashlib
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq.engine import FoqEngine
from foq.schemas import ClassificationChoice

REQUIRED_FIELDS = {"contexte", "question", "options", "index_correct", "categorie"}


def load_and_validate(path):
    items, errors = [], []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception as e:
                errors.append(f"ligne {i}: JSON invalide ({e})")
                continue
            if set(d.keys()) != REQUIRED_FIELDS:
                errors.append(f"ligne {i}: champs invalides {sorted(d.keys())}")
                continue
            opts = d["options"]
            if not (isinstance(opts, list) and len(opts) == 3 and len(set(map(str, opts))) == 3):
                errors.append(f"ligne {i}: options invalides")
                continue
            if d["index_correct"] not in (0, 1, 2):
                errors.append(f"ligne {i}: index_correct invalide")
                continue
            if len(d["contexte"]) < 25 or len(d["question"]) < 8:
                errors.append(f"ligne {i}: texte trop court")
                continue
            items.append(d)
    return items, errors


def main():
    parser = argparse.ArgumentParser(description="Import + vérification de données externes pour le LoRA Foq.")
    parser.add_argument("input", help="Fichier JSONL externe (ex: from-agent-dataset-avance.md)")
    parser.add_argument("--verify-url", default=None, help="Serveur du modèle juge (ex: http://127.0.0.1:8089)")
    parser.add_argument("--dataset", default=os.path.join("data", "lora_dataset.jsonl"))
    parser.add_argument("--eval-frac", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    print("=" * 66)
    print("  IMPORT DE DONNÉES EXTERNES + VÉRIFICATION À L'AVEUGLE")
    print("=" * 66)

    items, errors = load_and_validate(args.input)
    print(f"[*] {len(items)} items valides, {len(errors)} rejetés au schéma.")
    for e in errors[:10]:
        print("    ", e)

    # Conversion en prompts Foq (position de la bonne réponse uniforme — anti-biais de lettre)
    converted = []
    for d in items:
        correct = str(d["options"][d["index_correct"]])
        options = [str(o) for o in d["options"] if str(o) != correct]
        rng.shuffle(options)
        options.insert(rng.randrange(3), correct)
        schema = ClassificationChoice(name="ext", question=d["question"], categories=options)
        converted.append({
            "prompt": schema.format_prompt(d["contexte"]),
            "target_letter": chr(65 + options.index(correct)),
            "domain": f"ext_{d['categorie']}",
            "source": "external",
            "context": d["contexte"],
            "question": d["question"],
            "correct_text": correct,
            "options_order": options,
        })
    print(f"[*] {len(converted)} items convertis au format Foq (options mélangées).")

    # Vérification à l'aveugle par le juge
    kept = converted
    if args.verify_url:
        engine = FoqEngine(base_url=args.verify_url)
        if not engine.is_server_ready():
            print(f"[!] Juge indisponible sur {args.verify_url} — import sans vérification.")
        else:
            kept, dropped = [], []
            for c in converted:
                schema = ClassificationChoice(name="verify", question=c["question"], categories=c["options_order"])
                res = engine.decide(c["context"], schema, calibrate=False)
                if res.get("success") and res.get("decision_key") == c["target_letter"]:
                    kept.append(c)
                else:
                    dropped.append((c, res.get("decision_label"), res.get("confidence")))
            print(f"[*] Juge : {len(kept)} accordés / {len(dropped)} écartés (ambigus ou mal étiquetés).")
            for c, pred, conf in dropped[:15]:
                print(f"    [écarté] {c['context'][:70]}... | juge='{pred}' ({conf:.0%}) vs attendu='{c['correct_text']}'")
            engine.close()

    # Fusion avec le jeu existant + nouveau découpage train/eval
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", args.dataset))
    existing = []
    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            existing = [json.loads(l) for l in f if l.strip()]
    print(f"[*] Jeu existant : {len(existing)} exemples.")

    merged = existing + [
        {"prompt": c["prompt"], "target_letter": c["target_letter"], "domain": c["domain"], "source": c["source"]}
        for c in kept
    ]
    # Déduplication finale sur le prompt
    seen, unique = set(), []
    for e in merged:
        h = hashlib.md5(e["prompt"].encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        unique.append(e)
    rng.shuffle(unique)

    n_eval = max(1, int(len(unique) * args.eval_frac))
    eval_set, train_set = unique[:n_eval], unique[n_eval:]
    with open(dataset_path, "w", encoding="utf-8") as f:
        for e in train_set:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    eval_path = dataset_path.replace(".jsonl", "_eval.jsonl")
    with open(eval_path, "w", encoding="utf-8") as f:
        for e in eval_set:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    letters = {}
    for e in train_set:
        letters[e["target_letter"]] = letters.get(e["target_letter"], 0) + 1
    print(f"\n[+] ENTRAÎNEMENT : {len(train_set)} exemples -> {dataset_path}")
    print(f"[+] ÉVALUATION   : {len(eval_set)} exemples -> {eval_path}")
    print(f"[+] Lettres cibles : {dict(sorted(letters.items()))}")


if __name__ == "__main__":
    main()
