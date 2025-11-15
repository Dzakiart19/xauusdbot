## CHANGELOG - XauScalp Sentinel

### Version 1.0.0-EVAL (2025-11-15)
**Initial Release - Evaluation Build**

#### Features
- ✅ Multi-timeframe signal generation (M1/M5)
- ✅ Multi-indicator confirmation (EMA, RSI, Stochastic)
- ✅ Risk management layer with daily loss limits
- ✅ Evaluation Mode for unrestricted testing
- ✅ Telegram bot interface with real-time signals
- ✅ Virtual trading with P/L simulation
- ✅ SQLite database for trade history
- ✅ REST API for market data with failover
- ✅ Health check endpoint for Koyeb deployment
- ✅ Comprehensive logging and error handling

#### Components
1. **Strategy Engine** - Signal generation with 5-component confidence scoring
2. **Risk Manager** - Position controls and daily loss limits
3. **Indicator Calculator** - Technical analysis (EMA, RSI, Stochastic, ATR)
4. **REST Poller** - Multi-provider market data fetching
5. **Telegram Bot** - User interface and notifications
6. **Database** - SQLite with SQLAlchemy ORM
7. **Backtester** - CSV replay for strategy testing

#### Known Limitations (Evaluation Build)
- WebSocket data stream not yet implemented (REST polling only)
- Chart generation not yet integrated
- Multi-language support limited to English
- Manual trade execution required (signal provider only)

#### Testing
- Run unit tests: `python -m pytest tests/`
- Run backtester: `python backtester.py --data xauusd_m1.csv`
- Enable evaluation mode: `EVALUATION_MODE=true`

---

### Planned for v1.1.0
- [ ] WebSocket real-time data stream
- [ ] Chart generation and display
- [ ] Performance dashboard
- [ ] Multi-language Telegram interface
- [ ] News impact filtering
- [ ] Advanced statistics and reporting

### Deployment Notes
- **Replit:** Use `.replit` config for easy deployment
- **Koyeb:** Docker container ready, set environment variables in dashboard
- **Local:** `python main.py` after `pip install -r requirements.txt`

---

For detailed setup instructions, see `README.md`.
