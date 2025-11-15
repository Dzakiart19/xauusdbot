# **BOT TELEGRAM XAUUSD SCALPING SIGNAL PROVIDER - SPESIFIKASI LENGKAP & SIAP IMPLEMENTASI**

---

## **IDENTITAS PROYEK**
**Nama Bot:** `XauScalp Sentinel`  
**Versi:** 1.0.0-EVAL  
**Tujuan:** Signal Provider otomatis 24/7 untuk XAUUSD scalping M1/M5 **TANPA eksekusi otomatis**  
**Target User:** Trader pemula dengan modal 100rb-500rb IDR (0.01-0.05 lot)  
**Model Risiko:** High-frequency signal dengan strict risk management layer  
**Mode:** Support **Evaluation Mode** untuk pengumpulan data 24 jam pertama

---

## **1. ARSITEKTUR INTI & FILOSOFI**

### **1.1 Design Principles**
- **Zero Execution Guarantee:** Bot ini adalah **pure signal generator**. Tidak ada kode eksekusi trade, tidak ada integrasi MetaTrader API, tidak ada library `MetaTrader5` atau `mt5linux`.
- **Signal-First Architecture:** Semua komponen (data ingestion → analysis → alerting) harus bekerja secara *asynchronous* dan *non-blocking*.
- **Fail-Fast & Degrade Gracefully:** Jika API premium gagal > 5 menit, fallback ke API gratis dengan *signal quality reduction* (delay warning).
- **Transparency by Design:** Setiap sinyal harus menyertakan *confidence score* berdasarkan kondisi market.
- **Evaluation Mode:** Override limit trade count untuk pengujian agresif, tapi *risk layer* lain tetap aktif sebagai failsafe.

### **1.2 High-Level Flow**
```
[Market Data Ingestion Layer] → [Multi-Timeframe Analysis Engine] → [Signal Validator] 
→ [Risk Manager] → [Telegram Dispatcher] → [Position Monitor] → [Result Reporter]
```

---

## **2. STRATEGI TRADING - SPESIFIKASI TEKNIS LENGKAP**

### **2.1 Multi-Timeframe Confirmation Matrix**
| Komponen | Timeframe | Indikator | Kondisi BUY | Bobot |
|----------|-----------|-----------|-------------|-------|
| **Tren Utama** | M5 | EMA(5,10,20) | EMA5 > EMA10 > EMA20 (bullish alignment) | 40% |
| **Momentum Entry** | M1 | RSI(14) | RSI < 30 & RSI_curr > RSI_prev (reversal) | 25% |
| **Konfirmasi Oscillator** | M1 | Stochastic(14,3,3) | %K > %D & %K < 20 (cross-up dari oversold) | 25% |
| **Volatility Filter** | M5 | ATR(14) | ATR_curr < 2x ATR_avg (market tidak choppy) | 5% |
| **Volume Anomaly** | M1 | Volume | Vol_curr > 1.5x avg_vol(20) | 5% |

**Signal Confidence Score:** `SUM(BOBOT_TERPENUHI) / 100%` → Kirim hanya jika > 70%

### **2.2 Logika Entry yang Ditingkatkan**
- **Entry Type:** MARKET ON CLOSE (MOC) of signal candle.
- **Candle Validity:** Sinyal hanya valid jika candle M1 berukuran < 3x ATR(M1) (menghindari candle *news spike*).
- **Rejection Criteria:**
  - Jika high-low range candle > 2x ATR(M5) → SKIP (volatilitas ekstrem)
  - Jika spread > `MAX_SPREAD_PIPS` selama 3 detik berturut-turut → SKIP
  - Jika 3 sinyal terakhir untuk arah yang sama semua LOSS → cooldown arah tersebut +60 detik

