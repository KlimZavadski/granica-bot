#!/bin/bash
# Setup script for Granica Bot

echo "🤖 Granica Bot Setup"
echo "===================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "📝 Please create .env file with your credentials:"
    echo ""
    echo "TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "SUPABASE_URL=your_supabase_url"
    echo "SUPABASE_KEY=your_supabase_key"
    echo "ENVIRONMENT=development"
    echo ""
else
    echo "✅ .env file found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create .env file with your credentials (if not done)"
echo "2. Run database/schema.sql in your Supabase SQL Editor"
echo "3. Start the bot: python bot.py"
echo ""

