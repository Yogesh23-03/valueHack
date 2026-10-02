# BizSim

BizSim is a fire-drill cascade simulator for small businesses. It shows how one disruption (a late supplier, a late customer, a cost spike) propagates through a business into a stock-out, delayed orders, a customer payment delay, and a cash-flow gap.

## Features & Highlights

- **Cascade Simulator Engine**: Model disruption parameters (delay, cost spikes, payment extensions) and view dynamic timeline & cash flow projections.
- **Action Comparison**: Compare mitigation strategies (early discounts, alternative suppliers, payment term extensions).
- **AI Scenario Parser**: Translate natural language text into structured simulation parameters.
- **Vendor Risk & Bill Scanning**: Automated vendor verification checks and invoice parsing.
- **Automated Report Generation**: Download PDF summary reports of risk analysis and financial impact.

## Architecture

- **Frontend**: Next.js 14 (App Router), Tailwind CSS, Recharts, React Flow (`@xyflow/react`), Framer Motion, Lucide React
- **Backend**: FastAPI, SQLModel, SQLite, ReportLab, Google Generative AI SDK

## Local Setup & Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive API Documentation: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
- Web Application URL: `http://localhost:3000`

## Core API Endpoints

- `GET /health` - System health status check
- `GET /api/business` - Fetches active business profile details
- `POST /api/simulate/cascade` - Runs cash flow & stock-out cascade simulation
- `POST /api/actions/compare` - Evaluates mitigation action plans
- `POST /api/scenario/parse` - Parses plain-text disruption prompts
- `POST /api/vendor/check` - Verifies GSTIN/PAN vendor compliance
- `POST /api/bill/scan` - Scans uploaded invoice PDFs/images
- `GET /api/report` - Generates PDF summary export

## Demo Scenario

- **Business**: Sharma Hardware and Electricals
- **Baseline Scenario**: Supplier A is 14 days late.
- **Expected Outputs**: Stock-out on day 10, cash below zero on day 23, Supplier C payment fails on day 25.

## Philosophy

BizSim provides estimates, not predictions. The tool suggests; the owner decides.