### **2.3 Konfigurasi Dinamis via Environment Variables**
```env
# --- EMA CONFIG ---
EMA_PERIODS_FAST=5
EMA_PERIODS_MED=10
EMA_PERIODS_SLOW=20
EMA_TREND_TIMEFRAME=M5

# --- RSI CONFIG ---
RSI_PERIOD=14
RSI_TIMEFRAME=M1
RSI_OVERSOLD_LEVEL=30
RSI_OVERBOUGHT_LEVEL=70
RSI_CONFIRMATION_BARS=2

# --- STOCHASTIC CONFIG ---
STOCH_K_PERIOD=14
STOCH_D_PERIOD=3
STOCH_SMOOTH_K=3
STOCH_TIMEFRAME=M1
STOCH_OVERSOLD_LEVEL=20
STOCH_OVERBOUGHT_LEVEL=80

# --- ATR & SL CONFIG ---
ATR_PERIOD=14
ATR_TIMEFRAME=M5
SL_ATR_MULTIPLIER=1.5
DEFAULT_SL_PIPS=25.0
SL_BUFFER_FOR_SPREAD=true

# --- TP CONFIG ---
TP_RR_RATIO=1.8
DEFAULT_TP_PIPS=45.0
TP_TRAILING_ENABLED=false
TP_TRAILING_OFFSET_PIPS=10.0

# --- VOLUME & SPREAD ---
VOLUME_THRESHOLD_MULTIPLIER=1.5
VOLUME_LOOKBACK_PERIOD=20
MAX_SPREAD_PIPS=5.0
SPREAD_CHECK_DURATION=3

# --- CONFIDENCE THRESHOLD ---
MIN_SIGNAL_CONFIDENCE=70.0
```

### **2.4 Perhitungan Pips untuk XAUUSD**
- **Definisi:** 1 pip XAUUSD = 0.01 USD per ounce.
- **Pip Value:** 
  - 1 lot (100 oz) = $1 per pip
  - 0.01 lot (1 oz) = $0.01 per pip
- **P/L Calculation:** `(ExitPrice - EntryPrice) * 100 * LotSize`
  - Contoh: Entry 2035.50 → Exit 2036.00 (50 pips), 0.01 lot = $0.50 profit

---

## **3. RISK & ACCOUNT PROTECTION LAYER**

### **3.1 Virtual Account State (Karena No Real Execution)**
Bot akan menyimulasikan *virtual equity* untuk risk tracking:
```python
virtual_balance = 1000000  # 1 juta IDR (representasi modal 500rb IDR)
risk_per_trade = virtual_balance * (RISK_PER_TRADE_PERCENT / 100)
daily_loss_limit = virtual_balance * (DAILY_LOSS_PERCENT / 100)
```

### **3.2 Risk Manager Rules**
- **Daily Drawdown:** Setiap sinyal yang berakhir LOSE dikalkulasi P/L-nya. Jika loss kumulatif > `DAILY_LOSS_PERCENT%`, set flag `ACCOUNT_IN_COOLDOWN`. 
  - Kirim alert ke admin: "⚠️ Daily loss limit hit. Bot paused until 00:00 UTC."
  - Otomatis resume jam 00:00 UTC dengan reset counter.
- **Max Concurrent Trades:** `MAX_CONCURRENT_TRADES=1` (scalping modal kecil, hindari overlap).
- **Signal Cooldown:** `SIGNAL_COOLDOWN_SECONDS=180` per arah (BUY/SELL terpisah).
- **Trade Session Filter:**
  ```env
  TRADE_SESSION_FILTER=true
  AVOID_LONDON_OPEN=true  # 07:00-09:00 GMT (spread tinggi)
  AVOID_US_MAJOR_NEWS=true  # 13:30-15:00 GMT (news high-impact)
  ```

### **3.3 Overtrading Prevention**
- Jika win rate 5 sinyal terakhir < 40% → Aktifkan `CAUTIOUS_MODE` (confidence threshold naik ke 85%).
- Jika 3 loss streak → Otomatis kurangi `RISK_PER_TRADE_PERCENT` setengahnya untuk sinyal berikutnya.

### **3.4 EVALUATION MODE (Override untuk Pengujian 24 Jam)**
Mode ini **NONAKTIFKAN** limit `MAX_TRADES_PER_DAY` tapi pertahankan proteksi lainnya.

