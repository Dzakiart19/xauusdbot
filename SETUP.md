# XauScalp Sentinel - Setup & Deployment Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather on Telegram)
- (Optional) API keys for Polygon.io, Finnhub, etc.

### Local Setup (Development)

```bash
# 1. Clone the repository
git clone <repo-url>
cd xauusdbot

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN and API keys

# 5. Initialize database
python -c "from data.db import init_db; init_db()"

# 6. Run the bot
python main.py
```

The bot will:
- ✅ Initialize SQLite database
- ✅ Start Telegram bot polling
- ✅ Start health check on http://localhost:8080/health
- ✅ Begin generating signals

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Telegram (REQUIRED)
TELEGRAM_BOT_TOKEN=your_token_from_botfather
AUTHORIZED_USER_IDS=123456789,987654321  # Comma-separated user IDs
ADMIN_USER_IDS=123456789  # Subset for admin commands

# API Keys (Optional - bot will work with REST fallback)
POLYGON_API_KEY=your_polygon_key
FINNHUB_API_KEY=your_finnhub_key
```

### Strategy Parameters

All parameters can be modified in `.env` file. Examples:

```bash
# Confidence Threshold
MIN_SIGNAL_CONFIDENCE=70.0  # Only generate if 70%+ confidence

# Risk Management
MAX_TRADES_PER_DAY=5
DAILY_LOSS_PERCENT=3.0  # Pause if lose 3% of virtual balance

# Evaluation Mode (for testing - removes trade count limit)
EVALUATION_MODE=true  # Set to false for production
```

---

## 📊 Telegram Bot Commands

### User Commands
- `/start` - Welcome message
- `/help` - List all commands
- `/status` - Bot status
- `/monitor` - Subscribe to XAUUSD signals
- `/riwayat [n]` - View last n trades (default 10)

### Admin Commands
- `/performa [period]` - Performance report (default 7 days)
- `/settings` - Modify parameters in real-time
- `/pausebot` - Pause signal generation
- `/resumebot` - Resume bot
- `/health` - API provider health status

---

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/test_indicators.py -v
python -m pytest tests/test_strategy.py -v
```

### Backtesting with CSV Data
```bash
# Format: timestamp,open,high,low,close,volume
python backtester.py --data data/xauusd_m1_2024.csv

# With custom parameters
python backtester.py --data data/xauusd_m1_2024.csv \
  --initial-capital 500000 \
  --lot-size 0.01
```

### Enable Evaluation Mode (24-hour testing)
```bash
# .env file:
EVALUATION_MODE=true
MAX_TRADES_PER_DAY=100
MIN_SIGNAL_CONFIDENCE=60.0  # Lower for more signals

# Run bot
python main.py
```

This will generate 50-100+ signals in 24 hours for strategy evaluation.

---

## 🐳 Docker Deployment

### Local Docker
```bash
# Build image
docker build -t xauusdbot:latest .

# Run with environment file
docker run --env-file .env \
  -v $(pwd)/data:/app/data \
  -p 8080:8080 \
  xauusdbot:latest
```

### Push to Docker Hub
```bash
docker tag xauusdbot:latest <your-username>/xauusdbot:latest
docker push <your-username>/xauusdbot:latest
```

---

## ☁️ Deployment on Koyeb

### Step-by-Step (5 Minutes)

1. **Create Koyeb Account**
   - Go to https://www.koyeb.com
   - Sign up with GitHub/Email

2. **Connect GitHub Repository**
   - New Service → GitHub repository
   - Select `xauusdbot` repository
   - Dockerfile: Select `Dockerfile`
   - Builder: Buildpacks

3. **Configure Environment**
   - Go to Service Settings → Environment
   - Add variables from `.env.example`:
     ```
     TELEGRAM_BOT_TOKEN=your_token
     AUTHORIZED_USER_IDS=123456789
     ADMIN_USER_IDS=123456789
     POLYGON_API_KEY=optional
     EVALUATION_MODE=false
     ```

4. **Configure Health Check**
   - Settings → Health Checks
   - HTTP endpoint: `/health`
   - Port: 8080
   - Interval: 30s
   - Timeout: 10s

5. **Set Persistence**
   - Storage → Add Directory
   - Mount path: `/app/data`
   - Size: 1GB (enough for years of data)

6. **Deploy**
   - Click "Create Service"
   - Wait for deployment (2-3 minutes)
   - Bot is now live 24/7!

### Auto-Restart on Failure
Koyeb automatically restarts failed instances. Health check endpoint ensures bot is always responsive.

---

## 📈 Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "evaluation_mode": true,
  "telegram_configured": true
}
```

### View Logs

**Local:**
```bash
tail -f logs/bot.log
```

**Koyeb:**
- Dashboard → Service → Logs tab
- Real-time log streaming

### Database Query

```bash
# View trades
sqlite3 data/bot.db "SELECT * FROM trades LIMIT 10;"

