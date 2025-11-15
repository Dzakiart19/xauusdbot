"""
Data Models using SQLAlchemy ORM
Schemas untuk trades, market data cache, bot state, dan API health
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, Boolean, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
import enum
import uuid

Base = declarative_base()

class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED_WIN = "CLOSED_WIN"
    CLOSED_LOSE = "CLOSED_LOSE"
    CANCELLED = "CANCELLED"

class TradeDirection(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class APIStatus(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"

class TimeframeEnum(str, enum.Enum):
    M1 = "M1"
    M5 = "M5"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(36), nullable=False, unique=True)
    ticker = Column(String(10), nullable=False, default="XAUUSD")
    direction = Column(Enum(TradeDirection), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    sl_price = Column(Float, nullable=False)
    tp_price = Column(Float, nullable=False)
    signal_timestamp_utc = Column(DateTime, nullable=False)
    entry_timestamp_utc = Column(DateTime, nullable=True)
    exit_timestamp_utc = Column(DateTime, nullable=True)
    status = Column(Enum(TradeStatus), nullable=False, default=TradeStatus.OPEN)
    confidence_score = Column(Float, nullable=False)  # 0-100
    pips_gained = Column(Float, nullable=True)
    virtual_pl_usd = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trade {self.signal_id} {self.direction} {self.status}>"

class MarketDataCache(Base):
    __tablename__ = "market_data_cache"
    __table_args__ = (
        UniqueConstraint("ticker", "timeframe", "timestamp_utc", name="uq_market_data"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, default="XAUUSD")
    timeframe = Column(Enum(TimeframeEnum), nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False, default=0)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    
    # Indicator values (nullable for real-time cache)
    ema_5 = Column(Float, nullable=True)
    ema_10 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    stoch_k = Column(Float, nullable=True)
    stoch_d = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MarketData {self.ticker} {self.timeframe} {self.timestamp_utc}>"

class BotState(Base):
    __tablename__ = "bot_state"
    
    key = Column(String(50), primary_key=True)  # e.g., "daily_loss", "trade_count_today"
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BotState {self.key}={self.value}>"

class APIHealthLog(Base):
    __tablename__ = "api_health_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)  # e.g., "polygon", "finnhub"
    status = Column(Enum(APIStatus), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    logged_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIHealth {self.provider} {self.status}>"
