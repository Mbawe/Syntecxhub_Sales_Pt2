"""Automated unit test suite for Module C: AI Insights and Summary Engine.
Verifies JSON payload format compliance, strict 3+3 output constraints, and hyper-local specific recommendations.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine import AIInsightsEngine

def test_ai_engine():
    print("=== STARTING AI INSIGHTS ENGINE VERIFICATION ===")

    test_payload = {
        "total_revenue": "$3,464,381.52",
        "aov": "$974.78",
        "top_performing_region": "North America (36.6% of total sales)",
        "seasonality_delta": "9.7% MoM growth during peak month (Jul 2024)",
        "top_3_skus_by_revenue": ["SKU-LAPTOP-PRO16", "SKU-PHONE-ULTRA", "SKU-STAND-DESK-PRO"],
        "underperforming_segments": ["Software & Services Category (9.4% total share)", "Middle East Region (5.8% share)"]
    }

    engine = AIInsightsEngine(api_key=None)  # Tests deterministic local synthesis
    result = engine.generate_executive_insights(test_payload)

    assert "trends" in result, "Missing 'trends' in result"
    assert "recommendations" in result, "Missing 'recommendations' in result"

    trends = result["trends"]
    recs = result["recommendations"]

    # Constraint 1: Exactly 3 trends
    assert len(trends) == 3, f"Expected exactly 3 trends, got {len(trends)}"
    print(f"[PASS] Successfully generated exactly 3 performance trends:")
    for idx, t in enumerate(trends, 1):
        print(f"  {idx}. {t}")

    # Constraint 2: Exactly 3 recommendations
    assert len(recs) == 3, f"Expected exactly 3 recommendations, got {len(recs)}"
    print(f"\n[PASS] Successfully generated exactly 3 hyper-local business recommendations:")
    for idx, r in enumerate(recs, 1):
        print(f"  {idx}. {r}")

    # Constraint 3: Verify specificity and lack of generic platitudes
    for r in recs:
        assert not any(platitude in r.lower() for platitude in ["increase sales", "boost sales", "focus on customers", "improve marketing"]), \
            f"Detected prohibited generic platitude in recommendation: {r}"

    assert any("SKU-LAPTOP-PRO16" in r for r in recs), "Failed to cite top SKU in recommendations"
    assert any("North America" in r for r in recs), "Failed to cite top Region in recommendations"
    print("\n[PASS] Specificity verified: exact SKUs and regions cited, zero generic platitudes.")
    print(">>> MODULE C AI ENGINE TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_ai_engine()
