"""
analyzer.py
Enhanced rule-based AI analysis engine for promoter stake selling.
Provides: AI Verdict, Promoter Intent, Impact Analysis, Risk Score,
Investor Recommendation — all without external API keys.
"""

from datetime import datetime


# ── Reason templates by sell-off magnitude
REASON_TEMPLATES = {
    "large_selloff": {  # > 3% drop
        "reasons": [
            "Debt Servicing / Pledge Liquidation — Promoters with pledged shares face forced selling when stock prices decline, triggering margin calls.",
            "Personal Wealth Diversification — Large sell-off may indicate promoters redistributing wealth into real estate, private equity, or foreign assets.",
            "Business Restructuring / Capital Raise — Company may be preparing for large capex, acquisition, or rights issue; selling to make room for institutional investors.",
        ],
        "mode_of_selling": "Likely Bulk Deal / OFS",
        "sentiment": "Bearish",
        "sentiment_color": "#ff4d4d",
    },
    "medium_selloff": {  # 1–3% drop
        "reasons": [
            "Strategic Stake Dilution for SEBI Compliance — SEBI mandates minimum public float; promoters holding >75% are required to sell.",
            "Partial Profit Booking — After sustained price appreciation, promoters may book partial profits while retaining majority control.",
            "Promoter Entity Restructuring — Intra-group transfers between promoter entities may show as selling in one entity's data.",
        ],
        "mode_of_selling": "Open Market / Block Deal",
        "sentiment": "Cautious",
        "sentiment_color": "#ffa500",
    },
    "small_selloff": {  # < 1% drop
        "reasons": [
            "SEBI Minimum Public Float Compliance — Routine mandatory dilution to comply with 25% minimum public shareholding norm.",
            "ESOP/Stock Option Exercises — Employee equity plan fulfillment may reduce promoter's classified holding percentage.",
            "Reclassification of Promoter Entities — Some promoter group members reclassified as non-promoter public shareholders per SEBI guidelines.",
        ],
        "mode_of_selling": "Administrative / Reclassification",
        "sentiment": "Neutral",
        "sentiment_color": "#00cc88",
    },
}

# ── AI Verdict logic
VERDICT_MAP = {
    "exit":    {"label": "Exit",    "color": "#ff4d4d", "icon": "🔴", "desc": "High risk — consider exiting position"},
    "caution": {"label": "Caution", "color": "#ff8c00", "icon": "🟠", "desc": "Exercise caution — monitor closely"},
    "hold":    {"label": "Hold",    "color": "#ffc107", "icon": "🟡", "desc": "Hold position — no immediate action needed"},
    "buy":     {"label": "Buy",     "color": "#00cc88", "icon": "🟢", "desc": "Fundamentally sound — dip may be opportunity"},
}


def _categorize_selloff(change_abs: float) -> str:
    if change_abs >= 3.0:
        return "large_selloff"
    elif change_abs >= 1.0:
        return "medium_selloff"
    else:
        return "small_selloff"


def _compute_verdict(promoter_current: float, change_abs: float, category: str) -> dict:
    """Determine AI Verdict: Buy / Hold / Caution / Exit."""
    if category == "large_selloff":
        if promoter_current < 45:
            return VERDICT_MAP["exit"]
        elif promoter_current < 55:
            return VERDICT_MAP["caution"]
        else:
            return VERDICT_MAP["hold"]
    elif category == "medium_selloff":
        if promoter_current > 60:
            return VERDICT_MAP["buy"]
        elif promoter_current > 50:
            return VERDICT_MAP["hold"]
        else:
            return VERDICT_MAP["caution"]
    else:  # small_selloff
        if promoter_current > 55:
            return VERDICT_MAP["buy"]
        else:
            return VERDICT_MAP["hold"]


def _compute_risk(promoter_current: float, change_abs: float) -> dict:
    """Calculate risk level based on holding % and sell-off size."""
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
    else:
        return {"level": "Low", "color": "#00cc88", "icon": "🟢"}


def _promoter_intent(promoter_current: float, change_abs: float, all_holdings: list) -> dict:
    """Analyze promoter intent and confidence level."""
    # Check if this is a trend (multiple consecutive declines)
    is_trend = False
    if len(all_holdings) >= 3:
        recent = all_holdings[-3:]
        is_trend = all(recent[i] > recent[i+1] for i in range(len(recent)-1))

    if change_abs >= 3.0:
        confidence = "Low"
        pattern = "Aggressive selling — possible loss of confidence or forced liquidation"
    elif change_abs >= 1.0:
        confidence = "Medium"
        pattern = "Moderate reduction — could be strategic or compliance-driven"
    else:
        confidence = "High"
        pattern = "Minor adjustment — promoter remains highly invested"

    return {
        "confidence": confidence,
        "is_trend": is_trend,
        "trend_label": "Repeated selling (multi-quarter trend)" if is_trend else "Appears to be one-time event",
        "pattern": pattern,
    }


def _impact_analysis(promoter_current: float, change_abs: float, category: str) -> dict:
    """Assess governance signal, market perception, and time-horizon impact."""
    if category == "large_selloff":
        governance = "Negative"
        perception = "Market likely to react negatively; institutional investors may reassess"
        short_term = "Expect selling pressure and potential price correction in 1–4 weeks"
        long_term = "If selling continues, could signal fundamental business concerns over 12–24 months"
    elif category == "medium_selloff":
        governance = "Neutral"
        perception = "Market may view cautiously; depends on stated reason for sale"
        short_term = "Moderate near-term pressure; monitor quarterly earnings for confirmation"
        long_term = "Likely neutral if promoter still holds >50% — business fundamentals drive long-term"
    else:
        governance = "Positive"
        perception = "Market typically ignores minor promoter adjustments"
        short_term = "Minimal short-term impact; often regulatory or administrative"
        long_term = "Long-term positive — high promoter confidence with >40% stake retained"

    return {
        "governance": governance,
        "market_perception": perception,
        "short_term": short_term,
        "long_term": long_term,
    }


