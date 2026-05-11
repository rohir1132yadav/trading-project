from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from backend.models.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    ltp = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)
    bid_price = Column(Float, nullable=True)
    ask_price = Column(Float, nullable=True)
    premium = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # BUY / SELL / HOLD
    daily_change_pct = Column(Float, nullable=True)
    spread_pct = Column(Float, nullable=True)
    premium_growth_pct = Column(Float, nullable=True)
    ltp = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), default="default_user", index=True)
    balance = Column(Float, default=100000.0)
    total_profit_loss = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), default="default_user", index=True)
    symbol = Column(String(20), nullable=False)
    action = Column(String(10), nullable=False)  # BUY / SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    profit_loss = Column(Float, default=0.0)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
