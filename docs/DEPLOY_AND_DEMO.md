# Deploy and Demo Guide

## Deployment

### 1. Backend (Render)
- Create a new Web Service on Render, connect to this repo.
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:
  - `GEMINI_API_KEY`: (Your Google Gemini API Key, optional for fallback)

### 2. Frontend (Vercel)
- Create a new Project on Vercel, connect to this repo.
- Framework Preset: Next.js
- Root Directory: `frontend`
- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: (The URL of your Render backend)

## 3-Minute Demo Script
1. **0:00** — "Small businesses see suppliers, stock, orders, payments one at a time. But a late supplier becomes a stock-out, a late customer payment, and a cash gap. BizSim shows that chain before it happens."
2. **0:20** — Point at the landing hero animation.
3. **0:35** — Open Fire Drill. Set delay to 14. "Supplier A is 14 days late." Point at the cascade map lighting up. "Restock slips from day 8 to day 22. Fans run out on day 10. Verma order goes late. Cash goes negative on day 23. Supplier C payment fails on day 25."
4. **1:10** — Point at cash runway chart. "The red line is zero. Here's the danger day."
5. **1:25** — Point at action cards. Click "Check New Distributor". "Score 32. Red. Registered 4 months ago, two cheque-bounce cases, missing GST filings. The cheaper vendor is a trap." Point at SUGGESTED tag. "The combined action — extension plus early discount — protects the owner best."
6. **2:10** — Point at Why? panel. "Every number has a reason, every estimate has an assumption."
7. **2:30** — Open Report. "One-page decision report." Click Print.
8. **2:50** — "BizSim. See the chain before it happens."

## Judge Questions Checklist
- **Q: Is this real data?** A: We used realistic synthetic data to model the engine.
- **Q: How does the AI work?** A: Gemini is used for unstructured tasks like plain-language scenario parsing and bill scanning. The financial engine is purely deterministic and fully explainable.
