#!/bin/bash
# Quick Start Script for XauScalp Sentinel
# Usage: bash quickstart.sh

set -e  # Exit on error

echo "================================"
echo "🤖 XauScalp Sentinel - Quick Start"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python -c "from data.db import init_db; init_db(); print('✓ Database initialized')"

# Create directories
mkdir -p data/charts logs

# Display next steps
echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Configure environment:"
echo "   cp .env.example .env"
echo "   # Edit .env and add TELEGRAM_BOT_TOKEN"
echo ""
echo "2. Run the bot:"
echo "   python main.py"
echo ""
echo "3. Or run in Evaluation Mode (for testing):"
echo "   EVALUATION_MODE=true python main.py"
echo ""
echo "4. For backtesting:"
echo "   python backtester.py --data your_data.csv"
echo ""
echo "5. For tests:"
echo "   python -m pytest tests/ -v"
echo ""
echo "📚 Documentation:"
echo "   - SETUP.md         → Detailed setup & deployment guide"
echo "   - README.md        → Full technical specification"
echo "   - STRUCTURE.md     → Project structure & architecture"
echo ""
echo "🌐 Health Check (after starting bot):"
echo "   curl http://localhost:8080/health"
echo ""
