# BizSim

BizSim is a fire-drill cascade simulator for small businesses. It shows how one disruption (a late supplier, a late customer, a cost spike) propagates through a business into a stock-out, delayed orders, a customer payment delay, and a cash-flow gap.

## Architecture
- **Frontend**: Next.js 14 (App Router), Tailwind CSS, Recharts, Framer Motion
- **Backend**: FastAPI, SQLModel, SQLite

## Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Demo Scenario
- **Business**: Sharma Hardware and Electricals
- **Baseline Scenario**: Supplier A is 14 days late.
- **Expected Outputs**: Stock-out on day 10, cash below zero on day 23, Supplier C payment fails on day 25.

## Data
This app uses **synthetic mock data**. The vendor checks and bill scans simulate AI and API lookups for demonstration purposes.

## Philosophy
BizSim provides estimates, not predictions. The tool suggests; the owner decides.
