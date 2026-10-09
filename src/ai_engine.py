"""Automated AI Insights and Summary Engine for Retail Executive Intelligence.
Orchestrates structured payload generation, prompt engineering for generative models (GPT-4o, Claude 3.5 Sonnet, Gemini),
and provides a deterministic hyper-local heuristic engine fallback.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any
import requests


SYSTEM_PROMPT = """You are an elite Senior Retail Strategy Consultant and Lead Data Scientist specializing in Business Intelligence.
You analyze transactional retail performance metrics and output razor-sharp, highly specific executive intelligence.

STRICT CONSTRAINTS:
1. Output format must be pure JSON with exactly two array fields:
   {
     "trends": [
       "Trend bullet 1",
       "Trend bullet 2",
       "Trend bullet 3"
     ],
     "recommendations": [
       "Recommendation 1",
       "Recommendation 2",
       "Recommendation 3"
     ]
   }
2. The "trends" array must contain EXACTLY 3 bullet points summarizing performance trends, directly referencing the data payload (revenue, AOV, seasonality, top SKUs, regional yield).
3. The "recommendations" array must contain EXACTLY 3 highly specific, hyper-local business recommendations.
4. ABSOLUTELY FORBIDDEN: Generic platitudes like "increase marketing", "boost sales", or "focus on customers".
5. REQUIRED: Every recommendation must cite exact SKU names, regions, percentages, or tactical operational actions (e.g., "Divert 15% of SKU-LAPTOP-PRO16 inventory to the North America fulfillment hub 3 weeks prior to projected demand surges to prevent stock-outs").
"""


class AIInsightsEngine:
    """Orchestrator for LLM generation and deterministic local synthesis."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.model = model

    def generate_executive_insights(self, payload: dict[str, Any]) -> dict[str, list[str]]:
        """Generate 3 performance trend bullets and 3 hyper-local business recommendations.

        Attempts LLM API call if key is present; gracefully falls back to deterministic local heuristic engine.
        """
        # Validate payload structure
        validated_payload = self._validate_payload(payload)

        # Attempt live API if key is available
        if self.api_key and len(self.api_key.strip()) > 10:
            try:
                llm_result = self._call_llm_api(validated_payload)
                if llm_result and len(llm_result.get("trends", [])) == 3 and len(llm_result.get("recommendations", [])) == 3:
                    return llm_result
            except Exception as e:
                print(f"[AI Engine] Live API call failed, falling back to local heuristic synthesis: {e}")

        # Deterministic Hyper-Local Fallback
        return self._generate_heuristic_insights(validated_payload)

    def _validate_payload(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        """Ensure payload matches exact Module C schema."""
        return {
            "total_revenue": str(raw_payload.get("total_revenue", "$0.00")),
            "aov": str(raw_payload.get("aov", "$0.00")),
            "top_performing_region": str(raw_payload.get("top_performing_region", "National (100% of sales)")),
            "seasonality_delta": str(raw_payload.get("seasonality_delta", "Stable MoM cadence")),
            "top_3_skus_by_revenue": list(raw_payload.get("top_3_skus_by_revenue", ["SKU-A", "SKU-B", "SKU-C"]))[:3],
            "underperforming_segments": list(raw_payload.get("underperforming_segments", ["Standard"]))[:2],
        }

    def _call_llm_api(self, payload: dict[str, Any]) -> dict[str, list[str]] | None:
        """Call LLM API (OpenAI compatible endpoint)."""
        prompt = (
            f"Analyze the following retail executive dataset payload and return the strict JSON schema:\n"
            f"{json.dumps(payload, indent=2)}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.25,
            "response_format": {"type": "json_object"},
        }

        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "trends": parsed.get("trends", [])[:3],
                "recommendations": parsed.get("recommendations", [])[:3],
            }
        return None

    def _generate_heuristic_insights(self, payload: dict[str, Any]) -> dict[str, list[str]]:
        """Deterministic hyper-local heuristic engine synthesizing exact 3 trends and 3 hyper-local recommendations."""
        top_sku = payload["top_3_skus_by_revenue"][0] if payload["top_3_skus_by_revenue"] else "Anchor Hardware"
        sec_sku = payload["top_3_skus_by_revenue"][1] if len(payload["top_3_skus_by_revenue"]) > 1 else "Attached Accessories"
        top_reg = payload["top_performing_region"].split(" (")[0]
        under_seg = payload["underperforming_segments"][0] if payload["underperforming_segments"] else "Tail inventory"

        # Exactly 3 performance trends
        trends = [
            f"Consolidated top-line yield reached {payload['total_revenue']} across the period, maintaining a disciplined Average Order Value (AOV) of {payload['aov']}.",
            f"Regional revenue concentration is heavily driven by {payload['top_performing_region']}, representing the primary volume engine of the sales footprint.",
            f"Seasonal transaction velocity indicates {payload['seasonality_delta']}, heavily catalyzed by peak conversion in anchor SKU '{top_sku}'.",
        ]

        # Exactly 3 hyper-local specific business recommendations
        recommendations = [
            f"Reallocate 15% of regional safety stock for '{top_sku}' directly to {top_reg} fulfillment hubs 3 weeks prior to projected demand cycles to avoid margin-eroding stockouts.",
            f"Architect a cross-sell bundling incentive attaching high-margin accessories to '{sec_sku}', targeting a 12% lift in basket size to advance current AOV beyond {payload['aov']}.",
            f"Restructure promotional markdown allocations within {under_seg}, sunsetting slow-turn SKUs and transitioning capital into top-performing regional channels.",
        ]

        return {
            "trends": trends,
            "recommendations": recommendations,
        }
