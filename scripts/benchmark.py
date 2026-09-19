"""
Benchmark de vitesse et de latence pour Foq.
Mesure la latence par décision (ms) et le débit (décisions / seconde) sur Foq 27B.
"""

import sys
import os
import time

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq.engine import FoqEngine
from foq.schemas import BinaryChoice


def main():
    print("=" * 60)
    print("  BENCHMARK DE PERFORMANCE FOQ (SYSTEM 1)")
    print("=" * 60)

    engine = FoqEngine(base_url="http://127.0.0.1:8089")
    if not engine.is_server_ready():
        print("[!] Serveur Foq introuvable sur http://127.0.0.1:8089.")
        return

    schema = BinaryChoice("urgence", "Ce ticket est-il urgent ?", "Oui, urgent", "Non, normal")
    context = "Le client demande un renseignement sur les horaires d'ouverture."

    print("[*] Échauffement (Warmup)...")
    engine.decide(context, schema)

    n_iterations = 20
    print(f"[*] Lancement du test sur {n_iterations} requêtes consécutives...")

    latencies = []
    t_start = time.perf_counter()

    for i in range(n_iterations):
        res = engine.decide(f"{context} [id={i}]", schema)
        if res.get("success"):
            latencies.append(res["latency_ms"])

    total_time = time.perf_counter() - t_start
    decisions_per_sec = len(latencies) / total_time

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]

    print("\n--- RÉSULTATS DU BENCHMARK ---")
    print(f"  Décisions réussies        : {len(latencies)} / {n_iterations}")
    print(f"  Temps total               : {total_time:.2f} s")
    print(f"  Débit                     : {decisions_per_sec:.2f} décisions / seconde")
    print(f"  Latence Min               : {min(latencies):.2f} ms")
    print(f"  Latence Médiane (P50)     : {p50:.2f} ms")
    print(f"  Latence P95               : {p95:.2f} ms")
    print(f"  Latence Max               : {max(latencies):.2f} ms")
    print("--------------------------------")


if __name__ == "__main__":
    main()