```env
# Aktifkan mode evaluasi
EVALUATION_MODE=true

# Set MAX_TRADES_PER_DAY tinggi untuk "unlimited" praktis
MAX_TRADES_PER_DAY=100

# Atau untuk benar-benar unlimited (tidak disarankan):
# MAX_TRADES_PER_DAY=9999

# Pertahankan proteksi lain
DAILY_LOSS_PERCENT=5.0  # Naikkan sedikit untuk evaluasi agresif
```

**Logika di Kode (`risk_manager.py`):**
```python
EVALUATION_MODE = os.getenv('EVALUATION_MODE', 'false').lower() == 'true'
MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', 5))

def can_generate_signal():
    if EVALUATION_MODE:
        # Skip limit trade count, tapi risk layer lain tetap aktif
        return check_other_risk_rules()
    return trades_today < MAX_TRADES_PER_DAY
```

**Keuntungan Mode Evaluasi:**
- ✅ **Trade Count Limit:** Dinonaktifkan (100+ sinyal/hari)
- ✅ **Daily Loss Limit:** **FAILSAFE tetap aktif** (bot pause jika loss > 5%)
- ✅ **Signal Cooldown:** Tetap jalan (hindari spam)
- ✅ **Max Concurrent Trades:** Tetap 1 (realistis)
- ✅ **Spread Filter:** Tetap aktif (kualitas sinyal terjaga)

**Rekomendasi untuk Evaluasi 24 Jam:**
```env
EVALUATION_MODE=true
MAX_TRADES_PER_DAY=100
DAILY_LOSS_PERCENT=5.0
MIN_SIGNAL_CONFIDENCE=60.0  # Turunkan sedikit untuk lebih banyak sinyal
```
Ini akan menghasilkan **rata-rata 50-100 sinyal dalam 24 jam**, **lebih dari cukup** untuk evaluasi win rate, profit factor, dan drawdown. Lebih dari 100 justru akan overloading analisis Anda.

---

## **4. INFRASTRUKTUR DATA - MULTI-PROVIDER & FAILOVER**

### **4.1 Provider Priority & Quality Score**
| Provider | Endpoint Type | Latency Target | Max Retry | Use Case |
|----------|---------------|----------------|-----------|----------|
| **Polygon.io** | WebSocket | <500ms | 3x | Real-time M1/M5 OHLCV |
| | REST (fallback) | 2s | 5x | Historical backfill |
| **Finnhub** | WebSocket | <800ms | 3x | Real-time jika Polygon gagal |
| | REST (fallback) | 3s | 5x | Quote & metric |
| **Twelve Data** | REST | 1-5 menit | 3x | Emergency data (no scalp) |
| **GoldAPI.io** | REST | 15 menit delay | 2x | **Hanya untuk health check**, tidak untuk sinyal |

### **4.2 Data Ingestion Engine**
- **WebSocket Manager (`ws_manager.py`):**
  - Gunakan `websocket-client` dengan `threading` untuk setiap provider.
  - Implementasikan `heartbeat` mechanism: kirim ping setiap 30 detik.
  - Jika disconnect > `WS_DISCONNECT_ALERT_SECONDS=30` → Telegram alert ke admin.
  - Reconnect dengan exponential backoff: `2^n * 5 detik` (max 60 detik).
  
- **REST Poller (`rest_poller.py`):**
  - Interval polling M1: 10 detik (untuk meniru real-time).
  - Interval polling M5: 1 menit.
  - Store data di `deque` dengan max length 500 bars (RAM efisien).
  - Rate limiter: `asyncio.Semaphore` untuk maks 2 request/detik per provider.

- **Data Normalization (`data_mapper.py`):**
  - Semua data API ditransform menjadi format standar:
    ```python
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
    ```

