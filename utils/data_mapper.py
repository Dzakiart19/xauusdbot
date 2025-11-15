"""
Data Normalization & Mapping
Transform API responses into standardized format
"""

from typing import Dict, Any
from datetime import datetime
import pytz

def normalize_market_data(raw_data: Dict[str, Any], source: str = "polygon") -> Dict[str, Any]:
    """
    Normalize market data from different API sources to standard format
    
    Standard format:
    {
        "timestamp_utc": "2025-11-15T12:30:00",
        "open": 2035.15,
        "high": 2035.85,
        "low": 2035.10,
        "close": 2035.50,
        "volume": 1250,
        "bid": 2035.48,
        "ask": 2035.52
    }
    """
    
    if source.lower() == "polygon":
        return _normalize_polygon(raw_data)
    elif source.lower() == "finnhub":
        return _normalize_finnhub(raw_data)
    elif source.lower() == "twelvedata":
        return _normalize_twelvedata(raw_data)
    elif source.lower() == "goldapi":
        return _normalize_goldapi(raw_data)
    else:
        raise ValueError(f"Unknown data source: {source}")

def _normalize_polygon(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Polygon.io format
    Example: {"t": 1700055000000, "o": 2035.15, "h": 2035.85, "l": 2035.10, "c": 2035.50, "v": 1250}
    """
    timestamp_ms = data.get("t", 0)
    timestamp_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC).isoformat()
    
    return {
        "timestamp_utc": timestamp_utc,
        "open": float(data.get("o", 0)),
        "high": float(data.get("h", 0)),
        "low": float(data.get("l", 0)),
        "close": float(data.get("c", 0)),
        "volume": int(data.get("v", 0)),
        "bid": data.get("bid"),
        "ask": data.get("ask"),
    }

def _normalize_finnhub(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Finnhub format
    Example: {"t": 1700055000, "o": 2035.15, "h": 2035.85, "l": 2035.10, "c": 2035.50, "v": 1250}
    """
    timestamp_sec = data.get("t", 0)
    timestamp_utc = datetime.fromtimestamp(timestamp_sec, tz=pytz.UTC).isoformat()
    
    return {
        "timestamp_utc": timestamp_utc,
        "open": float(data.get("o", 0)),
        "high": float(data.get("h", 0)),
        "low": float(data.get("l", 0)),
        "close": float(data.get("c", 0)),
        "volume": int(data.get("v", 0)),
        "bid": data.get("bid"),
        "ask": data.get("ask"),
    }

def _normalize_twelvedata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize TwelveData format
    """
    timestamp_utc = data.get("datetime", datetime.utcnow().isoformat())
    
    return {
        "timestamp_utc": timestamp_utc,
        "open": float(data.get("open", 0)),
        "high": float(data.get("high", 0)),
        "low": float(data.get("low", 0)),
        "close": float(data.get("close", 0)),
        "volume": int(data.get("volume", 0)),
        "bid": data.get("bid"),
        "ask": data.get("ask"),
    }

def _normalize_goldapi(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize GoldAPI.io format
    Note: GoldAPI only provides current price, not OHLC
    """
    timestamp_utc = data.get("timestamp", datetime.utcnow().isoformat())
    price = float(data.get("price", 0))
    
    # For GoldAPI, use current price for all OHLC (not ideal for backtesting)
    return {
        "timestamp_utc": timestamp_utc,
        "open": price,
        "high": price,
        "low": price,
        "close": price,
        "volume": 0,  # GoldAPI doesn't provide volume
        "bid": price,
        "ask": price,
    }

def format_signal_message(signal: Dict[str, Any]) -> str:
    """
    Format signal data for Telegram message display
    
    Args:
        signal: Signal dictionary with direction, prices, confidence, etc.
    
    Returns:
        Formatted message string
    """
    direction = signal.get("direction", "UNKNOWN")
    entry_price = signal.get("entry_price", 0)
    sl_price = signal.get("sl_price", 0)
    tp_price = signal.get("tp_price", 0)
    confidence = signal.get("confidence_score", 0)
    signal_id = signal.get("signal_id", "N/A")
    timestamp = signal.get("timestamp", "N/A")
    
    direction_emoji = "📈 BUY" if direction == "BUY" else "📉 SELL"
    
    message = f"""{direction_emoji}

🎯 Signal ID: {signal_id}
🕐 Time: {timestamp}
⭐ Confidence: {confidence:.1f}%

📊 Price Levels:
Entry: {entry_price:.2f}
Stop Loss: {sl_price:.2f}
Take Profit: {tp_price:.2f}

🛡️ Risk/Reward: {signal.get('rr_ratio', 'N/A')}
"""
    return message

def format_trade_result(trade: Dict[str, Any]) -> str:
    """
    Format closed trade result for Telegram message
    """
    direction = trade.get("direction", "UNKNOWN")
    status = trade.get("status", "UNKNOWN")
    entry_price = trade.get("entry_price", 0)
    exit_price = trade.get("exit_price", 0)
    pips = trade.get("pips_gained", 0)
    pl_usd = trade.get("virtual_pl_usd", 0)
    
    status_emoji = "✅" if "WIN" in status else "❌"
    pl_color = "+" if pl_usd >= 0 else ""
    
    message = f"""{status_emoji} Trade Closed

Direction: {direction}
Entry: {entry_price:.2f}
Exit: {exit_price:.2f}
Pips: {pl_color}{pips:.2f}
P/L: ${pl_color}{pl_usd:.2f}
"""
    return message
