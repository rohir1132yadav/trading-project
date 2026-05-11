from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import SCAN_INTERVAL_MINUTES
from backend.models.database import SessionLocal, init_db
from backend.services.scanner import run_scan


def _scheduled_scan() -> None:
    db = SessionLocal()
    try:
        signals = run_scan(db)
        print(f"[Scheduler] Scan complete — {len(signals)} signal(s) generated")
    finally:
        db.close()


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(
        _scheduled_scan,
        "interval",
        minutes=SCAN_INTERVAL_MINUTES,
        id="stock_scan",
    )
    scheduler.start()
    print(f"[Scheduler] Started — scanning every {SCAN_INTERVAL_MINUTES} min")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Trading Stock Scanner",
    description="Layer 3/4 strategy: scan stocks, check liquidity & premium, generate signals",
    version="1.0.0",
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
