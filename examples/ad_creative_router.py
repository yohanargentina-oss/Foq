import sys
import json
from foq import FoqEngine, Choice, Boolean, Score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def analyze_ad_creative(creative_text: str, engine: FoqEngine) -> dict:
    """Analyze an ad creative / copy in a single System 1 pass."""
    questions = {
        "funnel_stage": Choice(
            "Customer funnel stage target",
            choices={
                "top": "Top of Funnel (Brand awareness / Problem discovery)",
                "middle": "Middle of Funnel (Comparison / Product demo / Solution)",
                "bottom": "Bottom of Funnel (Direct offer / Conversion / Discount)",
                "retention": "Post-Purchase (Retention / Reviews / Upsell)",
            },
        ),
        "hook_style": Choice(
            "Creative hook angle used",
            choices={
                "ugc_testimonial": "Customer testimonial / UGC review",
                "pain_point": "Frustration / Problem agitation",
                "behind_the_scenes": "Behind the scenes / Craftsmanship",
                "product_demo": "Product feature demo",
                "discount_offer": "Discount code / Promotional urgency",
            },
        ),
        "has_clear_cta": Boolean("Does the content include a clear call to action (CTA)?"),
        "risk_claims": Boolean("Are there misleading or unverified medical/compliance claims?"),
        "virality_potential": Score(
            "Engagement and virality potential",
            levels={"1": "Low / Generic", "2": "Moderate", "3": "High / Viral"}
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
    """Route content to the appropriate campaign channel based on analysis."""
    if analysis["risk_claims"]["value"] is True or "risk_claims" in analysis["needs_human_review"]:
        return "🚨 Manual moderation queue (Compliance / Misleading claim risk)"

    stage = analysis["funnel_stage"]["value"]
    style = analysis["hook_style"]["value"]

    if stage == "bottom" or analysis["has_clear_cta"]["value"]:
        return "🎯 Direct conversion campaign (BOFU Retargeting)"
    elif stage == "top" and style in ("ugc_testimonial", "pain_point"):
        return "📱 TikTok / Reels Cold Audience acquisition (TOFU)"
    else:
        return "📊 Nurturing / Middle of Funnel campaign"


if __name__ == "__main__":
    engine = FoqEngine()

    test_samples = [
        (
            "Ergonomic Pillow UGC",
            "I tried 10 different ergonomic pillows for morning neck pain. "
            "This one completely eliminated my stiffness in 3 nights. "
            "Click the link in bio for 20% off with code NECK20!"
        ),
        (
            "Desk Manufacturing Behind The Scenes",
            "Did you know that 80% of standing desks fail within 6 months? "
            "Here is how we engineer dual-motor columns in our workshop."
        ),
        (
            "Misleading Medical Claim",
            "This herbal tea permanently cures 100% of severe insomnia and replaces all prescription medication!"
        ),
        (
            "Compliant TOFU Educational Hook",
            "Sitting 8 hours a day hunched over your laptop? Here are 3 simple desk stretches you can do right now."
        ),
    ]

    for title, sample in test_samples:
        print(f"\n==================================================")
        print(f"[TEST] {title}")
        print(f"Text: \"{sample.strip()}\"")
        analysis = analyze_ad_creative(sample, engine)
        print("\nFoq System 1 analysis:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("\nAutomated routing:", route_creative(analysis))
