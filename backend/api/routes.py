from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.models import (
    Portfolio,
    PriceHistory,
    Signal,
    Stock,
    TradeHistory,
)
from backend.services.scanner import run_scan

router = APIRouter()


@router.get("/stocks")
def get_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.is_active.is_(True)).all()
    return [
        {"id": s.id, "symbol": s.symbol, "name": s.name, "active": s.is_active}
        for s in stocks
    ]


@router.post("/stocks")
def add_stock(symbol: str, name: str | None = None, db: Session = Depends(get_db)):
    existing = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already exists")
    stock = Stock(symbol=symbol.upper(), name=name, is_active=True)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return {"id": stock.id, "symbol": stock.symbol}


@router.get("/signals")
def get_signals(limit: int = 50, db: Session = Depends(get_db)):
    sigs = (
        db.query(Signal)
        .order_by(Signal.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "symbol": s.symbol,
            "signal": s.signal_type,
            "daily_change": s.daily_change_pct,
            "spread": s.spread_pct,
            "premium_growth": s.premium_growth_pct,
            "ltp": s.ltp,
            "confidence": s.confidence,
            "notes": s.notes,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sigs
    ]


@router.post("/scan")
def trigger_scan(db: Session = Depends(get_db)):
    signals = run_scan(db)
    return {"signals_generated": len(signals), "signals": signals}


@router.get("/portfolio")
def get_portfolio(user_id: str = "default_user", db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=user_id, balance=100000.0)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return {
        "user_id": portfolio.user_id,
        "balance": portfolio.balance,
        "total_profit_loss": portfolio.total_profit_loss,
        "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
    }


@router.get("/history")
def get_trade_history(
    user_id: str = "default_user",
    limit: int = 50,
    db: Session = Depends(get_db),
):
    trades = (
        db.query(TradeHistory)
        .filter(TradeHistory.user_id == user_id)
        .order_by(TradeHistory.executed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "action": t.action,
            "quantity": t.quantity,
            "price": t.price,
            "total_value": t.total_value,
            "profit_loss": t.profit_loss,
            "executed_at": t.executed_at.isoformat() if t.executed_at else None,
        }
        for t in trades
    ]


@router.get("/prices/{symbol}")
def get_price_history(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    prices = (
        db.query(PriceHistory)
        .filter(PriceHistory.symbol == symbol.upper())
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "symbol": p.symbol,
            "ltp": p.ltp,
            "open": p.open_price,
            "close": p.close_price,
            "high": p.high_price,
            "low": p.low_price,
            "bid": p.bid_price,
            "ask": p.ask_price,
            "volume": p.volume,
            "premium": p.premium,
            "recorded_at": p.recorded_at.isoformat() if p.recorded_at else None,
        }
        for p in prices
    ]
