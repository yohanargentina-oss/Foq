import json
import sys
from foq import FoqEngine, Choice, Boolean, Score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def score_tweet(tweet_text: str, engine: FoqEngine) -> dict:
    """Analyze a tweet or post hook in a single System 1 pass (25 ms)."""
    questions = {
        "viral_trigger": Choice(
            "What is the primary psychological hook used in this post?",
            choices={
                "curiosity_gap": "Curiosity gap / Unresolved mystery",
                "contrarian": "Contrarian take / Myth busting / Hot take",
                "high_value_framework": "Actionable framework / Practical playbook",
                "vulnerable_story": "Personal storytelling / Overcoming failure",
                "boring_announcement": "Generic update / Self-promotion without hook",
            },
        ),
        "virality_score": Score(
            "Repost potential and algorithmic reach",
            levels={
                "1": "Low (Under 10 reposts - Generic / Flat)",
                "2": "Moderate (Standard organic reach)",
                "3": "Good (Strong engagement from existing followers)",
                "4": "High (Out-of-network breakout potential)",
                "5": "Viral breakout (Exceptional hook / Broad debate)",
            },
        ),
        "comment_bait": Boolean(
            "Does the post naturally prompt replies or debate in comments?"
        ),
        "is_cheap_clickbait": Boolean(
            "Does the post use low-effort engagement bait or empty sensationalism?"
        ),
    }

    result = engine.system_one(
        state=f"Draft Tweet / Post:\n\"{tweet_text.strip()}\"",
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
    """Generate diagnostic feedback and actionable advice."""
    if analysis["cheap_clickbait"]:
        return "⚠️ Low-effort clickbait: add concrete substance to protect audience trust."

    score = int(analysis["score"])
    if score >= 4:
        return "🔥 Excellent hook: strong viral breakout potential."
    elif score == 3:
        return "👍 Solid post for your existing core audience."
    else:
        return "💤 Needs a sharper angle: rework the opening line to break pattern."


if __name__ == "__main__":
    engine = FoqEngine()

    test_tweets = [
        (
            "Contrarian Work Philosophy",
            "I spent 10 years coding 60h/week. It was the biggest mistake of my career.\n\nHere are 4 async leverage rules that tripled my income on 4h of deep work a day:"
        ),
        (
            "Generic Corporate Announcement",
            "We are thrilled to announce version 2.4 of our accounting software. Download the new release on our website."
        ),
        (
            "Spicy Discussion Prompt",
            "Unpopular opinion: Full remote work destroys junior mentorship in teams under 20 people. Change my mind."
        ),
        (
            "Low-Effort Engagement Bait",
            "This secret will change your life forever... 99% of people have no clue. Like and comment 'YES' for the secret PDF in DM."
        ),
    ]

    print("=" * 65)
    print("📊 TWEET VIRALITY PREDICTOR & ANALYZER (Foq System 1)")
    print("=" * 65)

    for title, tweet in test_tweets:
        print(f"\n[Test] {title}")
        print(f"Text: \"{tweet}\"")
        analysis = score_tweet(tweet, engine)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("Verdict:", get_recommendation(analysis))
