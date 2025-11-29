#!/bin/bash
# Development server with hot reload

set -e

echo "🚀 Starting development server with hot reload..."
echo ""

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dev dependencies if watchfiles not found
if ! python3 -c "import watchfiles" 2>/dev/null; then
    echo "📦 Installing watchfiles for hot reload..."
    pip install watchfiles
    echo ""
fi

# Run dev server
python3 dev.py

