"""
Banc de Benchmark Comparatif Multi-Modèles pour Foq.
Compare en direct :
1. Foq 27B (llama.cpp port 8089)
2. Llama-3.2-1B (Ollama port 11434)
3. Qwen-2.5-1.5B (Ollama port 11434)

Évalue :
- 35 tests de précision réelle (Sécurité, Médical, Sentiment, Support, Triage, Logique)
- 10 pièges cognitifs hardcore adversariaux (Physique, Enigmes, Injections, Négations triples)
Mesure l'exactitude exacte (%), la latence médiane (ms) et le débit (décisions/sec).
"""

import sys
import os
import time
import requests
import json
from typing import List, Dict, Any, Tuple

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq.schemas import ClassificationChoice
from scripts.precision_benchmark import TEST_DATASET
from scripts.hardcore_benchmark import HARDCORE_TESTS


def evaluate_ollama(model_name: str, context: str, schema: ClassificationChoice) -> Tuple[str, float]:
    prompt = schema.format_prompt(context)
    t0 = time.perf_counter()
    try:
        r = requests.post("http://127.0.0.1:11434/api/generate", json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 1, "temperature": 0.0}
        }, timeout=5.0).json()
        dt = (time.perf_counter() - t0) * 1000
        raw_tok = r.get("response", "").strip().strip("[]():").upper()
        opt_map = {opt.key: opt.label for opt in schema.options}
        decision = opt_map.get(raw_tok, "INVALIDE")
        return decision, dt
    except Exception as e:
        return "ERREUR", (time.perf_counter() - t0) * 1000


def evaluate_foq_server(context: str, schema: ClassificationChoice) -> Tuple[str, float]:
    prompt = schema.format_prompt(context)
    valid_keys = schema.get_keys()
    t0 = time.perf_counter()
    try:
        r = requests.post("http://127.0.0.1:8089/completion", json={
            "prompt": prompt,
            "n_predict": 1,
            "n_probs": 25,
            "temperature": 0.0,
        }, timeout=10.0).json()
        dt = (time.perf_counter() - t0) * 1000
        completion_probs = r.get("completion_probabilities", [])
        raw_logprobs_map = {k: -25.0 for k in valid_keys}
        if completion_probs and len(completion_probs) > 0:
            for item in completion_probs[0].get("top_logprobs", []):
                tok = item.get("token", "").strip().strip("[]():").upper()
                lp = item.get("logprob", -25.0)
                if tok in raw_logprobs_map:
                    if lp > raw_logprobs_map[tok]:
                        raw_logprobs_map[tok] = lp
        best_k = max(raw_logprobs_map.keys(), key=lambda k: raw_logprobs_map[k])
        opt_map = {opt.key: opt.label for opt in schema.options}
        return opt_map.get(best_k, best_k), dt
    except Exception as e:
        return "ERREUR", (time.perf_counter() - t0) * 1000