def _investor_recommendation(verdict: dict, risk: dict, intent: dict) -> str:
    """Generate plain-language investor recommendation."""
    v = verdict["label"]
    if v == "Exit":
        return "Consider reducing or exiting your position. The promoter is selling aggressively, which often precedes further downside. Set a stop-loss if you choose to hold."
    elif v == "Caution":
        return "Don't add to your position right now. Wait for clarity on why the promoter is selling. Monitor next quarter's shareholding pattern before making a decision."
    elif v == "Hold":
        return "No immediate action needed. The selling is moderate and the promoter still retains a strong stake. Continue monitoring quarterly filings."
    else:  # Buy
        return "The selling appears routine/regulatory. The company's fundamentals remain intact with strong promoter confidence. A price dip could be a buying opportunity for long-term investors."


def analyze_company(company_data: dict) -> dict:
    """
    Run comprehensive rule-based analysis on a company with promoter selling.
    """
    change_abs = company_data.get("promoter_change_abs", 0)
    promoter_current = company_data.get("promoter_current", 0)
    promoter_prev = company_data.get("promoter_prev", promoter_current)
    change = company_data.get("promoter_change", 0)
    all_holdings = company_data.get("all_holdings", [])

    category = _categorize_selloff(change_abs)
    template = REASON_TEMPLATES[category]
    risk = _compute_risk(promoter_current, change_abs)
    verdict = _compute_verdict(promoter_current, change_abs, category)
    intent = _promoter_intent(promoter_current, change_abs, all_holdings)
    impact = _impact_analysis(promoter_current, change_abs, category)
    recommendation = _investor_recommendation(verdict, risk, intent)

    analysis = {
        **company_data,
        "analysis": {
            "category": category,
            "reasons": template["reasons"],
            "mode_of_selling": template["mode_of_selling"],
            "sentiment": template["sentiment"],
            "sentiment_color": template["sentiment_color"],
            # AI Verdict
            "verdict": verdict["label"],
            "verdict_color": verdict["color"],
            "verdict_icon": verdict["icon"],
            "verdict_desc": verdict["desc"],
            # Risk
            "risk_level": risk["level"],
            "risk_color": risk["color"],
            "risk_icon": risk["icon"],
            # Promoter Intent
            "intent_confidence": intent["confidence"],
            "intent_is_trend": intent["is_trend"],
            "intent_trend_label": intent["trend_label"],
            "intent_pattern": intent["pattern"],
            # Impact
            "impact_governance": impact["governance"],
            "impact_perception": impact["market_perception"],
            "impact_short_term": impact["short_term"],
            "impact_long_term": impact["long_term"],
            # Recommendation
            "recommendation": recommendation,
            # Meta
            "analyzed_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        },
    }
    return analysis


def analyze_all(companies: list[dict]) -> list[dict]:
    """Analyze a list of companies with promoter selling."""
    return [analyze_company(c) for c in companies]


def generate_ai_insights(results: list[dict]) -> list[dict]:
    """Generate aggregated AI insights across all results."""
    if not results:
        return []

    insights = []
    high_risk = [r for r in results if r.get("analysis", {}).get("risk_level") == "High"]
    trends = [r for r in results if r.get("analysis", {}).get("intent_is_trend")]
    exits = [r for r in results if r.get("analysis", {}).get("verdict") == "Exit"]
    large = [r for r in results if r.get("analysis", {}).get("category") == "large_selloff"]

    if high_risk:
        names = ", ".join([r["ticker"] for r in high_risk[:5]])
        insights.append({
            "icon": "🔴",
            "title": f"{len(high_risk)} High-Risk Alert{'s' if len(high_risk) != 1 else ''}",
            "description": f"Companies with significant promoter exits: {names}",
            "severity": "high",
        })

    if trends:
        names = ", ".join([r["ticker"] for r in trends[:5]])
        insights.append({
            "icon": "📉",
            "title": "Repeated Selling Pattern Detected",
            "description": f"Multi-quarter promoter reduction trend in: {names}",
            "severity": "high",
        })

    if exits:
        insights.append({
            "icon": "🚪",
            "title": f"{len(exits)} Exit Signal{'s' if len(exits) != 1 else ''}",
            "description": "AI recommends considering exit for these companies due to aggressive promoter selling",
            "severity": "high",
        })

    if large:
        avg_drop = sum(r["promoter_change_abs"] for r in large) / len(large)
        insights.append({
            "icon": "⚠️",
            "title": f"Large Sell-offs Averaging {avg_drop:.1f}% Drop",
            "description": f"{len(large)} companies show >3% promoter reduction — warrants investigation",
            "severity": "medium",
        })

    buys = [r for r in results if r.get("analysis", {}).get("verdict") == "Buy"]
    if buys:
        names = ", ".join([r["ticker"] for r in buys[:5]])
        insights.append({
            "icon": "🟢",
            "title": f"{len(buys)} Potential Opportunities",
            "description": f"Routine/regulatory selling with strong fundamentals: {names}",
            "severity": "low",
        })

    total = len(results)
    avg_holding = sum(r["promoter_current"] for r in results) / total if total else 0
    insights.append({
        "icon": "📊",
        "title": f"{total} Companies Tracked · Avg Holding {avg_holding:.1f}%",
        "description": "Across the universe of 87 NSE/BSE stocks scanned for promoter activity",
        "severity": "info",
    })

    return insights
