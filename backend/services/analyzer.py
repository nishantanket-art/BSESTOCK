"""
services/analyzer.py
Enhanced rule-based analysis engine (migrated from analyzer.py).
Serves as fallback when OpenAI API is not available.
"""

from datetime import datetime
from backend.utils.helpers import get_logger

logger = get_logger("analyzer")

REASON_TEMPLATES = {
    "large_selloff": {
        "reasons": [
            "Debt Servicing / Pledge Liquidation — Promoters with pledged shares face forced selling when stock prices decline.",
            "Personal Wealth Diversification — Large sell-off may indicate promoters redistributing wealth.",
            "Business Restructuring / Capital Raise — Company may be preparing for large capex or acquisition.",
        ],
        "mode_of_selling": "Likely Bulk Deal / OFS",
        "sentiment": "Bearish",
        "sentiment_color": "#ff4d4d",
    },
    "medium_selloff": {
        "reasons": [
            "Strategic Stake Dilution for SEBI Compliance — SEBI mandates minimum public float.",
            "Partial Profit Booking — After sustained appreciation, promoters may book partial profits.",
            "Promoter Entity Restructuring — Intra-group transfers may show as selling.",
        ],
        "mode_of_selling": "Open Market / Block Deal",
        "sentiment": "Cautious",
        "sentiment_color": "#ffa500",
    },
    "small_selloff": {
        "reasons": [
            "SEBI Minimum Public Float Compliance — Routine mandatory dilution.",
            "ESOP/Stock Option Exercises — Employee equity plan fulfillment.",
            "Reclassification of Promoter Entities — Some promoter group members reclassified.",
        ],
        "mode_of_selling": "Administrative / Reclassification",
        "sentiment": "Neutral",
        "sentiment_color": "#00cc88",
    },
}

VERDICT_MAP = {
    "exit":    {"label": "Exit",    "color": "#ff4d4d", "icon": "🔴", "desc": "High risk — consider exiting position"},
    "caution": {"label": "Caution", "color": "#ff8c00", "icon": "🟠", "desc": "Exercise caution — monitor closely"},
    "hold":    {"label": "Hold",    "color": "#ffc107", "icon": "🟡", "desc": "Hold position — no immediate action needed"},
    "buy":     {"label": "Buy",     "color": "#00cc88", "icon": "🟢", "desc": "Fundamentally sound — dip may be opportunity"},
}


def categorize_selloff(change_abs: float) -> str:
    if change_abs >= 3.0:
        return "large_selloff"
    elif change_abs >= 1.0:
        return "medium_selloff"
    return "small_selloff"


def compute_verdict(promoter_current: float, change_abs: float, category: str) -> dict:
    if category == "large_selloff":
        if promoter_current < 45:
            return VERDICT_MAP["exit"]
        elif promoter_current < 55:
            return VERDICT_MAP["caution"]
        return VERDICT_MAP["hold"]
    elif category == "medium_selloff":
        if promoter_current > 60:
            return VERDICT_MAP["buy"]
        elif promoter_current > 50:
            return VERDICT_MAP["hold"]
        return VERDICT_MAP["caution"]
    else:
        if promoter_current > 55:
            return VERDICT_MAP["buy"]
        return VERDICT_MAP["hold"]


def compute_risk_level(promoter_current: float, change_abs: float) -> dict:
    score = 0
    if change_abs >= 3.0:
        score += 3
    elif change_abs >= 1.5:
        score += 2
    else:
        score += 1
    if promoter_current > 60:
        score -= 1
    elif promoter_current < 45:
        score += 1
    if score >= 4:
        return {"level": "High", "color": "#ff4d4d", "icon": "🔴"}
    elif score >= 2:
        return {"level": "Medium", "color": "#ffa500", "icon": "🟡"}
    return {"level": "Low", "color": "#00cc88", "icon": "🟢"}


def analyze_promoter_intent(promoter_current: float, change_abs: float, all_holdings: list) -> dict:
    is_trend = False
    if len(all_holdings) >= 3:
        recent = all_holdings[-3:]
        is_trend = all(recent[i] > recent[i + 1] for i in range(len(recent) - 1))

    if change_abs >= 3.0:
        confidence, pattern = "Low", "Aggressive selling — possible forced liquidation"
    elif change_abs >= 1.0:
        confidence, pattern = "Medium", "Moderate reduction — could be strategic or compliance-driven"
    else:
        confidence, pattern = "High", "Minor adjustment — promoter remains highly invested"

    return {
        "confidence": confidence,
        "is_trend": is_trend,
        "trend_label": "Repeated selling (multi-quarter trend)" if is_trend else "One-time event",
        "pattern": pattern,
    }


def analyze_impact(promoter_current: float, change_abs: float, category: str) -> dict:
    if category == "large_selloff":
        return {
            "governance": "Negative",
            "market_perception": "Market likely to react negatively",
            "short_term": "Expect selling pressure in 1–4 weeks",
            "long_term": "Could signal fundamental business concerns",
        }
    elif category == "medium_selloff":
        return {
            "governance": "Neutral",
            "market_perception": "Market may view cautiously",
            "short_term": "Moderate near-term pressure",
            "long_term": "Likely neutral if promoter holds >50%",
        }
    return {
        "governance": "Positive",
        "market_perception": "Market typically ignores minor adjustments",
        "short_term": "Minimal short-term impact",
        "long_term": "Long-term positive with >40% stake retained",
    }


def get_recommendation(verdict_label: str) -> str:
    recs = {
        "Exit": "Consider reducing or exiting your position. Set a stop-loss if you choose to hold.",
        "Caution": "Don't add to your position. Wait for clarity on promoter selling. Monitor next quarter.",
        "Hold": "No immediate action needed. Continue monitoring quarterly filings.",
        "Buy": "Selling appears routine. Fundamentals intact. A dip could be a buying opportunity.",
    }
    return recs.get(verdict_label, recs["Hold"])


def analyze_company(company_data: dict) -> dict:
    """Run full rule-based analysis on a company."""
    change_abs = company_data.get("promoter_change_abs", 0)
    promoter_current = company_data.get("promoter_current", 0)
    all_holdings = company_data.get("all_holdings", [])

    category = categorize_selloff(change_abs)
    template = REASON_TEMPLATES[category]
    risk = compute_risk_level(promoter_current, change_abs)
    verdict = compute_verdict(promoter_current, change_abs, category)
    intent = analyze_promoter_intent(promoter_current, change_abs, all_holdings)
    impact = analyze_impact(promoter_current, change_abs, category)
    recommendation = get_recommendation(verdict["label"])

    # Generate a descriptive summary for the UI
    summary = f"The promoter holding has {('reduced' if change_abs > 0 else 'remained stable')}. "
    summary += f"Current stake is {promoter_current}%. "
    if change_abs >= 1.0:
        summary += f"This is a {risk['level'].lower()} risk event involving a {change_abs}% stake reduction. "
        summary += f"Likely reasons include {', '.join(template['reasons'][:2]).lower()}. "
    else:
        summary += "The activity appears to be routine or administrative in nature with negligible impact on long-term ownership structure."

    return {
        "category": category,
        "summary": summary,
        "reasons": template["reasons"],
        "mode_of_selling": template["mode_of_selling"],
        "sentiment": template["sentiment"],
        "sentiment_color": template["sentiment_color"],
        "verdict": verdict["label"],
        "verdict_color": verdict["color"],
        "verdict_icon": verdict["icon"],
        "verdict_desc": verdict["desc"],
        "risk_level": risk["level"],
        "risk_color": risk["color"],
        "risk_icon": risk["icon"],
        "risk_score": 100 if risk["level"] == "High" else 60 if risk["level"] == "Medium" else 30,
        "intent_confidence": intent["confidence"],
        "intent_is_trend": intent["is_trend"],
        "intent_trend_label": intent["trend_label"],
        "intent_pattern": intent["pattern"],
        "impact_governance": impact["governance"],
        "impact_perception": impact["market_perception"],
        "impact_short_term": impact["short_term"],
        "impact_long_term": impact["long_term"],
        "recommendation": recommendation,
        "analyzed_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }


def analyze_all(companies: list[dict]) -> list[dict]:
    """Analyze a list of companies and attach analysis to each."""
    results = []
    for c in companies:
        analysis = analyze_company(c)
        results.append({**c, "analysis": analysis})
    return results


def generate_insights(results: list[dict]) -> list[dict]:
    """Generate aggregated insights across all results."""
    if not results:
        return []

    insights = []
    high_risk = [r for r in results if r.get("analysis", {}).get("risk_level") == "High"]
    trends = [r for r in results if r.get("analysis", {}).get("intent_is_trend")]
    exits = [r for r in results if r.get("analysis", {}).get("verdict") == "Exit"]
    large = [r for r in results if r.get("analysis", {}).get("category") == "large_selloff"]
    buys = [r for r in results if r.get("analysis", {}).get("verdict") == "Buy"]

    if high_risk:
        names = ", ".join([r["ticker"] for r in high_risk[:5]])
        insights.append({
            "icon": "🔴", "title": f"{len(high_risk)} High-Risk Alert{'s' if len(high_risk) != 1 else ''}",
            "description": f"Companies with significant promoter exits: {names}", "severity": "high",
        })
    if trends:
        names = ", ".join([r["ticker"] for r in trends[:5]])
        insights.append({
            "icon": "📉", "title": "Repeated Selling Pattern Detected",
            "description": f"Multi-quarter promoter reduction trend in: {names}", "severity": "high",
        })
    if exits:
        insights.append({
            "icon": "🚪", "title": f"{len(exits)} Exit Signal{'s' if len(exits) != 1 else ''}",
            "description": "AI recommends exit for these companies due to aggressive promoter selling", "severity": "high",
        })
    if large:
        avg_drop = sum(r["promoter_change_abs"] for r in large) / len(large)
        insights.append({
            "icon": "⚠️", "title": f"Large Sell-offs Averaging {avg_drop:.1f}% Drop",
            "description": f"{len(large)} companies show >3% promoter reduction", "severity": "medium",
        })
    if buys:
        names = ", ".join([r["ticker"] for r in buys[:5]])
        insights.append({
            "icon": "🟢", "title": f"{len(buys)} Potential Opportunities",
            "description": f"Routine selling with strong fundamentals: {names}", "severity": "low",
        })

    total = len(results)
    avg_holding = sum(r["promoter_current"] for r in results) / total if total else 0
    insights.append({
        "icon": "📊", "title": f"{total} Companies Tracked · Avg Holding {avg_holding:.1f}%",
        "description": "Across the universe of NSE/BSE stocks scanned for promoter activity", "severity": "info",
    })

    return insights
