"""
Couche de correctifs déterministes pour Foq (neuro-symbolique).

Certains biais profonds du modèle (ex. l'énigme du dépassement) résistent au
fine-tuning : ils sont soudés dans les poids. Cette couche applique des
correctifs déterministes, auditables et désactivables, aux familles d'erreurs
CONNUES et CALCULABLES — uniquement quand la formulation est reconnue avec
confiance. Chaque correctif :
  - ne se déclenche que sur un motif précis (jamais à l'aveugle) ;
  - marque le résultat avec "patched_by" (transparence totale) ;
  - laisse la réponse brute intacte si le motif est ambigu.

Registre des défauts connus (KnownIssue) extensible : un nouvel échec répété du
banc hardcore devient un correctif + un test de régression.
"""

import re
from typing import Any, Callable, Dict, List, Optional

from .schemas import DecisionSchema


# ---------------------------------------------------------------------------
# Analyseurs d'ordinaux français
# ---------------------------------------------------------------------------

_MOTS_VERS_N = {
    "première": 1, "premier": 1, "1ère": 1, "1ere": 1, "1er": 1, "1re": 1,
    "deuxième": 2, "deuxieme": 2, "2ème": 2, "2eme": 2, "2e": 2,
    "seconde": 2, "second": 2,
    "troisième": 3, "troisieme": 3, "3ème": 3, "3eme": 3, "3e": 3,
    "quatrième": 4, "quatrieme": 4, "4ème": 4, "4eme": 4, "4e": 4,
    "cinquième": 5, "cinquieme": 5, "5ème": 5, "5eme": 5, "5e": 5,
    "sixième": 6, "sixieme": 6, "6ème": 6, "6eme": 6, "6e": 6,
    "septième": 7, "septieme": 7, "7ème": 7, "7eme": 7, "7e": 7,
    "huitième": 8, "huitieme": 8, "8ème": 8, "8eme": 8, "8e": 8,
    "neuvième": 9, "neuvieme": 9, "9ème": 9, "9eme": 9, "9e": 9,
    "dixième": 10, "dixieme": 10, "10ème": 10, "10eme": 10, "10e": 10,
}

# "en 2ème position", "en deuxième position", "en 3e position"
_POSITION_RE = re.compile(
    r"en\s+([0-9]+|1er|1re|1ère|1ere|[a-zàâéèêôûùç]+)\s*(?:è|e|eme|ème|er|ère|re)?\s*position",
    re.IGNORECASE,
)


def _extraire_position(texte: str) -> Optional[int]:
    """Extrait l'entier d'une mention « en N-ième position » (chiffre ou mot)."""
    m = _POSITION_RE.search(texte)
    if not m:
        return None
    brut = m.group(1).lower()
    if brut.isdigit():
        return int(brut)
    return _MOTS_VERS_N.get(brut)


def _libelle_position(n: int) -> str:
    if n == 1:
        return "1ère position"
    return f"{n}ème position"


# ---------------------------------------------------------------------------
# Correctif KI-001 : l'énigme du dépassement
# Défaut constaté : les modèles 8B ternaires répondent « 1ère position » avec
# une confiance élevée (3 fine-tunings n'ont pas délogé ce biais).
# Règle : doubler le coureur en N-ième position → on prend SA place (N-ième).
#         Se faire doubler quand on est N-ième → on recule d'une place (N+1).
# ---------------------------------------------------------------------------

_DOUBLE_VERBES = r"(doubles?|doubl\w*|dépass\w*|depasse\w*)"


def _ki001_trigger(context: str, question: str) -> bool:
    """La question porte-t-elle sur une position après dépassement ?"""
    tout = f"{context} {question}".lower()
    return bool(re.search(_DOUBLE_VERBES, tout) and "position" in tout)


def _ki001_corrigee(context: str, question: str) -> Optional[int]:
    """Renvoie la position correcte si le scénario est reconnu, sinon None.

    Conservateur : seuls deux schémas non ambigus sont corrigés ;
    au moindre conflit ou formulation inconnue, on ne touche à rien.
    """
    # Voix active : « tu/vous/je doubles/dépasse… » → je dépasse
    je_depasse = re.search(
        r"\b(tu|vous|je)\s+" + _DOUBLE_VERBES, context, re.IGNORECASE
    ) or re.search(r"\bj'(?:ai|e)\s+" + _DOUBLE_VERBES, context, re.IGNORECASE)
    # Voix passive : « on m'a doublé / on vous a dépassé… » → je suis doublé
    on_me_depasse = re.search(
        r"\b(me|m|te|nous|vous)'?\s*(?:a|ont|as|avez|est|sont)\s+" + _DOUBLE_VERBES,
        context, re.IGNORECASE,
    )
    if je_depasse and not on_me_depasse:
        n = _extraire_position(context)
        return n  # on prend la place du dépassé
    if on_me_depasse and not je_depasse:
        n = _extraire_position(context)
        if n is not None:
            return n + 1  # on recule d'une place
    return None


def _appliquer_ki001(context: str, question: str, schema: DecisionSchema, resultat: Dict[str, Any]) -> bool:
    cible = _ki001_corrigee(context, question)
    if cible is None:
        return False
    for opt in schema.options:
        m = re.search(r"(\d+)\s*(?:è|e|eme|ème|er|ère|re)?", opt.label.lower())
        if m and int(m.group(1)) == cible and ("position" in opt.label.lower() or cible == 1 and "1" in opt.label.lower()):
            resultat["decision_key"] = opt.key
            resultat["decision_label"] = opt.label
            resultat["confidence"] = 1.0
            return True
    return False


