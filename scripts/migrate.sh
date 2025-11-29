#!/bin/bash
# Database migration helper script

set -e

echo "🗄️  Granica Bot - Database Migration"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Please create .env file with your Supabase credentials"
    exit 1
fi

# Load .env
export $(grep -v '^#' .env | xargs)

echo "📋 Migration options:"
echo ""
echo "1. Copy schema.sql content (paste into Supabase Dashboard)"
echo "2. Show connection instructions"
echo "3. Show schema.sql contents"
echo ""
read -p "Choose option (1-3): " option

case $option in
    1)
        echo ""
        echo "✂️  Copying schema.sql to clipboard..."
        if command -v pbcopy &> /dev/null; then
            cat database/schema.sql | pbcopy
            echo "✅ Schema copied to clipboard!"
            echo ""
            echo "Next steps:"
            echo "1. Go to: https://app.supabase.com"
            echo "2. Select your project"
            echo "3. Click 'SQL Editor' in sidebar"
            echo "4. Paste and click 'Run'"
        else
            echo "⚠️  pbcopy not available"
            echo "Please manually copy database/schema.sql contents"
        fi
        ;;
    2)
        echo ""
        echo "📡 Connection Instructions:"
        echo ""
        echo "Method 1: Supabase Dashboard (Recommended)"
        echo "  1. Go to https://app.supabase.com"
        echo "  2. Select your project"
        echo "  3. Click 'SQL Editor'"
        echo "  4. Paste database/schema.sql contents"
        echo "  5. Click 'Run'"
        echo ""
        echo "Method 2: Using psql"
        echo "  Install: brew install libpq"
        echo "  Get connection string from Dashboard → Settings → Database"
        echo "  Run: psql 'YOUR_CONNECTION_STRING' -f database/schema.sql"
        echo ""
        echo "Method 3: Supabase CLI"
        echo "  Install: brew install supabase/tap/supabase"
        echo "  Link: supabase link --project-ref YOUR_PROJECT_REF"
        echo "  Run: supabase db push"
        echo ""
        ;;
    3)
        echo ""
        echo "📄 Schema contents:"
        echo "=================="
        cat database/schema.sql
        echo ""
        echo "=================="
        echo "Copy this and paste into Supabase SQL Editor"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"

