"""
REST API Data Poller
Fetch market data from REST endpoints with caching and rate limiting
"""

import requests
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import time
from utils.logger import get_logger
from utils.data_mapper import normalize_market_data
from config.settings import (
    POLYGON_API_KEY, FINNHUB_API_KEY, TWELVEDATA_API_KEY, GOLDAPI_API_KEY
)

logger = get_logger()

class RESTPoller:
    """
    Poll market data from REST APIs with fallback mechanism
    """
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.last_request_time = {}
        self.rate_limit_delay = 0.5  # seconds between requests per provider
        
        # Data cache (deque for memory efficiency)
        self.m1_cache = deque(maxlen=500)
        self.m5_cache = deque(maxlen=500)
        self.quote_cache = {}
        self.quote_cache_time = None
        self.quote_cache_ttl = 5  # seconds
    
    async def get_market_data(self, symbol: str = "XAUUSD", timeframe: str = "M1") -> Optional[Dict[str, Any]]:
        """
        Get market data from primary provider, fallback to secondary
        
        Args:
            symbol: Trading symbol (default XAUUSD)
            timeframe: Timeframe (M1 or M5)
        
        Returns:
            Normalized market data dict or None if all providers fail
        """
        
        providers = [
            ("polygon", self._fetch_from_polygon),
            ("finnhub", self._fetch_from_finnhub),
            ("twelvedata", self._fetch_from_twelvedata),
        ]
        
        for provider_name, fetch_func in providers:
            try:
                data = await fetch_func(symbol, timeframe)
                if data:
                    normalized = normalize_market_data(data, provider_name)
                    return normalized
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {str(e)}")
                continue
        
        logger.error(f"All providers failed for {symbol} {timeframe}")
        return None
    
    async def _fetch_from_polygon(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Fetch from Polygon.io REST API"""
        if not POLYGON_API_KEY:
            return None
        
        await self._rate_limit("polygon")
        
        # Convert XAUUSD to proper format for Polygon
        endpoint_symbol = "C:XAUUSD"
        multiplier = {"M1": 1, "M5": 5}.get(timeframe, 1)
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{endpoint_symbol}/range/{multiplier}/minute"
        params = {
            "from": (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%d"),
            "to": datetime.utcnow().strftime("%Y-%m-%d"),
            "apiKey": POLYGON_API_KEY,
            "limit": 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                latest = data["results"][-1]
                return latest
        except Exception as e:
            logger.error(f"Polygon API error: {str(e)}")
        
        return None
    
    async def _fetch_from_finnhub(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Fetch from Finnhub REST API"""
        if not FINNHUB_API_KEY:
            return None
        
        await self._rate_limit("finnhub")
        
        # Finnhub uses different symbol format
        # For real-time: use quote endpoint
        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": "XAUUSD",
            "token": FINNHUB_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Extract OHLC from Finnhub quote
            if "c" in data:  # current price
                return {
                    "c": data["c"],
                    "h": data.get("h", data["c"]),
                    "l": data.get("l", data["c"]),
                    "o": data.get("o", data["c"]),
                    "t": int(time.time()),
                    "v": data.get("v", 0),
                    "bid": data.get("bid"),
                    "ask": data.get("ask"),
                }
        except Exception as e:
            logger.error(f"Finnhub API error: {str(e)}")
        
        return None
    
    async def _fetch_from_twelvedata(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Fetch from TwelveData REST API"""
        if not TWELVEDATA_API_KEY:
            return None
        
        await self._rate_limit("twelvedata")
        
        interval = {"M1": "1min", "M5": "5min"}.get(timeframe, "1min")
        
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": "XAUUSD",
            "interval": interval,
            "apikey": TWELVEDATA_API_KEY,
            "outputsize": 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "ok" and data.get("values"):
                latest = data["values"][0]
                return {
                    "open": float(latest["open"]),
                    "high": float(latest["high"]),
                    "low": float(latest["low"]),
                    "close": float(latest["close"]),
                    "volume": int(latest.get("volume", 0)),
                    "datetime": latest["datetime"]
                }
        except Exception as e:
            logger.error(f"TwelveData API error: {str(e)}")
        
        return None
    
    async def _rate_limit(self, provider: str) -> None:
        """Enforce rate limiting per provider"""
        last_time = self.last_request_time.get(provider, 0)
        elapsed = time.time() - last_time
        
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        
        self.last_request_time[provider] = time.time()
    
    def get_cached_data(self, timeframe: str = "M1") -> List[Dict[str, Any]]:
        """
        Get cached market data
        
        Args:
            timeframe: M1 or M5
        
        Returns:
            List of cached candles
        """
        cache = self.m1_cache if timeframe == "M1" else self.m5_cache
        return list(cache)
    
    def add_to_cache(self, data: Dict[str, Any], timeframe: str = "M1") -> None:
        """Add data to cache"""
        cache = self.m1_cache if timeframe == "M1" else self.m5_cache
        cache.append(data)

# Global poller instance
rest_poller = RESTPoller()