# ---------------------------------------------------------------------------
# KI-002 : pourcentages en chaîne (+50 % puis -50 % → -25 %, pas 0 %)
# Erreur constatée : les 8B additionnent les pourcentages au lieu de composer.
# Règle déterministe : facteur = (1+x1/100)(1+x2/100)…, delta = (facteur-1)*100.
# ---------------------------------------------------------------------------

_PCT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:%|por cent|pour cent)", re.IGNORECASE)
_BAISSE_RE = re.compile(r"(baisse\w*|diminu\w*|perte|réduct\w*|reduct\w*|perte|moins|chute|recul)", re.IGNORECASE)


def _ki002_trigger(context: str, question: str) -> bool:
    tout = f"{context} {question}"
    pcts = _PCT_RE.findall(tout)
    return len(pcts) >= 2 and bool(re.search(r"(augment|hausse|baisse|diminu|perte|chute)", tout, re.IGNORECASE))


def _ki002_delta(context: str) -> Optional[float]:
    """Compose les pourcentages dans l'ordre d'apparition ; signe par verbe proche."""
    signes = []
    for m in _PCT_RE.finditer(context):
        avant = context[max(0, m.start() - 40):m.start()]
        signe = -1 if _BAISSE_RE.search(avant) else 1
        signes.append((signe, float(m.group(1).replace(",", "."))))
    if len(signes) < 2:
        return None
    facteur = 1.0
    for signe, v in signes:
        facteur *= (1 + signe * v / 100.0)
    return round((facteur - 1) * 100)


def _appliquer_ki002(context: str, question: str, schema: DecisionSchema, resultat: Dict[str, Any]) -> bool:
    delta = _ki002_delta(context)
    if delta is None:
        return False
    cible_txt = f"{abs(delta):g}"
    for opt in schema.options:
        lab = opt.label
        if cible_txt in lab:
            if delta < 0 and not re.search(r"baisse|diminution|perte|perte|-|recul|moins", lab, re.IGNORECASE) and "+" not in lab:
                continue
            if delta > 0 and not re.search(r"hausse|augmentation|gain|\+|recul de -", lab, re.IGNORECASE) and "-" not in lab:
                continue
            resultat["decision_key"] = opt.key
            resultat["decision_label"] = opt.label
            resultat["confidence"] = 1.0
            return True
    return False


# ---------------------------------------------------------------------------
# KI-003 : fuseaux horaires (il est 8h00 à Paris, -5 h de décalage → 3h00)
# Erreur constatée : additions/décalages horaires mal posés par les 8B.
# Règle : (heure + décalage) mod 24.
# ---------------------------------------------------------------------------

_HEURE_RE = re.compile(r"\bil est (\d{1,2})h(\d{2})?\b", re.IGNORECASE)
_DECALAGE_RE = re.compile(r"([+-]?\s?\d+)\s*heures?\s+de\s+décalage", re.IGNORECASE)


def _ki003_trigger(context: str, question: str) -> bool:
    return bool(_HEURE_RE.search(context) and _DECALAGE_RE.search(context))


def _appliquer_ki003(context: str, question: str, schema: DecisionSchema, resultat: Dict[str, Any]) -> bool:
    hm = _HEURE_RE.search(context)
    dec = _DECALAGE_RE.search(context)
    if not hm or not dec:
        return False
    h = (int(hm.group(1)) + int(dec.group(1).replace(" ", ""))) % 24
    minutes = hm.group(2) or "00"
    cible = f"{h}h{minutes}" if minutes != "00" else f"{h}h"
    for opt in schema.options:
        lab = opt.label.replace(" ", "")
        if lab == cible or lab == f"{h}h{minutes}":
            resultat["decision_key"] = opt.key
            resultat["decision_label"] = opt.label
            resultat["confidence"] = 1.0
            return True
    return False


# ---------------------------------------------------------------------------
# Registre
# ---------------------------------------------------------------------------

KNOWN_ISSUES: List[Dict[str, Any]] = [
    {
        "id": "KI-001",
        "trigger": _ki001_trigger,
        "apply": _appliquer_ki001,
        "note": "Énigme du dépassement : biais soudé des 8B ternaires (répondre 1er). "
                "Règle déterministe : dépasser le N-ième → finir N-ième.",
    },
    {
        "id": "KI-002",
        "trigger": _ki002_trigger,
        "apply": _appliquer_ki002,
        "note": "Pourcentages en chaîne : les 8B additionnent au lieu de composer. "
                "Règle : facteur multiplicatif, signe par verbe (hausse/baisse).",
    },
    {
        "id": "KI-003",
        "trigger": _ki003_trigger,
        "apply": _appliquer_ki003,
        "note": "Fuseaux horaires : (heure + décalage) mod 24, appliqué sur formulation explicite.",
    },
]


def appliquer_correctifs(context: str, question: str, schema: DecisionSchema,
                         resultat: Dict[str, Any], actifs: bool = True) -> Dict[str, Any]:
    """Applique les correctifs connus au résultat brut d'une décision.

    Ne modifie le résultat QUE si un motif connu est reconnu avec certitude ;
    sinon le résultat brut traverse intact. Un résultat corrigé porte
    "patched_by": "<id du correctif>".
    """
    if not actifs or not resultat.get("success", False):
        return resultat
    brut = resultat.get("decision_label")
    for ki in KNOWN_ISSUES:
        if ki["trigger"](context, question):
            if ki["apply"](context, question, schema, resultat):
                resultat["patched_by"] = ki["id"]
                if brut is not None:
                    resultat["raw_decision_label"] = brut
                break
    return resultat
