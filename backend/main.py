from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import SCAN_CRON_HOUR, SCAN_CRON_MINUTE
from backend.models.database import SessionLocal, init_db
from backend.services.scanner import run_scan


def _scheduled_scan() -> None:
    db = SessionLocal()
    try:
        signals = run_scan(db)
        print(f"[Scheduler] Morning scan complete — {len(signals)} signal(s) generated")
    finally:
        db.close()


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    scheduler.add_job(
        _scheduled_scan,
        CronTrigger(hour=SCAN_CRON_HOUR, minute=SCAN_CRON_MINUTE),
        id="morning_stock_scan",
    )
    scheduler.start()
    print(
        f"[Scheduler] Started — auto-scan every morning at "
        f"{SCAN_CRON_HOUR:02d}:{SCAN_CRON_MINUTE:02d}"
    )
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Trading Stock Scanner",
    description=(
        "Layer 3/4 strategy: system auto-selects stocks with >2% daily change, "
        "checks liquidity (Ask-Bid)/Spot < 40%, ATM premium growth > 4%, "
        "trades at Ask price. Signals auto-display on user dashboard each morning."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"status": "running", "service": "Trading Stock Scanner API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
