# Promoter Stake Selling Dashboard v2 - Project Documentation

## 1. Project Overview
The **Promoter Stake Selling Dashboard v2** is a financial intelligence tool that tracks Indian companies listed on the NSE and BSE. It specifically monitors companies where the promoters hold more than **40%** of the shares but are actively **reducing their stake** (selling off shares). 

The application scans a predefined list of companies, analyzes the magnitude and pattern of the sell-offs using a custom rule-based engine, and provides actionable insights (Buy/Hold/Caution/Exit), risk scores, and trend analysis to investors.

---

## 2. Technology Stack
The project is built using a lightweight, Python-heavy tech stack. It currently operates primarily as a monolithic application.

*   **Backend / Server:** Python 3 with the **Flask** web framework.
*   **Web Scraping & Data Fetching:** `requests` for making HTTP calls and `BeautifulSoup4` (bs4) for extracting data from HTML pages.
*   **Frontend (Main Dashboard):** Vanilla HTML ([templates/index.html](file:///d:/pr/templates/index.html)), CSS ([static/style.css](file:///d:/pr/static/style.css)), and JavaScript ([static/app.js](file:///d:/pr/static/app.js)). *Note: There is a React template created via Vite in the `frontend/` folder, but the actual working dashboard is running entirely on the vanilla stack.*
*   **Data Visualization:** **Chart.js** (loaded via CDN) for rendering interactive trend charts.
*   **Concurrency:** Python's built-in `threading` module is used to run the data fetching process in the background without blocking the web server.

---

## 3. Data Source and Fetching Mechanism

### Where is the data fetched from?
The data is primarily scraped from **Screener.in**, a popular financial research website for Indian stocks. 

### How is it fetched? ([data_fetcher.py](file:///d:/pr/data_fetcher.py))
1.  **Ticker Universe:** The script has a hardcoded list of 87 popular large-cap and mid-cap Indian stocks (e.g., RELIANCE, TCS, ZOMATO).
2.  **Web Scraping:** The [fetch_screener_data](file:///d:/pr/data_fetcher.py#70-150) function uses the `requests` library to download the HTML page for each company from Screener.in (`https://www.screener.in/company/{ticker}/`).
3.  **Data Extraction:** It uses `BeautifulSoup` to parse the HTML. It looks specifically for the "Shareholding Pattern" table and extracts the quarterly percentage of shares held by promoters. It also fetches the company name and Market Cap.
4.  **Filtering:** The [get_promoter_sellers](file:///d:/pr/data_fetcher.py#152-192) function filters the scraped data. It only returns companies where:
    *   The current promoter holding is `> 40%`.
    *   The current holding is *less than* the previous quarter's holding (indicating recent selling).
5.  **Rate Limiting:** To avoid being blocked by Screener.in for making too many requests rapidly, the fetcher includes random delays (`time.sleep()`) and retries.

---

## 4. Analysis and AI Engine

Once the data is fetched, it is passed to a custom "AI" Analysis Engine ([analyzer.py](file:///d:/pr/analyzer.py)). Notably, this doesn't use external LLMs like OpenAI; instead, it uses a highly structured **Rule-Based system** to assess the sell-off and generate insights:

*   **Categorization:** Sell-offs are categorized into Large (> 3% drop), Medium (1–3%), or Small (< 1%).
*   **Verdict & Risk Assessment:** Based on the size of the drop and the remaining holding percentage, it calculates a risk level (High/Medium/Low) and an actionable verdict (Exit/Caution/Hold/Buy).
*   **Promoter Intent:** It analyzes the historical trend of sell-offs to determine if it's a one-time event or a continuous, repeated pattern spanning multiple quarters.
*   **Reasoning & Generation:** It maps these statistics to pre-written, detailed financial explanations (e.g., "Debt Servicing / Pledge Liquidation" or "SEBI Minimum Public Float Compliance") to explain *why* the promoter might be selling and issues a final, combined *Investor Recommendation*.

---

## 5. How the Graphs are Made

The data visualization is handled entirely on the frontend using **Chart.js**, a popular JavaScript charting library.

1.  **API Data (`/api/trend`):** When the user triggers the "trend" command, the frontend fetches aggregated statistics from the Flask backend. This includes the distribution of risk levels, verdicts, and the holding data of the companies with the largest sell-offs.
2.  **Chart Rendering ([static/app.js](file:///d:/pr/static/app.js)):** 
    *   **Risk Distribution Chart:** Plotted as a `doughnut` (donut) chart showing the proportion of High, Medium, and Low risk companies.
    *   **Verdict Breakdown Chart:** Plotted as a horizontal `bar` chart showing the total number of companies in the Exit, Caution, Hold, or Buy categories.
    *   **Holding Comparison Chart:** Plotted as a vertical `bar` chart showing the top 10 companies with the largest promoter reductions. It places the "Previous %" holding and "Current %" holding side-by-side for comparison.

---

## 6. Detailed End-to-End Workflow

1.  **User Access:** The user opens `http://localhost:5000` in their browser. The Flask backend ([app.py](file:///d:/pr/app.py)) serves the [templates/index.html](file:///d:/pr/templates/index.html) file.
2.  **Triggering a Scan:** The user types [update](file:///d:/pr/app.py#77-87) into the UI command prompt and hits Enter.
3.  **Background Processing & Polling:** 
    *   The [app.js](file:///d:/pr/static/app.js) frontend sends a POST request to the `/api/update` endpoint.
    *   Flask starts a background thread ([_run_update](file:///d:/pr/app.py#31-70)).
    *   The frontend begins polling `/api/status` every 1.8 seconds to smoothly animate the progress bar in the UI.
4.  **Fetching & Analyzing:** In the background, [data_fetcher.py](file:///d:/pr/data_fetcher.py) iterates through and scrapes the 87 companies from Screener.in. Next, [analyzer.py](file:///d:/pr/analyzer.py) calculates the insights, risks, and recommendations for the filtered subset of companies.
5.  **Rendering Results:** Once the scan is complete, [app.js](file:///d:/pr/static/app.js) fetches the final JSON from `/api/results`. The JavaScript dynamically builds HTML "Cards" for each company, injecting specific colors and CSS badges based on the calculated risk and verdict.
6.  **Deep Dive:** If the user clicks "View Details" on a card or types `analyze [ticker]`, a modal dynamically opens showing the full, detailed textual report (Intent, Impact, Reasoning, Recommendation) generated by the [analyzer.py](file:///d:/pr/analyzer.py) engine.
