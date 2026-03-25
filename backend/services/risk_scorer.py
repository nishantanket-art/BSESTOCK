"""
services/risk_scorer.py
Smart composite risk scoring system (0-100).
Combines: promoter change %, holding level, selling trend, price trend.
"""

from backend.utils.helpers import get_logger

logger = get_logger("risk_scorer")


def compute_risk_score(company_data: dict) -> int:
    """
    Compute a composite risk score from 0 (safest) to 100 (highest risk).

    Factors and weights:
    - Promoter change magnitude: 30%
    - Current holding level: 25%
    - Multi-quarter selling trend: 20%
    - Holding velocity (acceleration): 15%
    - Distance from critical threshold (50%): 10%
    """
    score = 0.0

    change_abs = company_data.get("promoter_change_abs", 0)
    promoter_current = company_data.get("promoter_current", 60)
    all_holdings = company_data.get("all_holdings", [])

    # ── Factor 1: Change magnitude (30 points max)
    if change_abs >= 5.0:
        score += 30
    elif change_abs >= 3.0:
        score += 24
    elif change_abs >= 2.0:
        score += 18
    elif change_abs >= 1.0:
        score += 12
    elif change_abs >= 0.5:
        score += 6
    else:
        score += 2

    # ── Factor 2: Current holding level (25 points max)
    # Lower holding = higher risk
    if promoter_current < 40:
        score += 25
    elif promoter_current < 45:
        score += 20
    elif promoter_current < 50:
        score += 15
    elif promoter_current < 55:
        score += 10
    elif promoter_current < 60:
        score += 5
    else:
        score += 2

    # ── Factor 3: Multi-quarter trend (20 points max)
    if len(all_holdings) >= 3:
        recent = all_holdings[-3:]
        consecutive_declines = sum(
            1 for i in range(len(recent) - 1) if recent[i] > recent[i + 1]
        )
        if consecutive_declines == 2:
            score += 20  # 3 consecutive quarters of decline
        elif consecutive_declines == 1:
            score += 10
    elif len(all_holdings) >= 2:
        if all_holdings[-1] < all_holdings[-2]:
            score += 8

    # ── Factor 4: Selling velocity (15 points max)
    if len(all_holdings) >= 3:
        recent_change = abs(all_holdings[-1] - all_holdings[-2]) if len(all_holdings) >= 2 else 0
        prev_change = abs(all_holdings[-2] - all_holdings[-3]) if len(all_holdings) >= 3 else 0
        if recent_change > prev_change and prev_change > 0:
            # Accelerating selling
            acceleration = recent_change / prev_change
            if acceleration > 2.0:
                score += 15
            elif acceleration > 1.5:
                score += 10
            else:
                score += 5

    # ── Factor 5: Distance from 50% threshold (10 points max)
    if promoter_current < 50:
        distance = 50 - promoter_current
        score += min(10, distance)
    elif promoter_current > 65:
        score += 0  # Safe
    else:
        score += 3

    return min(100, max(0, int(score)))


def get_risk_label(score: int) -> dict:
    """Convert numeric score to label with color."""
    if score >= 70:
        return {"level": "High", "color": "#ff4d4d", "icon": "🔴"}
    elif score >= 40:
        return {"level": "Medium", "color": "#ffa500", "icon": "🟡"}
    return {"level": "Low", "color": "#00cc88", "icon": "🟢"}