# View bot state
sqlite3 data/bot.db "SELECT * FROM bot_state;"

# Statistics
sqlite3 data/bot.db "
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status='CLOSED_WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN status='CLOSED_LOSE' THEN 1 ELSE 0 END) as losses
  FROM trades;
"
```

---

## 🔐 Security

### API Key Management
- Never commit `.env` file (in `.gitignore`)
- Use Koyeb's Secret management for production
- Rotate API keys regularly
- Use scoped API keys with minimal permissions

### Telegram Security
- Only add trusted user IDs to `AUTHORIZED_USER_IDS`
- Admin commands require `ADMIN_USER_IDS`
- Bot validates all inputs before processing

### Database
- SQLite WAL mode enabled for concurrent access
- Automatic backups recommended (external sync)
- No sensitive data stored (only prices, signals, results)

---

## 🐛 Troubleshooting

### Bot Not Starting
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip install -r requirements.txt --upgrade

# Verify .env file
cat .env  # Ensure TELEGRAM_BOT_TOKEN is set
```

### No Signals Generated
```bash
# Check evaluation mode
grep EVALUATION_MODE .env

# Lower confidence threshold for testing
MIN_SIGNAL_CONFIDENCE=50.0

# Check logs
tail -f logs/bot.log

# Verify API connectivity
python -c "from services.rest_poller import rest_poller; import asyncio; print(asyncio.run(rest_poller.get_market_data()))"
```

### Database Errors
```bash
# Reset database (WARNING: Deletes all trades)
python -c "from data.db import drop_db; drop_db()"

# Reinitialize
python -c "from data.db import init_db; init_db()"
```

### Telegram Bot Not Responding
```bash
# Verify token
echo $TELEGRAM_BOT_TOKEN

# Test bot
curl -X GET "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Check bot status
/health endpoint should return 200 with telegram_configured: true
```

---

## 📊 Performance Benchmarks

**Expected Performance (Evaluation Mode, 24h):**
- Signals/day: 50-100
- Win rate: 50-65%
- Profit factor: 1.2-1.8
- Max drawdown: 2-5%
- Memory usage: 150-250MB
- CPU usage: < 5% average

**Hardware Requirements:**
- Minimum: 256MB RAM, 100MB disk (Koyeb free tier)
- Recommended: 512MB RAM, 1GB disk
- Network: Stable internet (failover to REST if WebSocket down)

---

## 🚀 Next Steps

1. **Set up Telegram Bot**
   - Go to @BotFather on Telegram
   - Create bot → Get token
   - Add to `.env`

2. **Choose Deployment**
   - Local: `python main.py`
   - Docker: See "Docker Deployment" above
   - Koyeb: See "Koyeb Deployment" above

3. **Test Strategy**
   - Enable EVALUATION_MODE
   - Run for 24 hours
   - Review performance via `/performa`
   - Adjust parameters as needed

4. **Go to Production**
   - Set EVALUATION_MODE=false
   - Adjust MAX_TRADES_PER_DAY (default 5)
   - Deploy to Koyeb
   - Monitor via logs and `/status` endpoint

---

## 📚 Additional Resources

- [README.md](README.md) - Full specification
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [LICENSE](LICENSE) - MIT License & Disclaimer
- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [Polygon.io Docs](https://polygon.io/docs)
- [Finnhub Docs](https://finnhub.io/docs/api)

---

## ❓ FAQ

**Q: Can the bot execute trades automatically?**
A: No, by design. This is a signal provider only. You must manually execute trades or use a separate execution system.

**Q: Is backtesting available?**
A: Yes, use `backtester.py` with CSV data. See "Testing" section above.

**Q: How are virtual P/L calculated?**
A: Based on 0.01 lot size. 1 pip = $0.01 × lot size. Multiply by 100 for 0.01 lot = $1/pip.

**Q: Can I modify strategy parameters while running?**
A: Yes, via `/settings` Telegram command (admin only). Changes take effect next signal generation.

**Q: What happens if all APIs fail?**
A: Bot enters DEGRADED mode. Health check returns 503. No new signals generated until APIs recover.

**Q: How is daily loss calculated?**
A: Sum of all closed trades with negative P/L. Resets at 00:00 UTC.

---

## 📞 Support

For issues, questions, or contributions:
1. Check [CHANGELOG.md](CHANGELOG.md) for known issues
2. Review logs: `tail -f logs/bot.log`
3. Test in Evaluation Mode first
4. Open GitHub issue with detailed logs

---

**Happy Trading! 🎯**

Remember: This is a signal provider, not an execution system. Always verify signals before trading and use proper risk management on your broker platform.
