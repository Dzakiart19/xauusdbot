"""
Main Entry Point - Bot Initialization & Event Loop
"""

import asyncio
import os
import sys
from datetime import datetime
from flask import Flask, jsonify

# Import all modules
from config.settings import (
    TELEGRAM_BOT_TOKEN, APP_PORT, APP_HOST, print_config, EVALUATION_MODE
)
from data.db import init_db, SessionLocal
from utils.logger import get_logger, log_info, log_error
from config.strategy import StrategyEngine, RiskManager
from services.rest_poller import rest_poller

logger = get_logger()

# Flask app for health checks
app = Flask(__name__)

# Global state
bot_start_time = datetime.utcnow()
bot_status = "INITIALIZING"
api_health = {}

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Koyeb"""
    global api_health, bot_status
    
    uptime = (datetime.utcnow() - bot_start_time).total_seconds()
    
    response = {
        "status": bot_status,
        "uptime_seconds": int(uptime),
        "timestamp": datetime.utcnow().isoformat(),
        "evaluation_mode": EVALUATION_MODE,
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN),
    }
    
    is_healthy = bot_status in ["RUNNING", "HEALTHY"]
    status_code = 200 if is_healthy else 503
    
    return jsonify(response), status_code

@app.route("/status", methods=["GET"])
def get_status():
    """Get detailed bot status"""
    uptime = (datetime.utcnow() - bot_start_time).total_seconds()
    
    try:
        db = SessionLocal()
        from data.models import Trade, TradeStatus
        
        open_trades = db.query(Trade).filter(Trade.status == TradeStatus.OPEN).count()
        total_trades = db.query(Trade).count()
        
        # Calculate win rate
        closed_trades = db.query(Trade).filter(
            Trade.status.in_([TradeStatus.CLOSED_LOSE, TradeStatus.CLOSED_WIN])
        ).all()
        win_count = sum(1 for t in closed_trades if t.status == TradeStatus.CLOSED_WIN)
        win_rate = (win_count / len(closed_trades) * 100) if closed_trades else 0
        
        # Calculate total P/L
        total_pl = sum(t.virtual_pl_usd or 0 for t in closed_trades)
        
        db.close()
        
        return jsonify({
            "status": bot_status,
            "uptime_hours": round(uptime / 3600, 2),
            "evaluation_mode": EVALUATION_MODE,
            "trades": {
                "open": open_trades,
                "total": total_trades,
                "win_rate": round(win_rate, 2),
                "total_pl_usd": round(total_pl, 2)
            }
        }), 200
    except Exception as e:
        logger.error(f"Status endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def run_telegram_bot():
    """Run Telegram bot (blocking, should be in separate thread)"""
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        from telegram import Update
        
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot disabled.")
            return
        
        # Create application
        app_tg = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "👋 Welcome to XauScalp Sentinel!\n\n"
                "🤖 XAUUSD Trading Signal Bot (Evaluation Mode)\n\n"
                "Commands:\n"
                "/help - Show all commands\n"
                "/monitor - Subscribe to signals\n"
                "/status - Bot status\n"
            )
        
        async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "📚 Available Commands:\n\n"
                "/start - Welcome message\n"
                "/monitor - Subscribe to XAUUSD signals\n"
                "/status - View bot status\n"
                "/riwayat - View recent trades (default 10)\n"
                "/health - API health status\n\n"
                "Admin Commands (if authorized):\n"
                "/performa - Performance report\n"
                "/settings - Modify parameters\n"
            )
        
        async def monitor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "✅ Monitoring XAUUSD signals activated!\n\n"
                "You will receive notifications for:\n"
                "📈 BUY signals\n"
                "📉 SELL signals\n"
                "🎯 Trade closures\n\n"
                "Use /stopmonitor to unsubscribe."
            )
        
        async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            uptime = (datetime.utcnow() - bot_start_time).total_seconds() / 3600
            await update.message.reply_text(
                f"🤖 Bot Status Report\n\n"
                f"Status: {bot_status}\n"
                f"Uptime: {uptime:.1f}h\n"
                f"Eval Mode: {EVALUATION_MODE}\n"
                f"Mode: {'Evaluation' if EVALUATION_MODE else 'Production'}\n"
            )
        
        # Register handlers
        app_tg.add_handler(CommandHandler("start", start_handler))
        app_tg.add_handler(CommandHandler("help", help_handler))
        app_tg.add_handler(CommandHandler("monitor", monitor_handler))
        app_tg.add_handler(CommandHandler("status", status_handler))
        
        # Start polling
        logger.info("Starting Telegram bot polling...")
        app_tg.run_polling()
        
    except Exception as e:
        logger.error(f"Telegram bot error: {str(e)}")

async def main_loop():
    """Main async loop for signal generation and trade management"""
    global bot_status
    
    logger.info("Starting main trading loop...")
    bot_status = "RUNNING"
    
    db = SessionLocal()
    strategy = StrategyEngine(db)
    risk_manager = RiskManager(db)
    
    while True:
        try:
            # Fetch market data
            market_data_m1 = await rest_poller.get_market_data(timeframe="M1")
            market_data_m5 = await rest_poller.get_market_data(timeframe="M5")
            
            if market_data_m1:
                rest_poller.add_to_cache(market_data_m1, "M1")
            if market_data_m5:
                rest_poller.add_to_cache(market_data_m5, "M5")
            
            # Get cached data for analysis
            m1_data = rest_poller.get_cached_data("M1")
            m5_data = rest_poller.get_cached_data("M5")
            
            if m1_data and m5_data:
                # Prepare data for strategy
                analysis_data = {
                    "m1_closes": [d.get("close", 0) for d in m1_data],
                    "m1_highs": [d.get("high", 0) for d in m1_data],
                    "m1_lows": [d.get("low", 0) for d in m1_data],
                    "m1_volumes": [d.get("volume", 0) for d in m1_data],
                    "m5_closes": [d.get("close", 0) for d in m5_data],
                    "m5_highs": [d.get("high", 0) for d in m5_data],
                    "m5_lows": [d.get("low", 0) for d in m5_data],
                    "current_price": m1_data[-1].get("close", 0),
                    "bid": m1_data[-1].get("bid"),
                    "ask": m1_data[-1].get("ask"),
                    "timestamp": datetime.utcnow()
                }
                
                # Check risk conditions
                can_trade, reason = risk_manager.can_generate_signal()
                if not can_trade:
                    logger.warning(f"Trading paused: {reason}")
                else:
                    # Generate signal
                    signal = strategy.generate_signal(analysis_data)
                    if signal:
                        # Save signal to database
                        from data.models import Trade, TradeDirection
                        trade = Trade(
                            signal_id=signal["signal_id"],
                            direction=TradeDirection[signal["direction"]],
                            entry_price=signal["entry_price"],
                            sl_price=signal["sl_price"],
                            tp_price=signal["tp_price"],
                            signal_timestamp_utc=datetime.utcnow(),
                            confidence_score=signal["confidence_score"],
                        )
                        db.add(trade)
                        db.commit()
                        logger.info(f"Signal saved: {signal['signal_id']}")
                
                # Update open trades
                strategy.update_trades(analysis_data)
            
            # Sleep before next iteration (polling interval)
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Main loop error: {str(e)}")
            await asyncio.sleep(5)
    
    db.close()

def main():
    """Main entry point"""
    try:
        print("\n" + "="*60)
        print("🤖 XauScalp Sentinel - XAUUSD Trading Signal Bot")
        print("="*60 + "\n")
        
        # Initialize
        print_config()
        init_db()
        log_info("Bot initialization complete")
        
        # Run health check endpoint in Flask (non-blocking)
        import threading
        flask_thread = threading.Thread(
            target=lambda: app.run(host=APP_HOST, port=APP_PORT, debug=False, use_reloader=False),
            daemon=True
        )
        flask_thread.start()
        log_info(f"Health check endpoint started on {APP_HOST}:{APP_PORT}")
        
        # Run Telegram bot in separate thread
        tg_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        tg_thread.start()
        log_info("Telegram bot thread started")
        
        # Run main trading loop
        asyncio.run(main_loop())
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
        sys.exit(0)
    except Exception as e:
        log_error(f"Fatal error: {str(e)}", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