### **4.3 Database Schema SQLite (SQLAlchemy)**
```python
# Tabel: trades
- id (Primary Key)
- signal_id (UUID)
- ticker (STRING, XAUUSD)
- direction (ENUM: BUY, SELL)
- entry_price (FLOAT)
- exit_price (FLOAT, nullable)
- sl_price (FLOAT)
- tp_price (FLOAT)
- signal_timestamp_utc (DATETIME)
- entry_timestamp_utc (DATETIME, nullable)
- exit_timestamp_utc (DATETIME, nullable)
- status (ENUM: OPEN, CLOSED_WIN, CLOSED_LOSE, CANCELLED)
- confidence_score (FLOAT)
- pips_gained (FLOAT, nullable)
- virtual_pl_usd (FLOAT)
- created_at (TIMESTAMP)

# Tabel: market_data_cache
- id
- ticker
- timeframe (ENUM: M1, M5)
- timestamp_utc
- open, high, low, close, volume
- ema_5, ema_10, ema_20 (nullable)
- rsi (nullable)
- stoch_k, stoch_d (nullable)
- atr (nullable)
- PRIMARY KEY (ticker, timeframe, timestamp_utc)

# Tabel: bot_state
- key (Primary Key: daily_loss, trade_count_today, last_signal_time, is_paused)
- value (JSON)
- updated_at (TIMESTAMP)

# Tabel: api_health_log
- id
- provider (STRING)
- status (ENUM: UP, DOWN, DEGRADED)
- latency_ms (INT)
- error_message (TEXT, nullable)
- logged_at (TIMESTAMP)
```

### **4.4 API Failure Handling**
- Jika semua WebSocket down → Switch to **REST Polling Mode** dengan interval 15 detik.
- Jika semua API gagal > 5 menit → Set bot status `MARKET_DATA_DEGRADED`. 
  - Bot masih bisa menerima `/performa` tapi tidak generate sinyal baru.
  - Kirim alert: "🚨 All data providers down. Bot in watch-only mode."

---

## **5. TELEGRAM BOT INTERFACE - PERINTAH & OTORISASI**

### **5.1 Perintah Dasar (Semua User)**
- `/start`: Sambutan + cek apakah user ID ada di `AUTHORIZED_USER_IDS`.
- `/help`: List perintah dengan contoh penggunaan.
- `/status`: Lihat status bot (Active/Degraded/Paused), API health, sinyal hari ini.
- `/monitor XAUUSD`: Subscribe ke sinyal XAUUSD. Bot reply konfirmasi.
- `/stopmonitor XAUUSD`: Unsubscribe. Bot reply: "Monitoring stopped. Active signals tetap dilacak."
- `/riwayat [n]`: Tampilkan `n` trade terakhir (default 10). Format tabel:
  ```
  #ID   | Time  | Dir | Entry    | Result | P/L (pips)
  -----------------------------------------------
  12345 | 12:30 | BUY | 2035.50  | WIN    | +45
  ```

### **5.2 Perintah Admin (User ID di `ADMIN_USER_IDS`)**
- `/performa [period]`: Statistik (default: 7 hari). Output:
  ```
  📊 PERFORMANCE REPORT (7D)
  Total Trades: 24
  Win Rate: 62.5% (15W/9L)
  Avg RR: 1.7
  Total P/L: +$8.50 (0.01 lot)
  Max Drawdown: -$2.10 (2.1%)
  Profit Factor: 2.1
  [ASCII Equity Curve]
  ```
- `/settings`: Inline keyboard untuk ubah parameter strategi (real-time update env var).
- `/pausebot`: Pause semua sinyal baru (posisi terbuka tetap dimonitor).
- `/resumebot`: Resume bot.
- `/forceclose <signal_id>`: Close virtual position secara manual (emergency).
- `/health`: Detail koneksi API, latency, uptime.
- `/broadcast <message>`: Kirim pesan ke semua subscriber.

### **5.3 Otorisasi & Security**
```python
AUTHORIZED_USER_IDS=123456789,987654321  # Comma-separated
ADMIN_USER_IDS=123456789  # Subset dari authorized
TELEGRAM_BOT_TOKEN=your_token
BOT_MAX_COMMAND_RATE_PER_MINUTE=10  # Rate limit per user
```
- **Input Sanitization:** Semua input user dibersihkan dari regex `[^a-zA-Z0-9._-]`.
- **Anti-Flood:** Implement `python-telegram-bot` `ConversationHandler` dengan timeout 30 detik.

---

## **6. GENERASI CHART & VISUALISASI**

