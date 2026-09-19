# -*- coding: utf-8 -*-
"""
Assembleur et validateur strict des 300 items pour Foq.
"""

import sys
import os
import json

# Ajout du dossier au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset_builder.c01_spatial import SPATIAL_ITEMS
from dataset_builder.c02_linguistique import LINGUISTIQUE_ITEMS
from dataset_builder.c03_sens_commun import SENS_COMMUN_ITEMS
from dataset_builder.c04_maths import MATHS_ITEMS
from dataset_builder.c05_negations import NEGATIONS_ITEMS
from dataset_builder.c06_physiologie import PHYSIOLOGIE_ITEMS
from dataset_builder.c07_securite import SECURITE_ITEMS
from dataset_builder.c08_sentiment import SENTIMENT_ITEMS
from dataset_builder.c09_routage import ROUTAGE_ITEMS
from dataset_builder.c10_triage import TRIAGE_ITEMS

all_pools = [
    ("raisonnement_spatial", SPATIAL_ITEMS, 35),
    ("enigme_linguistique", LINGUISTIQUE_ITEMS, 35),
    ("sens_commun", SENS_COMMUN_ITEMS, 35),
    ("maths_contre_intuitives", MATHS_ITEMS, 35),
    ("negations_multiples", NEGATIONS_ITEMS, 30),
    ("physiologie_contre_intuitive", PHYSIOLOGIE_ITEMS, 30),
    ("securite_info", SECURITE_ITEMS, 25),
    ("sentiment", SENTIMENT_ITEMS, 25),
    ("routage", ROUTAGE_ITEMS, 25),
    ("triage", TRIAGE_ITEMS, 25),
]

all_items = []
errors = []

# Mots ou thèmes interdits par l'énoncé
banned_checks = [
    "double le 2ème", "plumes", "plomb", "trois fils", "oiseaux sur une branche",
    "50 km/h puis 100 km/h", "i <= 5", "kaliémie", "7.2 mmol", "pig butchering",
    "whatsapp", "indemnité sur triple négation", "override admin",
    "ignore toutes les instructions", "pas mauvais du tout",
    "ni passionnant ni catastrophe", "0.95 g/l", "logo décalé de 2 pixels",
    "incendie de la salle serveurs"
]

allowed_categories = {
    "raisonnement_spatial", "enigme_linguistique", "sens_commun",
    "maths_contre_intuitives", "negations_multiples", "physiologie_contre_intuitive",
    "securite_info", "sentiment", "routage", "triage"
}

for cat_name, pool, expected_len in all_pools:
    if len(pool) != expected_len:
        errors.append(f"Catégorie {cat_name}: {len(pool)} items au lieu de {expected_len}")
    
    for i, item in enumerate(pool):
        # Vérification des clés exactes
        required_keys = {"contexte", "question", "options", "index_correct", "categorie"}
        if set(item.keys()) != required_keys:
            errors.append(f"[{cat_name} #{i}] Clés invalides: {item.keys()}")
        
        # Catégorie exacte
        if item["categorie"] != cat_name or item["categorie"] not in allowed_categories:
            errors.append(f"[{cat_name} #{i}] Nom de catégorie invalide: {item['categorie']}")
        
        # Options
        opts = item["options"]
        if len(opts) != 3:
            errors.append(f"[{cat_name} #{i}] Nombre d'options != 3 ({len(opts)})")
        
        for o_idx, opt in enumerate(opts):
            words = opt.split()
            if len(words) > 12:
                errors.append(f"[{cat_name} #{i} opt {o_idx}] Option trop longue ({len(words)} mots): '{opt}'")
            if len(opt.strip()) == 0:
                errors.append(f"[{cat_name} #{i} opt {o_idx}] Option vide")

        # Unicité des options
        if len(set(opts)) != 3:
            errors.append(f"[{cat_name} #{i}] Options non distinctes: {opts}")
        
        # Index correct
        if item["index_correct"] not in (0, 1, 2):
            errors.append(f"[{cat_name} #{i}] index_correct hors limites: {item['index_correct']}")
        
        # Anti-contamination
        raw_str = json.dumps(item, ensure_ascii=False).lower()
        for b in banned_checks:
            if b in raw_str:
                errors.append(f"[{cat_name} #{i}] Contient un élément banni '{b}'")
        
        all_items.append(item)

print(f"Total items assemblés : {len(all_items)}")

# Distribution des index
index_counts = {0: 0, 1: 0, 2: 0}
for it in all_items:
    index_counts[it["index_correct"]] += 1

print("\nDistribution globale de 'index_correct' :")
for idx, count in sorted(index_counts.items()):
    print(f"  - Index {idx} : {count} items ({count / len(all_items) * 100:.1f} %)")

if errors:
    print(f"\n[ERREURS] ({len(errors)}) :")
    for e in errors:
        print("  - " + e)
    sys.exit(1)
else:
    print("\n[SUCCES] AUCUNE ERREUR : 100% de conformite sur toutes les regles !")

# Ecriture du fichier final
output_path = os.path.join("data", "_external", "dataset_avance.jsonl")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(json.dumps(item, ensure_ascii=False) for item in all_items))

print(f"\nFichier JSONL genere avec succes : {output_path}")
print(f"Taille du fichier : {os.path.getsize(output_path)} octets")
