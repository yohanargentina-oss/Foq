import json
import sys
from foq import FoqEngine, Choice, Boolean, Score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def score_tweet(tweet_text: str, engine: FoqEngine) -> dict:
    """Analyse un tweet ou hook de post en une passe Système 1 (25 ms)."""
    questions = {
        "viral_trigger": Choice(
            "Quel est le levier psychologique dominant utilise dans ce post ?",
            choices={
                "curiosity_gap": "Boucle de curiosite / Mystere non resolu",
                "contrarian": "Avis a contre-courant / Controverse / Mythe casse",
                "high_value_framework": "Valeur actionnable / Framework / Guide pratique",
                "vulnerable_story": "Storytelling personnel / Echec surmonte",
                "boring_announcement": "Annonce banale / Auto-promo sans angle",
            },
        ),
        "virality_score": Score(
            "Potentiel de repartage (Retweets / Reposts) et de diffusion algorithmique",
            levels={
                "1": "Faible (Moins de 10 retweets - Banal / Plat)",
                "2": "Moyen (Portee organique standard)",
                "3": "Bon (Fort engagement de la communaute existante)",
                "4": "Tres fort (Potentiel de breakout hors de l'audience)",
                "5": "Viral massif (Hook exceptionnel / Debat generalise)",
            },
        ),
        "comment_bait": Boolean(
            "Le post incite-t-il naturellement les gens a donner leur avis ou a debattre en reponse ?"
        ),
        "is_cheap_clickbait": Boolean(
            "Le post utilise-t-il un formatage force, racoleur ou vide de substance reelle ?"
        ),
    }

    result = engine.system_one(
        state=f"Brouillon de Tweet / Post :\n\"{tweet_text.strip()}\"",
        questions=questions,
        min_confidence=0.80,
    )

    return {
        "trigger": result.viral_trigger.choice,
        "score": result.virality_score.level,
        "generates_debate": result.comment_bait.answer,
        "cheap_clickbait": result.is_cheap_clickbait.answer,
        "confidence": round(result.virality_score.confidence, 2),
        "latency_ms": round(result.latency_ms, 1),
        "needs_review": result.needs_review,
    }


def get_recommendation(analysis: dict) -> str:
    """Genere le diagnostic et le conseil d'optimisation."""
    if analysis["cheap_clickbait"]:
        return "⚠️ Trop racoleur / Cringe : apportez plus de substance pour eviter de devaleuriser votre compte."

    score = int(analysis["score"])
    if score >= 4:
        return "🔥 Excellent hook : tres fort potentiel viral."
    elif score == 3:
        return "👍 Bon post de fond pour votre audience fidele."
    else:
        return "💤 Manque d'angle : retravaillez la 1ere ligne pour creer une rupture de pattern."


if __name__ == "__main__":
    engine = FoqEngine()

    test_tweets = [
        (
            "Hook Contre-Intuitif (Tech / Business)",
            "J'ai passe 10 ans a coder 60h/semaine. C'etait la pire erreur de ma vie.\n\nVoici les 4 regles de travail asynchrone qui ont triple mes revenus en travaillant 4h par jour :"
        ),
        (
            "Annonce corporate sans angle",
            "Nous sommes ravis de vous annoncer la sortie de notre version 2.4 de notre logiciel comptable. N'hesitez pas a telecharger la mise a jour sur notre site."
        ),
        (
            "Controverse / Débat d'opinion",
            "Opinion impopulaire : Le teletravail a 100% detruit la culture des juniors dans les entreprises de moins de 20 personnes. Vous en pensez quoi ?"
        ),
        (
            "Clickbait artificiel",
            "Ce secret va changer votre vie a tout jamais... 99% des gens l'ignorent. Likez et commentez 'OUI' pour recevoir le PDF secret en DM."
        ),
    ]

    print("=" * 65)
    print("📊 ANALYSEUR & PREDICTEUR DE VIRALITE DE TWEETS (Foq Systeme 1)")
    print("=" * 65)

    for title, tweet in test_tweets:
        print(f"\n[Test] {title}")
        print(f"Texte : \"{tweet}\"")
        analysis = score_tweet(tweet, engine)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("Verdict :", get_recommendation(analysis))
