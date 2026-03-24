"""
app.py
Flask backend for the Promoter Stake Selling Dashboard v2.
Serves the dashboard and handles API endpoints for update, status,
results, trend data, and per-company deep analysis.
"""

import threading
import time
from flask import Flask, render_template, jsonify, request
from data_fetcher import get_promoter_sellers
from analyzer import analyze_all, generate_ai_insights

app = Flask(__name__)

# ── Global in-memory cache
_cache = {
    "data": [],
    "insights": [],
    "status": "idle",          # idle | running | done | error
    "progress": 0,
    "total": 0,
    "current_ticker": "",
    "last_updated": None,
    "error": None,
    "scan_history": [],        # list of past scan summaries (30-day memory)
}
_lock = threading.Lock()


def _run_update(min_holding: float = 40.0):
    """Background thread that fetches + analyzes promoter data."""
    with _lock:
        _cache["status"] = "running"
        _cache["progress"] = 0
        _cache["error"] = None
        _cache["data"] = []
        _cache["insights"] = []

    def progress_cb(done, total, ticker):
        with _lock:
            _cache["progress"] = done
            _cache["total"] = total
            _cache["current_ticker"] = ticker

    try:
        sellers = get_promoter_sellers(min_holding=min_holding, progress_callback=progress_cb)
        analyzed = analyze_all(sellers)
        insights = generate_ai_insights(analyzed)

        timestamp = time.strftime("%d %b %Y, %I:%M %p")
        with _lock:
            _cache["data"] = analyzed
            _cache["insights"] = insights
            _cache["status"] = "done"
            _cache["last_updated"] = timestamp
            # Store scan summary for history
            _cache["scan_history"].append({
                "timestamp": timestamp,
                "count": len(analyzed),
                "high_risk": len([r for r in analyzed if r.get("analysis", {}).get("risk_level") == "High"]),
                "tickers": [r["ticker"] for r in analyzed],
            })
            # Keep only last 30 entries
            _cache["scan_history"] = _cache["scan_history"][-30:]
    except Exception as e:
        with _lock:
            _cache["status"] = "error"
            _cache["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/update", methods=["POST"])
def api_update():
    """Start background update task."""
    with _lock:
        if _cache["status"] == "running":
            return jsonify({"status": "already_running", "message": "Scan already in progress…"}), 200

    thread = threading.Thread(target=_run_update, args=(40.0,), daemon=True)
    thread.start()
    return jsonify({"status": "started", "message": "Scanning markets… This takes 2–3 minutes."})


@app.route("/api/status", methods=["GET"])
def api_status():
    """Return current scan status and progress."""
    with _lock:
        return jsonify({
            "status": _cache["status"],
            "progress": _cache["progress"],
            "total": _cache["total"],
            "current_ticker": _cache["current_ticker"],
            "last_updated": _cache["last_updated"],
            "count": len(_cache["data"]),
            "error": _cache["error"],
        })


@app.route("/api/results", methods=["GET"])
def api_results():
    """Return the current results data with insights."""
    with _lock:
        return jsonify({
            "status": _cache["status"],
            "last_updated": _cache["last_updated"],
            "count": len(_cache["data"]),
            "results": _cache["data"],
            "insights": _cache["insights"],
        })


@app.route("/api/analyze/<ticker>", methods=["GET"])
def api_analyze(ticker):
    """Return deep-dive analysis for a specific company."""
    ticker = ticker.upper().strip()
    with _lock:
        for r in _cache["data"]:
            if r["ticker"] == ticker:
                return jsonify({"found": True, "data": r})
    return jsonify({"found": False, "message": f"No data found for {ticker}. Run 'update' first."}), 404


@app.route("/api/trend", methods=["GET"])
def api_trend():
    """Return trend data for charts."""
    with _lock:
        results = _cache["data"]
        history = _cache["scan_history"]

    # Build chart data
    risk_distribution = {"High": 0, "Medium": 0, "Low": 0}
    verdict_distribution = {"Exit": 0, "Caution": 0, "Hold": 0, "Buy": 0}
    holding_data = []

    for r in results:
        a = r.get("analysis", {})
        risk = a.get("risk_level", "Low")
        verdict = a.get("verdict", "Hold")
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        verdict_distribution[verdict] = verdict_distribution.get(verdict, 0) + 1
        holding_data.append({
            "ticker": r["ticker"],
            "company_name": r.get("company_name", r["ticker"]),
            "current": r.get("promoter_current", 0),
            "previous": r.get("promoter_prev", 0),
            "change": r.get("promoter_change", 0),
            "all_holdings": r.get("all_holdings", []),
            "quarters": r.get("quarters", []),
        })

    return jsonify({
        "risk_distribution": risk_distribution,
        "verdict_distribution": verdict_distribution,
        "holding_data": holding_data,
        "scan_history": history,
    })


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("\n" + "="*60)
    print("  [*] PROMOTER STAKE SELLING DASHBOARD v2")
    print("  [>] Open: http://localhost:5000")
    print("  [i] Commands: update | analyze [ticker] | trend")
    print("="*60 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