def run_benchmark_suite(eval_fn, model_title: str):
    print(f"\n{'='*72}")
    print(f"  🚀 ÉVALUATION DU MODÈLE : {model_title}")
    print(f"{'='*72}")

    # 1. Benchmark Standard (35 tests)
    print("\n--- PARTIE 1 : BENCHMARK DE PRÉCISION GÉNÉRALE (35 cas) ---")
    prec_correct = 0
    prec_latencies = []
    prec_failures = []

    for idx, test in enumerate(TEST_DATASET, 1):
        schema = ClassificationChoice(
            name="test_schema",
            question=test["question"],
            categories=test["options"]
        )
        dec, lat = eval_fn(test["context"], schema)
        prec_latencies.append(lat)
        expected = test["target"]
        is_ok = (dec == expected)
        if is_ok:
            prec_correct += 1
            icon = "✅"
        else:
            icon = "❌"
            prec_failures.append((test["id"], test["question"], expected, dec))
        
        # Affichage compact
        print(f"[{idx:02d}/35] {icon} {test['id']:<10} | {lat:4.0f}ms | Attendu: {expected[:25]:<25} | Prédit: {dec[:25]}")

    prec_acc = (prec_correct / len(TEST_DATASET)) * 100
    p50_prec = sorted(prec_latencies)[len(prec_latencies)//2]

    # 2. Benchmark Hardcore (10 pièges cognitifs)
    print("\n--- PARTIE 2 : PIÈGES COGNITIFS HARDCORE & INJECTIONS (10 cas) ---")
    hard_correct = 0
    hard_latencies = []
    hard_failures = []

    for idx, test in enumerate(HARDCORE_TESTS, 1):
        schema = ClassificationChoice(
            name="hardcore_schema",
            question=test["question"],
            categories=test["options"]
        )
        dec, lat = eval_fn(test["context"], schema)
        hard_latencies.append(lat)
        expected = test["target"]
        is_ok = (dec == expected)
        if is_ok:
            hard_correct += 1
            icon = "✅"
        else:
            icon = "❌"
            hard_failures.append((test["id"], test["question"], expected, dec))
        
        print(f"[{idx:02d}/10] {icon} {test['id']:<12} | {lat:4.0f}ms | Attendu: {expected[:25]:<25} | Prédit: {dec[:25]}")

    hard_acc = (hard_correct / len(HARDCORE_TESTS)) * 100
    p50_hard = sorted(hard_latencies)[len(hard_latencies)//2]

    total_tests = len(TEST_DATASET) + len(HARDCORE_TESTS)
    total_correct = prec_correct + hard_correct
    overall_acc = (total_correct / total_tests) * 100
    all_latencies = prec_latencies + hard_latencies
    global_p50 = sorted(all_latencies)[len(all_latencies)//2]
    mean_lat = sum(all_latencies) / len(all_latencies)

    print(f"\n{'-'*72}")
    print(f"  RÉSUMÉ POUR {model_title} :")
    print(f"  • Précision Générale (35 cas) : {prec_correct}/35 ({prec_acc:.1f}%) | Latence P50: {p50_prec:.1f} ms")
    print(f"  • Pièges Hardcore (10 cas)    : {hard_correct}/10 ({hard_acc:.1f}%) | Latence P50: {p50_hard:.1f} ms")
    print(f"  • SCORE GLOBAL COMBINÉ        : {total_correct}/{total_tests} ({overall_acc:.1f}%)")
    print(f"  • Vitesse Médiane (P50)       : {global_p50:.1f} ms ({1000/global_p50:.1f} décisions/sec)")
    print(f"  • Vitesse Moyenne             : {mean_lat:.1f} ms")
    print(f"{'-'*72}")

    return {
        "model": model_title,
        "prec_acc": prec_acc,
        "hard_acc": hard_acc,
        "overall_acc": overall_acc,
        "p50_ms": global_p50,
        "prec_failures": prec_failures,
        "hard_failures": hard_failures,
    }


def main():
    print("=" * 72)
    print("  🏆 GRAND COMPARATIF BENCHMARK FOQ : FOQ 27B vs LLAMA-3.2 vs QWEN-2.5")
    print("  Hardware : NVIDIA RTX 4080 Super (16 Go VRAM) - Windows 11")
    print("=" * 72)

    results = []

    # 1. Évaluation Qwen-2.5-1.5B
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.0)
        qwen_ready = any("qwen2.5:1.5b" in m["name"] for m in r.json().get("models", []))
    except Exception:
        qwen_ready = False

    if qwen_ready:
        res_qwen = run_benchmark_suite(
            lambda ctx, sch: evaluate_ollama("qwen2.5:1.5b", ctx, sch),
            "Qwen-2.5-1.5B (Ollama)"
        )
        results.append(res_qwen)

    # 2. Évaluation Llama-3.2-1B
    try:
        llama_ready = any("llama3.2:1b" in m["name"] for m in r.json().get("models", []))
    except Exception:
        llama_ready = False

    if llama_ready:
        res_llama = run_benchmark_suite(
            lambda ctx, sch: evaluate_ollama("llama3.2:1b", ctx, sch),
            "Llama-3.2-1B (Ollama)"
        )
        results.append(res_llama)

    # 3. Évaluation Foq 27B
    try:
        r_foq = requests.get("http://127.0.0.1:8089/health", timeout=1.0)
        foq_ready = (r_foq.status_code == 200)
    except Exception:
        foq_ready = False

    if foq_ready:
        res_foq = run_benchmark_suite(
            evaluate_foq_server,
            "Foq-27B Système 1 (llama.cpp)"
        )
        results.append(res_foq)

    # Tableau Récapitulatif Final
    print("\n" + "=" * 72)
    print("  🏁 TABLEAU COMPARATIF FINAL DES PERFORMANCES")
    print("=" * 72)
    print(f"{'Modèle':<30} | {'Précision (35)':<14} | {'Hardcore (10)':<13} | {'Global':<8} | {'Latence P50':<12}")
    print("-" * 85)
    for res in results:
        print(f"{res['model']:<30} | {res['prec_acc']:5.1f}%        | {res['hard_acc']:5.1f}%       | {res['overall_acc']:5.1f}%  | {res['p50_ms']:5.1f} ms")
    print("=" * 85)


if __name__ == "__main__":
    main()
