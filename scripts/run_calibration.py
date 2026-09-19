"""
Script d'étalonnage et d'optimisation de la calibration (RLCD / Temperature Scaling).
Évalue les prédictions brutes vs la vérité terrain, calcule l'ECE (Expected Calibration Error),
trouve la température optimale T* pour éliminer la sur-confiance, et enregistre le profil.
"""

import sys
import os
import json
import math
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq.engine import FoqEngine
from foq.schemas import ClassificationChoice
from foq.calibration import ExpectedCalibrationError, BrierScore, TemperatureScaler, CalibrationProfile


def main():
    parser = argparse.ArgumentParser(description="Calibration RLCD (Temperature Scaling) pour un serveur Foq.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8089", help="URL du serveur llama-server à calibrer")
    parser.add_argument("--output", default="calibration_profile.json", help="Fichier profil de sortie")
    parser.add_argument("--alias", default="foq", help="Alias du modèle pour le profil")
    args = parser.parse_args()

    print("=" * 65)
    print("  ÉVALUATION ET CALIBRATION STATISTIQUE RLCD POUR FOQ")
    print(f"  Serveur : {args.base_url} | Sortie : {args.output}")
    print("=" * 65)

    engine = FoqEngine(base_url=args.base_url)
    if not engine.is_server_ready():
        print(f"[!] Le serveur Foq n'est pas actif sur {args.base_url}.")
        return

    dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "calibration_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"[*] Chargement du dataset de calibration ({len(dataset)} exemples)...")

    raw_confidences = []
    correctness = []
    optimization_data = []

    print("[*] Évaluation des décisions en cours...")
    for idx, item in enumerate(dataset):
        schema = ClassificationChoice(
            name=f"task_{idx}",
            question=item["question"],
            categories=item["categories"],
        )
        # Appel sans calibration pour obtenir les logprobs et probabilités brutes
        res = engine.decide(item["context"], schema, calibrate=False)
        target_key = schema.options[item["target_idx"]].key

        is_correct = (res["decision_key"] == target_key)
        conf = res["confidence"]

        raw_confidences.append(conf)
        correctness.append(is_correct)

        # Logprobs brutes pour l'optimiseur
        # On reconstitue les logprobs relatives à partir des probabilités brutes
        raw_probs = res["raw_probabilities"]
        logprobs = {k: math.log(max(1e-12, v)) for k, v in raw_probs.items()}
        optimization_data.append({
            "logprobs": logprobs,
            "correct_choice": target_key,
        })

    # Calcul des métriques brutes
    ece_calc = ExpectedCalibrationError(n_bins=5)
    raw_ece_res = ece_calc.compute(raw_confidences, correctness)
    raw_brier = BrierScore.compute(raw_confidences, [1 if c else 0 for c in correctness])

    print("\n--- RÉSULTATS AVANT CALIBRATION (Modèle Brut) ---")
    print(f"  Exactitude (Accuracy)          : {sum(correctness)/len(correctness)*100:.1f}%")
    print(f"  Confiance moyenne affichée     : {sum(raw_confidences)/len(raw_confidences)*100:.1f}%")
    print(f"  Expected Calibration Error (ECE): {raw_ece_res['ece_percentage']}")
    print(f"  Brier Score (plus bas = mieux) : {raw_brier:.4f}")

    # Optimisation de la température T*
    print("\n[*] Recherche de la température optimale T*...")
    scaler = TemperatureScaler(temperature=1.0)
    best_t = scaler.fit(optimization_data)

    # Réévaluation avec la température optimisée
    calibrated_confidences = []
    for item in optimization_data:
        scaled_probs = scaler.scale_probabilities(item["logprobs"])
        best_k = max(scaled_probs.keys(), key=lambda k: scaled_probs[k])
        calibrated_confidences.append(scaled_probs[best_k])

    calib_ece_res = ece_calc.compute(calibrated_confidences, correctness)
    calib_brier = BrierScore.compute(calibrated_confidences, [1 if c else 0 for c in correctness])

    print("\n--- RÉSULTATS APRÈS CALIBRATION RLCD ---")
    print(f"  Température optimale trouvée T*: {best_t:.3f}")
    print(f"  Nouvelle confiance moyenne      : {sum(calibrated_confidences)/len(calibrated_confidences)*100:.1f}%")
    print(f"  Nouvel ECE                     : {calib_ece_res['ece_percentage']} (Erreur d'écart réduite)")
    print(f"  Nouveau Brier Score            : {calib_brier:.4f}")

    # Sauvegarde du profil
    profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", args.output))
    profile = CalibrationProfile(profile_path)
    profile.temperature = best_t
    profile.ece = calib_ece_res["ece"]
    profile.brier_score = calib_brier
    profile.model_alias = args.alias
    profile.save()
    print(f"\n[+] Profil de calibration enregistré dans : {profile_path}")
    print("[+] Chargez-le via FoqEngine(profile_path=...) pour ce modèle !")


if __name__ == "__main__":
    main()