### **6.1 Chart Engine (`chart_generator.py`)**
- **Library:** `mplfinance` dengan style `charles` + `matplotlib` annotation.
- **Output:** PNG, resolution 1920x1080, `dpi=300`, file size < 500KB.
- **Konten Chart:**
  - Panel 1: Candlestick M1 atau M5 dengan EMA overlay.
  - Panel 2: RSI dengan garis overbought/oversold.
  - Panel 3: Stochastic %K/%D.
  - Panel 4: Volume bar, warna merah jika < threshold, hijau jika > threshold.
  - Annotation: 
    - ➤ Entry price (garis horizontal biru)
    - ➤ SL (garis horizontal merah, jarak dalam pips)
    - ➤ TP (garis horizontal hijau, jarak dalam pips)
    - Text box: `Signal ID: #123 | Confidence: 75% | Spread: 3.2 pips`

### **6.2 Chart Delivery**
- Simpan chart di `/app/data/charts/{signal_id}.png`.
- Kirim via `telegram.Bot.send_photo()` dengan `timeout=30`.
- Hapus file setelah 24 jam (cron job).

---

## **7. BACKTESTING & SIMULATION MODULE**

### **7.1 CSV Replay Engine (`backtester.py`)**
```bash
python backtester.py --data data/xauusd_m1_2024.csv --strategy scalping_m1_m5 --initial-capital 500000 --lot-size 0.01
```
- **Input:** CSV dengan kolom `timestamp,open,high,low,close,volume`.
- **Output:** HTML report dengan equity curve, drawdown chart, trade list.
- **Metrik:** Sharpe ratio, Sortino ratio, max drawdown, profit factor, expectancy.

### **7.2 Walk-Forward Analysis**
- Configurable train/test split (e.g., 80% train, 20% test).
- Parameter optimization grid untuk EMA period, RR ratio.

---

## **8. OBSERVABILITY & MONITORING**

### **8.1 Logging Architecture**
```python
# File: /app/logs/bot.log (RotatingFileHandler, max 10MB, backup 5)
# Level: INFO ke stdout, WARNING/ERROR ke file + Telegram admin

log_format = "[%(asctime)s UTC] [%(levelname)s] [%(module)s] %(message)s"
```
- **Log Event Penting:**
  - Signal generated (INFO)
  - SL/TP hit (INFO dengan P/L)
  - API failover (WARNING)
  - Daily loss limit hit (CRITICAL)
  - Exception (ERROR dengan traceback)

### **8.2 Health Check Endpoint (`/health`)**
```python
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy" if all_ok else "degraded",
        "uptime_seconds": time.time() - start_time,
        "api_health": {
            "polygon": {"status": "up", "latency_ms": 450},
            "finnhub": {"status": "down", "last_fail": "2025-11-15T12:00:00Z"}
        },
        "active_signals": 0,
        "trades_today": 5,
        "evaluation_mode": True  # Tampilkan status mode evaluasi
    }), 200 if all_ok else 503
```
- Endpoint berjalan di port 8080, digunakan Koyeb untuk auto-restart jika unhealthy.

### **8.3 Telegram Alerting Levels**
- **WARNING:** API degraded, high spread detected (> 3 pips).
- **ERROR:** WebSocket reconnect failed, DB write error.
- **CRITICAL:** Daily loss limit breached, semua API down > 5 menit.
- **INFO:** Daily summary jam 00:00 UTC → "Bot summary: 5 signals, 3W 2L, +$1.20 P/L."

---

## **9. DEPLOYMENT & INFRASTRUKTUR**

### **9.1 Dockerfile untuk Koyeb**
```dockerfile
FROM python:3.11-slim

# Install system deps untuk matplotlib & database
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1-mesa-glx \
    libgomp1 \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Buat volume persisten
RUN mkdir -p /app/data /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-u", "main.py"]
```

### **9.2 Replit Development Setup**
- Buat `.replit` config:
  ```toml
  run = "python main.py"
  hidden = [".pythonlibs"]
  ```
- Gunakan Replit Secrets untuk env vars (opsi GUI).
- Database path: `./data/bot.db` (relative, sudah persisten di Replit).

