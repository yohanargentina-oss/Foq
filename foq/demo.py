"""
Interactive demonstration for Foq (`foq demo`).
Shows instant System 1 decisions with calibrated probability distributions.
"""

import sys
import json

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .engine import FoqEngine
from .schemas import BinaryChoice, ClassificationChoice, Boolean, Choice, Score


def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def format_bar(prob: float, length: int = 25) -> str:
    filled = int(round(prob * length))
    return "█" * filled + "░" * (length - filled)


def main():
    print_separator("⚡ FOQ SYSTEM 1 ENGINE - DEMONSTRATION")
    engine = FoqEngine(base_url="http://127.0.0.1:8089")

    if not engine.is_server_ready():
        print("[!] Foq server is not running on http://127.0.0.1:8089.")
        print("[>] Launch the server first using: start_foq_server.cmd (or .sh)")
        return

    print("[+] Successfully connected to Foq server.")
    print(f"[*] Active calibration temperature: T = {engine.scaler.temperature:.3f}")

    # Test 1: Fast Binary Detection
    print_separator("Test 1: Spam / Phishing Detection (Binary)")
    text_1 = "URGENT: Your bank card has been suspended. Click here immediately to verify your credentials: http://bit.ly/secure-fake"
    schema_1 = BinaryChoice(
        name="is_phishing",
        question="Is this message a phishing attempt or scam?",
        true_label="Phishing / Scam",
        false_label="Legitimate message",
    )
    print(f"Input text:\n\"{text_1}\"")
    res_1 = engine.decide(text_1, schema_1)

    print(f"\nVerdict    : {res_1['decision_label']} ({res_1['confidence'] * 100:.1f}%)")
    print(f"Latency    : {res_1['latency_ms']:.1f} ms | Predicted tokens: {res_1['tokens_predicted']}")
    print("Calibrated distribution:")
    for k, p in res_1["calibrated_probabilities"].items():
        lbl = next(opt.label for opt in schema_1.options if opt.key == k)
        print(f"  [{k}] {lbl:<25} : {p*100:5.1f}% |{format_bar(p)}|")

    # Test 2: Multi-class Routing
    print_separator("Test 2: Support Ticket Routing (Multi-class)")
    text_2 = "Hello, I was billed twice for my September subscription, order #84920. Could you please refund the duplicate charge?"
    schema_2 = ClassificationChoice(
        name="ticket_category",
        question="Which department should handle this ticket?",
        categories=["Billing & Refunds", "Technical Bug Support", "Sales & Commercial", "Other"],
    )
    print(f"Ticket:\n\"{text_2}\"")
    res_2 = engine.decide(text_2, schema_2)

    print(f"\nSelected route: {res_2['decision_label']} ({res_2['confidence'] * 100:.1f}%)")
    print(f"Latency       : {res_2['latency_ms']:.1f} ms")
    for k, p in res_2["calibrated_probabilities"].items():
        lbl = next(opt.label for opt in schema_2.options if opt.key == k)
        print(f"  [{k}] {lbl:<30} : {p*100:5.1f}% |{format_bar(p)}|")

    # Test 3: Parallel Multi-field Evaluation
    print_separator("Test 3: Parallel Multi-field Evaluation (System 1 JSON Schema)")
    text_3 = "Our production database server crashed! No customers can log in for the past 10 minutes!"
    schemas_multi = [
        ClassificationChoice(
            name="severity",
            question="What is the severity level of this incident?",
            categories=["Critical (P0)", "High (P1)", "Medium (P2)", "Low (P3)"],
        ),
        ClassificationChoice(
            name="impacted_domain",
            question="Which technical domain is affected?",
            categories=["Infrastructure / Servers", "Frontend / CSS", "Billing", "Human Resources"],
        ),
        BinaryChoice(
            name="page_oncall",
            question="Should the on-call engineer be paged immediately?",
            true_label="Yes, page immediately",
            false_label="No, wait for business hours",
        ),
    ]

    print(f"Incident report:\n\"{text_3}\"")
    res_multi = engine.decide_multi(text_3, schemas_multi)

    print(f"\nTotal execution time (3 resolved decisions): {res_multi['total_latency_ms']:.1f} ms")
    print("Typed structured output:")
    print(json.dumps(res_multi["structured_output"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
