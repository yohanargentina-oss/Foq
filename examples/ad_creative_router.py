import sys
import json
from foq import FoqEngine, Choice, Boolean, Score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def analyze_ad_creative(creative_text: str, engine: FoqEngine) -> dict:
    """Analyse un script/post publicitaire en une passe Système 1."""
    questions = {
        "funnel_stage": Choice(
            "Customer funnel stage target",
            choices={
                "top": "Top of Funnel (Notoriete / Decouverte / Probleme)",
                "middle": "Middle of Funnel (Comparaison / Solution / Demo)",
                "bottom": "Bottom of Funnel (Offre / Conversion / Promo)",
                "retention": "Post-Achat (Fidelisation / Avis)",
            },
        ),
        "hook_style": Choice(
            "Creative hook angle used",
            choices={
                "ugc_testimonial": "Temoignage client / Avis spontane",
                "pain_point": "Probleme / Frustration / Douleur",
                "behind_the_scenes": "Coulisses / Fabrication / Storytelling",
                "product_demo": "Demonstration produit / Solution",
                "discount_offer": "Code promo / Offre reduction / Urgence",
            },
        ),
        "has_clear_cta": Boolean("Le contenu contient-il un appel a l action clair (CTA) ?"),
        "risk_claims": Boolean("Y a-t-il des allegations medicales, trompeuses ou a risque ?"),
        "virality_potential": Score(
            "Score de potentiel viral ou d engagement",
            levels={"1": "Faible / Banal", "2": "Moyen", "3": "Fort / Tres viral"}
        ),
    }

    result = engine.system_one(
        state=f"Transcript / Ad Copy:\n{creative_text.strip()}",
        questions=questions,
        min_confidence=0.80,
    )

    return {
        "funnel_stage": {
            "value": result.funnel_stage.choice,
            "confidence": round(result.funnel_stage.confidence, 3),
        },
        "hook_style": {
            "value": result.hook_style.choice,
            "confidence": round(result.hook_style.confidence, 3),
        },
        "has_clear_cta": {
            "value": result.has_clear_cta.answer,
            "confidence": round(result.has_clear_cta.confidence, 3),
        },
        "risk_claims": {
            "value": result.risk_claims.answer,
            "confidence": round(result.risk_claims.confidence, 3),
        },
        "virality_score": {
            "score": result.virality_potential.score,
            "level": result.virality_potential.level,
            "confidence": round(result.virality_potential.confidence, 3),
        },
        "latency_ms": round(result.latency_ms, 1),
        "needs_human_review": result.needs_review,
    }


def route_creative(analysis: dict) -> str:
    """Aiguille automatiquement le contenu vers le bon canal selon l'analyse."""
    if analysis["risk_claims"]["value"] is True or "risk_claims" in analysis["needs_human_review"]:
        return "🚨 File de moderation manuelle (Risque de claim ou doute de conformite)"

    stage = analysis["funnel_stage"]["value"]
    style = analysis["hook_style"]["value"]

    if stage == "bottom" or analysis["has_clear_cta"]["value"]:
        return "🎯 Campagne Retargeting / Conversion directe (Meta Ads BOFU)"
    elif stage == "top" and style in ("ugc_testimonial", "pain_point"):
        return "📱 Campagne Acquisition TikTok / Reels (TOFU Cold Audience)"
    else:
        return "📊 Campagne Nurturing / Middle of Funnel"


if __name__ == "__main__":
    engine = FoqEngine()

    test_samples = [
        (
            "UGC Coussin Ergonomique",
            "J'ai teste 10 coussins ergonomiques differents pour mes douleurs de nuque le matin. "
            "Celui-ci est le seul qui a elimine mes migraines en 3 nuits. "
            "Cliquez sur le lien dans ma bio pour -20% avec le code NUQUE20 !"
        ),
        (
            "Coulisses Fabrication Bureau",
            "Saviez-vous que 80% des bureaux assis-debout tombent en panne apres 6 mois ? "
            "Voici comment nous concevons notre moteur a double verin dans nos ateliers a Lyon."
        ),
        (
            "Allégation médicale trompeuse",
            "Cette tisane guerit definitivement 100% de vos insomnies graves et remplace tous vos traitements medicaux sans ordonnance !"
        ),
        (
            "Acquisition TOFU Conforme (Douleur / Posture)",
            "Tu passes 8h par jour assis le dos voute devant ton ecran ? Voici 3 etirements simples a faire directement sur ta chaise."
        ),
    ]

    for title, sample in test_samples:
        print(f"\n==================================================")
        print(f"[TEST] {title}")
        print(f"Texte : \"{sample.strip()}\"")
        analysis = analyze_ad_creative(sample, engine)
        print("\nResultat de l'analyse Foq (Systeme 1) :")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("\nAiguillage automatique :", route_creative(analysis))