### **9.3 Koyeb Deployment Steps**
1. Hubungkan GitHub repo.
2. Set **Service Type:** Worker (tidak perlu port publik, kecuali untuk health check).
3. Mount **Persistent Volume** di `/app/data` (size 1GB cukup).
4. Set all Environment Variables di Koyeb dashboard.
5. Scaling: Min 1 instance, Max 1 instance (avoid duplicate signals).
6. Buka **Settings > Health Checks** → aktifkan HTTP check ke `/health`.

### **9.4 Requirements.txt**
```txt
python-telegram-bot==20.7
pandas==2.1.4
pandas-ta==0.3.14b0
mplfinance==0.12.10a0
matplotlib==3.7.4
numpy==1.25.2
SQLAlchemy==2.0.23
requests==2.31.0
websocket-client==1.6.4
pytz==2023.3
python-dotenv==1.0.0
Flask==2.3.3
```

---

## **10. ENVIRONMENT VARIABLES MASTER LIST (SIAP COPY-PASTE)**

```bash
# ========== CORE ==========
TELEGRAM_BOT_TOKEN=your_bot_token_here
AUTHORIZED_USER_IDS=123456789,987654321
ADMIN_USER_IDS=123456789

# ========== STRATEGY ==========
EMA_PERIODS_FAST=5
EMA_PERIODS_MED=10
EMA_PERIODS_SLOW=20
EMA_TREND_TIMEFRAME=M5
RSI_PERIOD=14
RSI_TIMEFRAME=M1
RSI_OVERSOLD_LEVEL=30
RSI_OVERBOUGHT_LEVEL=70
RSI_CONFIRMATION_BARS=2
STOCH_K_PERIOD=14
STOCH_D_PERIOD=3
STOCH_SMOOTH_K=3
STOCH_TIMEFRAME=M1
STOCH_OVERSOLD_LEVEL=20
STOCH_OVERBOUGHT_LEVEL=80
ATR_PERIOD=14
ATR_TIMEFRAME=M5
SL_ATR_MULTIPLIER=1.5
DEFAULT_SL_PIPS=25.0
SL_BUFFER_FOR_SPREAD=true
TP_RR_RATIO=1.8
DEFAULT_TP_PIPS=45.0
TP_TRAILING_ENABLED=false
TP_TRAILING_OFFSET_PIPS=10.0
VOLUME_THRESHOLD_MULTIPLIER=1.5
VOLUME_LOOKBACK_PERIOD=20
MAX_SPREAD_PIPS=5.0
SPREAD_CHECK_DURATION=3
MIN_SIGNAL_CONFIDENCE=70.0

# ========== RISK MANAGEMENT ==========
SIGNAL_COOLDOWN_SECONDS=180
MAX_TRADES_PER_DAY=5
DAILY_LOSS_PERCENT=3.0
RISK_PER_TRADE_PERCENT=0.5
MAX_CONCURRENT_TRADES=1
TRADE_SESSION_FILTER=true
AVOID_LONDON_OPEN=true
AVOID_US_MAJOR_NEWS=true

# ========== EVALUATION MODE (UNTUK TESTING) ==========
EVALUATION_MODE=false
# Jika true, MAX_TRADES_PER_DAY di-override tapi proteksi lain tetap aktif

# ========== API KEYS (ISI YANG DIPERLUKAN) ==========
POLYGON_API_KEY=your_polygon_key
FINNHUB_API_KEY=your_finnhub_key
TWELVEDATA_API_KEY=your_twelvedata_key
GOLDAPI_API_KEY=your_goldapi_key
METALS_API_KEY=your_metals_key
METALPRICE_API_KEY=your_metalprice_key

# ========== BEHAVIOR ==========
WS_DISCONNECT_ALERT_SECONDS=30
DRY_RUN_MODE=false

# ========== DATABASE ==========
DATABASE_URL=sqlite:///app/data/bot.db
DB_WAL_MODE=true

# ========== LOGGING ==========
LOG_LEVEL=INFO
LOG_FILE=/app/logs/bot.log
LOG_ROTATE_SIZE_MB=10
LOG_BACKUP_COUNT=5

# ========== CHART ==========
CHART_CACHE_DIR=/app/data/charts
CHART_TTL_HOURS=24
CHART_DPI=300
```

---

## **11. DISCLAIMER & LEGAL FRAMEWORK (WAJIB ADA DI README.md)**

