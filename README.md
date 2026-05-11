# Trading Stock Scanner

A Python-based stock trading scanner that implements a multi-layer screening strategy:

1. **Volume Filter** — Only consider stocks with volume > 1,000
2. **Daily Change** — Stock must have increased > 2% from previous close
3. **Liquidity Check** — Bid-ask spread must be < 2%
4. **Premium Growth** — Option premium growth must exceed 4%

Stocks passing all filters generate **BUY** signals displayed on a real-time dashboard.

## Architecture

```
┌───────────────────┐
│   Streamlit UI    │
│  (Python Front)   │
└────────┬──────────┘
         │
┌────────┴──────────┐
│  FastAPI Backend   │
│   (Python API)     │
└────────┬──────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │ Scanner │ Liquidity│ Premium  │
    │ Engine  │ Checker  │ Checker  │
    └────┬────┴──────────┴──────────┘
         │
┌────────┴──────────┐
│   PostgreSQL DB   │
└───────────────────┘
```

## Quick Start

### Using Docker Compose (recommended)

```bash
docker-compose up --build
```

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://trading_user:trading_pass@localhost:5432/trading_db"

# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
streamlit run frontend/dashboard.py --server.port 8501
```

## API Endpoints

| Method | Endpoint             | Description              |
|--------|----------------------|--------------------------|
| GET    | `/api/stocks`        | List tracked stocks      |
| POST   | `/api/stocks`        | Add a new stock          |
| GET    | `/api/signals`       | Get latest signals       |
| POST   | `/api/scan`          | Trigger a manual scan    |
| GET    | `/api/portfolio`     | View user portfolio      |
| GET    | `/api/history`       | Trade history            |
| GET    | `/api/prices/{sym}`  | Price history for stock  |

## Scan Pipeline

```
Morning Scheduler Starts
        ↓
Fetch Demo Account Market Data
        ↓
Compare Previous Price
        ↓
If Increase > 2%
        ↓
Liquidity Check (Spread < 2%)
        ↓
Premium Check (Growth > 4%)
        ↓
Generate Signal
        ↓
Store In Database
        ↓
Show In Streamlit Dashboard
```

## Configuration

All thresholds are configurable via environment variables:

| Variable                     | Default | Description                     |
|------------------------------|---------|---------------------------------|
| `DATABASE_URL`               | —       | PostgreSQL connection string    |
| `SCAN_INTERVAL_MINUTES`      | 60      | Background scan interval        |
| `DAILY_INCREASE_THRESHOLD`   | 2.0     | Min daily change % to consider  |
| `LIQUIDITY_SPREAD_THRESHOLD` | 2.0     | Max spread % for liquidity      |
| `PREMIUM_GROWTH_THRESHOLD`   | 4.0     | Min premium growth % for signal |
| `MIN_VOLUME`                 | 1000    | Min volume filter                |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, APScheduler
- **Frontend**: Python, Streamlit, Plotly
- **Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose
