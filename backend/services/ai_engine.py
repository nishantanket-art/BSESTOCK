"""
services/ai_engine.py
OpenAI-powered AI analysis engine.
Falls back to rule-based analysis when API key is not configured.
"""

import json
import asyncio
from openai import AsyncOpenAI
from backend.config import settings
from backend.services.analyzer import analyze_company as rule_based_analyze
from backend.utils.helpers import get_logger

logger = get_logger("ai_engine")

_client = None


def _get_client():
    global _client
    if _client is None and settings.OPENAI_API_KEY:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """You are an expert financial analyst specializing in Indian stock markets and promoter shareholding patterns. 
You analyze promoter selling behavior and provide structured, actionable insights.

When given company data with promoter holding changes, you must return a JSON object with these exact keys:
{
    "reason_for_selling": "1-2 sentence explanation of most likely reason",
    "future_outlook": "1-2 sentence outlook for the stock",
    "risk_explanation": "1-2 sentence risk assessment",
    "verdict": "Buy" or "Hold" or "Caution" or "Exit",
    "confidence": "High" or "Medium" or "Low",
    "key_factors": ["factor1", "factor2", "factor3"]
}

Consider: promoter holding level, magnitude of change, pattern (one-time vs trend), SEBI compliance requirements, 
market conditions, and typical promoter behavior in Indian markets."""


async def ai_analyze_company(company_data: dict) -> dict:
    """
    Analyze a company using OpenAI. Falls back to rule-based if:
    - No API key configured
    - API call fails
    """
    client = _get_client()
    if client is None:
        logger.info("No OpenAI API key — using rule-based analysis")
        return rule_based_analyze(company_data)

    # Build the prompt
    ticker = company_data.get("ticker", "UNKNOWN")
    user_prompt = f"""Analyze this Indian stock's promoter selling activity:

Company: {company_data.get('company_name', ticker)} ({ticker})
Market Cap: {company_data.get('market_cap', 'N/A')}
Current Promoter Holding: {company_data.get('promoter_current', 0)}%
Previous Quarter Holding: {company_data.get('promoter_prev', 0)}%
Change: {company_data.get('promoter_change', 0)}%
Historical Holdings: {company_data.get('all_holdings', [])}
Quarters: {company_data.get('quarters', [])}

Provide your analysis as JSON only, no other text."""

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        ai_result = json.loads(response.choices[0].message.content)

        # Merge AI results with rule-based analysis (for structural fields)
        base = rule_based_analyze(company_data)
        
        # Construct summary from AI parts
        ai_reason = ai_result.get("reason_for_selling", "")
        ai_outlook = ai_result.get("future_outlook", "")
        ai_risk = ai_result.get("risk_explanation", "")
        
        base["summary"] = f"{ai_reason} {ai_outlook} {ai_risk}".strip()
        base["ai_reason"] = ai_reason
        base["ai_outlook"] = ai_outlook
        base["ai_explanation"] = ai_risk
        base["ai_key_factors"] = ai_result.get("key_factors", [])

        # Override verdict if AI provides one
        ai_verdict = ai_result.get("verdict", "")
        if ai_verdict in ("Buy", "Hold", "Caution", "Exit"):
            verdict_map = {
                "Exit":    {"color": "#ff4d4d", "icon": "🔴", "desc": "AI: High risk — consider exiting"},
                "Caution": {"color": "#ff8c00", "icon": "🟠", "desc": "AI: Exercise caution"},
                "Hold":    {"color": "#ffc107", "icon": "🟡", "desc": "AI: Hold position"},
                "Buy":     {"color": "#00cc88", "icon": "🟢", "desc": "AI: Fundamentally sound"},
            }
            v = verdict_map[ai_verdict]
            base["verdict"] = ai_verdict
            base["verdict_color"] = v["color"]
            base["verdict_icon"] = v["icon"]
            base["verdict_desc"] = v["desc"]

        base["analysis_source"] = "ai"
        logger.info(f"AI analysis complete for {ticker}: verdict={base['verdict']}")
        return base

    except Exception as e:
        logger.error(f"AI analysis failed for {ticker}: {e} — falling back to rule-based")
        result = rule_based_analyze(company_data)
        result["analysis_source"] = "rule_based"
        return result


async def ai_analyze_all(companies: list[dict]) -> list[dict]:
    """Analyze all companies in parallel (limit 5), using AI where possible."""
    sem = asyncio.Semaphore(5)

    async def sem_analyze(c):
        async with sem:
            return await ai_analyze_company(c)

    tasks = [sem_analyze(c) for c in companies]
    analyses = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = []
    for c, analysis in zip(companies, analyses):
        if isinstance(analysis, Exception):
            logger.error(f"Error analyzing {c.get('ticker')}: {analysis}")
            analysis = rule_based_analyze(c)
        results.append({**c, "analysis": analysis})
    return results
