"""
Speed and latency benchmark for Foq (`foq benchmark`).
Measures per-decision latency (ms) and throughput (decisions / second) on Foq 8B.
"""

import sys
import time

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .engine import FoqEngine
from .schemas import BinaryChoice


def main():
    print("=" * 60)
    print("  FOQ PERFORMANCE BENCHMARK (SYSTEM 1)")
    print("=" * 60)

    engine = FoqEngine(base_url="http://127.0.0.1:8089")
    if not engine.is_server_ready():
        print("[!] Foq server not reachable on http://127.0.0.1:8089.")
        return

    schema = BinaryChoice("urgency", "Is this ticket urgent?", "Yes, urgent", "No, normal")
    context = "The customer is asking for store opening hours."

    print("[*] Warming up...")
    engine.decide(context, schema)

    n_iterations = 20
    print(f"[*] Running benchmark across {n_iterations} consecutive requests...")

    latencies = []
    t_start = time.perf_counter()

    for i in range(n_iterations):
        res = engine.decide(f"{context} [id={i}]", schema)
        if res.get("success"):
            latencies.append(res["latency_ms"])

    total_time = time.perf_counter() - t_start
    decisions_per_sec = len(latencies) / total_time if total_time > 0 else 0

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]

    print("\n--- BENCHMARK RESULTS ---")
    print(f"  Successful decisions   : {len(latencies)} / {n_iterations}")
    print(f"  Total time             : {total_time:.2f} s")
    print(f"  Throughput             : {decisions_per_sec:.2f} decisions / second")
    print(f"  Min Latency            : {min(latencies):.2f} ms")
    print(f"  Median Latency (P50)   : {p50:.2f} ms")
    print(f"  P95 Latency            : {p95:.2f} ms")
    print(f"  Max Latency            : {max(latencies):.2f} ms")
    print("-------------------------")


if __name__ == "__main__":
    main()
