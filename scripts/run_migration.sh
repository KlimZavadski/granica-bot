#!/bin/bash
# Run database migration using psql

set -e

echo "🗄️  Database Migration Runner"
echo "============================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Source .env
export $(grep -v '^#' .env | xargs)

# Check if migration file is provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/run_migration.sh <migration_file>"
    echo ""
    echo "Available migrations:"
    ls -1 database/migrations/*.sql 2>/dev/null || echo "  (none found)"
    echo ""
    echo "Example:"
    echo "  ./scripts/run_migration.sh 001_add_cancelled_field.sql"
    exit 1
fi

MIGRATION_FILE="database/migrations/$1"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "📄 Migration file: $MIGRATION_FILE"
echo ""
echo "Preview:"
head -20 "$MIGRATION_FILE"
echo ""
echo "..."
echo ""

# Get Supabase connection details
echo "To run this migration, you need the PostgreSQL connection string from Supabase."
echo ""
echo "Steps:"
echo "1. Go to https://app.supabase.com"
echo "2. Select your project"
echo "3. Settings → Database"
echo "4. Copy 'Connection string' (Transaction mode)"
echo "5. Replace [YOUR-PASSWORD] with your database password"
echo ""
echo "Then run:"
echo ""
echo "  psql 'YOUR_CONNECTION_STRING' -f $MIGRATION_FILE"
echo ""
echo "Or use Supabase Dashboard SQL Editor (easier):"
echo "1. Copy contents of $MIGRATION_FILE"
echo "2. Paste in SQL Editor"
echo "3. Click Run"
echo ""

# Optionally try to run if SUPABASE_DB_URL is set
if [ ! -z "$SUPABASE_DB_URL" ]; then
    echo "Found SUPABASE_DB_URL in environment"
    read -p "Run migration now? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo ""
        echo "🔄 Running migration..."
        psql "$SUPABASE_DB_URL" -f "$MIGRATION_FILE"
        echo ""
        echo "✅ Migration completed!"
    fi
else
    echo "💡 Tip: Set SUPABASE_DB_URL in .env for automatic execution"
fi

