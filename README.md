# Promoter Stake AI Platform

@https://bsestock-frontend.onrender.com/

An enterprise-grade, AI-powered financial platform that monitors promoter stake selling in Indian markets.

## Architecture

- **Backend**: FastAPI (Python), MongoDB (Motor sync/async), APScheduler
- **Frontend**: React 18, Vite, Tailwind CSS v4, Recharts
- **AI Intelligence**: OpenAI API for context, summarization, and trend prediction
- **Data Gathering**: Async HTTP scraping (Screener.in), Yahoo Finance APIs

## Features

- **Automated Scanning**: Tracks +40% promoter holdings and detects significant reductions.
- **Smart Risk Scoring**: 0-100 composite risk score with High/Medium/Low thresholds.
- **AI Insights**: Automatically drafts "Reasons for Selling", "Future Outlook", and "Verdict".
- **Telegram Alerts**: Real-time push notifications for high-risk alerts.
- **Watchlist**: Users can track specific companies.

## Local Development

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Setup Environment Variables
cp .env.example .env
# Edit .env with your MongoDB URI, JWT Secret, and OpenAI key
```

### 2. Frontend Setup

```bash
# Install Node dependencies
cd frontend
npm install
```

### 3. Running Development Servers

Start the backend (runs in `localhost:8000`):
```bash
uvicorn backend.main:app --reload
```

Start the frontend (runs on `localhost:5173`):
```bash
cd frontend
npm run dev
```

## Production Deployment

This project uses Render for deployment. Push to GitHub and connect Render to deploy the `render.yaml` blueprint.
