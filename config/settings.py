"""
Settings & Environment Variables Manager
Centralized configuration loading with defaults and validation
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CHARTS_DIR = BASE_DIR / "data" / "charts"

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, CHARTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ========== CORE ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in os.getenv("AUTHORIZED_USER_IDS", "").split(",") if uid.strip()]
ADMIN_USER_IDS = [int(uid.strip()) for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip()]

# ========== STRATEGY - EMA ==========
EMA_PERIODS_FAST = int(os.getenv("EMA_PERIODS_FAST", 5))
EMA_PERIODS_MED = int(os.getenv("EMA_PERIODS_MED", 10))
EMA_PERIODS_SLOW = int(os.getenv("EMA_PERIODS_SLOW", 20))
EMA_TREND_TIMEFRAME = os.getenv("EMA_TREND_TIMEFRAME", "M5")

# ========== STRATEGY - RSI ==========
RSI_PERIOD = int(os.getenv("RSI_PERIOD", 14))
RSI_TIMEFRAME = os.getenv("RSI_TIMEFRAME", "M1")
RSI_OVERSOLD_LEVEL = int(os.getenv("RSI_OVERSOLD_LEVEL", 30))
RSI_OVERBOUGHT_LEVEL = int(os.getenv("RSI_OVERBOUGHT_LEVEL", 70))
RSI_CONFIRMATION_BARS = int(os.getenv("RSI_CONFIRMATION_BARS", 2))

# ========== STRATEGY - STOCHASTIC ==========
STOCH_K_PERIOD = int(os.getenv("STOCH_K_PERIOD", 14))
STOCH_D_PERIOD = int(os.getenv("STOCH_D_PERIOD", 3))
STOCH_SMOOTH_K = int(os.getenv("STOCH_SMOOTH_K", 3))
STOCH_TIMEFRAME = os.getenv("STOCH_TIMEFRAME", "M1")
STOCH_OVERSOLD_LEVEL = int(os.getenv("STOCH_OVERSOLD_LEVEL", 20))
STOCH_OVERBOUGHT_LEVEL = int(os.getenv("STOCH_OVERBOUGHT_LEVEL", 80))

# ========== STRATEGY - ATR & SL ==========
ATR_PERIOD = int(os.getenv("ATR_PERIOD", 14))
ATR_TIMEFRAME = os.getenv("ATR_TIMEFRAME", "M5")
SL_ATR_MULTIPLIER = float(os.getenv("SL_ATR_MULTIPLIER", 1.5))
DEFAULT_SL_PIPS = float(os.getenv("DEFAULT_SL_PIPS", 25.0))
SL_BUFFER_FOR_SPREAD = os.getenv("SL_BUFFER_FOR_SPREAD", "true").lower() == "true"

# ========== STRATEGY - TP ==========
TP_RR_RATIO = float(os.getenv("TP_RR_RATIO", 1.8))
DEFAULT_TP_PIPS = float(os.getenv("DEFAULT_TP_PIPS", 45.0))
TP_TRAILING_ENABLED = os.getenv("TP_TRAILING_ENABLED", "false").lower() == "true"
TP_TRAILING_OFFSET_PIPS = float(os.getenv("TP_TRAILING_OFFSET_PIPS", 10.0))

# ========== STRATEGY - VOLUME & SPREAD ==========
VOLUME_THRESHOLD_MULTIPLIER = float(os.getenv("VOLUME_THRESHOLD_MULTIPLIER", 1.5))
VOLUME_LOOKBACK_PERIOD = int(os.getenv("VOLUME_LOOKBACK_PERIOD", 20))
MAX_SPREAD_PIPS = float(os.getenv("MAX_SPREAD_PIPS", 5.0))
SPREAD_CHECK_DURATION = int(os.getenv("SPREAD_CHECK_DURATION", 3))

# ========== SIGNAL GENERATION ==========
MIN_SIGNAL_CONFIDENCE = float(os.getenv("MIN_SIGNAL_CONFIDENCE", 70.0))

# ========== RISK MANAGEMENT ==========
SIGNAL_COOLDOWN_SECONDS = int(os.getenv("SIGNAL_COOLDOWN_SECONDS", 180))
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", 5))
DAILY_LOSS_PERCENT = float(os.getenv("DAILY_LOSS_PERCENT", 3.0))
RISK_PER_TRADE_PERCENT = float(os.getenv("RISK_PER_TRADE_PERCENT", 0.5))
MAX_CONCURRENT_TRADES = int(os.getenv("MAX_CONCURRENT_TRADES", 1))
TRADE_SESSION_FILTER = os.getenv("TRADE_SESSION_FILTER", "true").lower() == "true"
AVOID_LONDON_OPEN = os.getenv("AVOID_LONDON_OPEN", "true").lower() == "true"
AVOID_US_MAJOR_NEWS = os.getenv("AVOID_US_MAJOR_NEWS", "true").lower() == "true"

# ========== EVALUATION MODE ==========
EVALUATION_MODE = os.getenv("EVALUATION_MODE", "false").lower() == "true"

# ========== API KEYS ==========
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")
GOLDAPI_API_KEY = os.getenv("GOLDAPI_API_KEY", "")
METALS_API_KEY = os.getenv("METALS_API_KEY", "")
METALPRICE_API_KEY = os.getenv("METALPRICE_API_KEY", "")

# ========== BEHAVIOR ==========
WS_DISCONNECT_ALERT_SECONDS = int(os.getenv("WS_DISCONNECT_ALERT_SECONDS", 30))
DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "false").lower() == "true"

# ========== DATABASE ==========
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/bot.db")
DB_WAL_MODE = os.getenv("DB_WAL_MODE", "true").lower() == "true"

# ========== LOGGING ==========
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = str(LOGS_DIR / "bot.log")
LOG_ROTATE_SIZE_MB = int(os.getenv("LOG_ROTATE_SIZE_MB", 10))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

# ========== CHART ==========
CHART_CACHE_DIR = str(CHARTS_DIR)
CHART_TTL_HOURS = int(os.getenv("CHART_TTL_HOURS", 24))
CHART_DPI = int(os.getenv("CHART_DPI", 300))

# ========== VIRTUAL ACCOUNT ==========
VIRTUAL_INITIAL_BALANCE = 1000000  # 1 juta IDR representasi
LOT_SIZE = 0.01  # 0.01 lot untuk modal kecil

# App settings
APP_PORT = int(os.getenv("APP_PORT", 8080))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")

def print_config():
    """Print active configuration (for debugging)"""
    print(f"=== Active Configuration ===")
    print(f"Evaluation Mode: {EVALUATION_MODE}")
    print(f"Max Trades/Day: {MAX_TRADES_PER_DAY}")
    print(f"Daily Loss %: {DAILY_LOSS_PERCENT}%")
    print(f"Min Signal Confidence: {MIN_SIGNAL_CONFIDENCE}%")
    print(f"DB: {DATABASE_URL}")
    print(f"Logs: {LOG_FILE}")
    print(f"===========================")