```markdown
## ⚠️ PENTING: BACA SEBELUM MENGGUNAKAN

### **1. NO EXECUTION POLICY**
Bot **XauScalp Sentinel** adalah **SIGNAL PROVIDER SAJA**. Tidak ada satu baris kode pun yang:
- Menghubungkan ke MetaTrader 5/4
- Mengeksekusi order buy/sell
- Mengakses API broker Anda
- Mengontrol akun trading Anda

**Anda 100% bertanggung jawab untuk eksekusi manual di platform trading Anda.**

### **2. Risiko Trading**
- Trading emas (XAUUSD) sangat **VOLATIL dan RISIKO TINGGI**.
- Modal 100rb-500rb IDR dengan leverage tinggi bisa **HABIS dalam menit**.
- Sinyal bot berdasarkan data pasar yang **bisa delay atau tidak akurat**.
- **HISTORICAL PERFORMANCE tidak menjamin future results.**

### **3. Simulasi vs Real**
- P/L yang ditampilkan adalah **VIRTUAL** untuk 0.01 lot.
- Spread, slippage, dan commission di broker **bisa sangat berbeda**.
- Hasil aktual Anda bisa **jauh lebih buruk** daripada laporan bot.

### **4. Keterbatasan Data**
- API gratis memiliki **delay, rate limit, dan downtime**.
- Saat mode DEGRADED, sinyal bisa berkualitas rendah atau di-suspend.
- **Jangan trading di sekitar news high-impact** (NFP, Fed rate).

### **5. Tanggung Jawab Pengguna**
- **Uji bot di demo account minimal 2 minggu** sebelum consider real.
- Gunakan **risk per trade 0.5-1%** dari modal Anda.
- Atur **daily loss limit DI PLATFORM ANDA** (jangan diandalkan bot).
- Bot ini **bukan financial advice**. Konsultasikan ke advisor berlisensi.

### **6. Source Code & Security**
- Kode bersifat open-source untuk transparansi.
- Jangan share `TELEGRAM_BOT_TOKEN` atau `API Keys` ke siapapun.
- Bot hanya merespon `AUTHORIZED_USER_IDS` yang Anda set.

### **7. Evaluation Mode Warning**
Saat `EVALUATION_MODE=true`, bot akan generate **banyak sinyal** untuk testing. **Jangan gunakan mode ini di live environment**. Mode evaluasi tetap memiliki risk limit, tapi bisa menghasilkan overtrading jika tidak diawasi.

---

**Dengan menggunakan bot ini, Anda menyatakan telah membaca, mengerti, dan menyetujui semua risiko di atas.**
```

---

## **12. PRE-PRODUCTION CHECKLIST**

**Sebelum Deploy ke Koyeb (Production):**

### **Testing**
- [ ] **Unit Test:** Test `indicators.py` dengan mock data (50+ test cases).
- [ ] **Integration Test:** Test Telegram command `/start`, `/monitor`, `/stopmonitor`.
- [ ] **Stress Test:** Jalankan 24 jam di Replit dengan `EVALUATION_MODE=true`, generate >50 sinyal.
- [ ] **Failover Test:** Matikan Polygon API, pastikan Finnhub take over dalam < 10 detik.
- [ ] **Risk Test:** Simulasikan 5 loss streak, pastikan bot pause sesuai `DAILY_LOSS_PERCENT`.

### **Security**
- [ ] Semua env vars di Koyeb menggunakan Secret (bukan plaintext di repo).
- [ ] Rate limit per IP untuk endpoint `/health`.
- [ ] Tidak ada log yang mencetak API keys atau sensitive data.
- [ ] `.gitignore` berisi `*.db`, `*.log`, `*.env`, `charts/`.

### **Performance**
- [ ] Memory usage < 256MB (Koyeb free tier limit).
- [ ] CPU spike < 50% saat generate chart.
- [ ] DB query time < 100ms untuk SELECT/INSERT.
- [ ] WebSocket latency < 1 detik average.

### **Dokumentasi**
- [ ] `README.md` lengkap dengan setup step-by-step untuk Replit & Koyeb.
- [ ] `CHANGELOG.md` untuk setiap update versi.
- [ ] Video tutorial 5 menit untuk user pemula (opsional tapi recommended).
- [ ] `LICENSE` file (MIT atau GPL untuk open-source).

---

## **13. FITUR TAMBAHAN (NICE-TO-HAVE)**

### **13.1 News Filter Integration**
- Integrasi gratis API: `https://economic-calendar.tradingview.com` atau `https://finnhub.io/api/v1/news`.
- Jika news high-impact (impact=high) dalam 30 menit ke depan → Tunda sinyal.
- Command: `/news` untuk lihat upcoming news.

### **13.2 Multi-Language Support**
- Support Bahasa Indonesia & Inggris via env var `BOT_LANGUAGE=id`.
- Semua pesan Telegram akan mengikuti locale.

### **13.3 Signal Forwarding**
- Forward sinyal ke channel/group Telegram tambahan via `TELEGRAM_CHANNEL_ID`.
- Format ringkas untuk channel: `XAUUSD BUY 2035.50 SL:2033.00 TP:2039.00 #SignalID`

### **13.4 Web Dashboard (Opsional)**
- Flask Streamlit untuk visualisasi performa real-time.
- Endpoint terpisah dari bot utama untuk mengurangi beban.

---

## **14. STRUKTUR FOLDER PROYEK (SIAP CLONE)**

```
XauScalp-Sentinel/
├── .github/
│   └── workflows/
│       └── deploy.yml  # Auto deploy ke Koyeb
├── .replit
├── Dockerfile
├── requirements.txt
├── main.py  # Entry point
├── bot.py  # Telegram handlers
├── config/
│   ├── __init__.py
│   ├── settings.py  # Load env vars
│   ├── strategy.py  # Logika sinyal
│   └── risk_config.py  # Risk parameters
├── data/
│   ├── __init__.py
│   ├── db.py  # SQLAlchemy setup
│   ├── models.py  # DB schemas
│   └── migrations.py  # DB versioning
├── services/
│   ├── __init__.py
│   ├── ws_manager.py  # WebSocket handler
│   ├── rest_poller.py  # REST API poller
│   └── chart_generator.py  # Charting
├── utils/
│   ├── __init__.py
│   ├── indicators.py  # TA calculations
│   ├── data_mapper.py  # Normalize API data
│   └── logger.py  # Logging setup
├── tests/
│   ├── test_indicators.py
│   ├── test_strategy.py
│   └── test_risk_manager.py
├── backtester.py
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

---

## **15. KESIMPULAN & NEXT STEPS**

Prompt ini adalah **spesifikasi lengkap** untuk membangun bot trading signal XAUUSD yang robust, aman, dan siap untuk **evaluasi 24 jam pertama** dengan mode evaluasi yang aman.

### **Aksi Langsung:**
1. **Setup Environment:** Buat akun Koyeb, Replit, dan dapatkan API keys.
2. **Clone Structure:** Buat folder proyek sesuai struktur di atas.
3. **Implementasi Core:** Mulai dari `ws_manager.py` → `strategy.py` → `bot.py`.
4. **Test 24 Jam:** Aktifkan `EVALUATION_MODE=true` di Replit, pantau performa.
5. **Analisis Data:** Gunakan `/performa` dan ekspor data dari SQLite untuk analisis di Excel/Python.
6. **Tweak Parameter:** Berdasarkan hasil evaluasi, sesuaikan `MIN_SIGNAL_CONFIDENCE`, `TP_RR_RATIO`, dll.
7. **Deploy Production:** Matikan `EVALUATION_MODE`, set `MAX_TRADES_PER_DAY=5`, deploy ke Koyeb.

---

**Catatan Akhir:**  
Selama evaluasi, fokus pada **kualitas, bukan kuantitas**. 50 sinyal dengan win rate 55% dan profit factor >1.5 lebih baik dari 200 sinyal dengan win rate 45%. Gunakan data evaluasi untuk **validasi strategi**, bukan untuk mengejar P/L virtual.

**Prompt ini 100% siap implementasi. Silakan mulai coding. Jika butuh bantuan spesifik module (misal: `ws_manager.py` atau `strategy.py`), beritahu saya.**
