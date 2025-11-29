#!/usr/bin/env python3
"""Run database migrations locally."""
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def run_migration(migration_file: str):
    """Run a specific migration file."""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    # Read migration file
    migration_path = Path(__file__).parent.parent / "database" / "migrations" / migration_file

    if not migration_path.exists():
        print(f"❌ Error: Migration file not found: {migration_path}")
        return False

    print(f"📄 Reading migration: {migration_file}")
    with open(migration_path, 'r') as f:
        sql = f.read()

    print(f"📝 SQL preview:\n{sql[:200]}...\n")

    # Confirm
    response = input("⚠️  Run this migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        return False

    try:
        # Create Supabase client
        client = create_client(supabase_url, supabase_key)

        print("🔄 Running migration...")

        # Note: Supabase Python client doesn't support raw SQL execution
        # This is a limitation - need to use Dashboard or psql for DDL
        print("\n⚠️  Note: Python Supabase client doesn't support DDL operations.")
        print("Please use one of these methods instead:")
        print("\n1️⃣  Supabase Dashboard:")
        print("   - Go to SQL Editor")
        print("   - Paste the SQL above")
        print("   - Click Run")
        print("\n2️⃣  psql command:")
        print("   - Get connection string from Supabase Settings → Database")
        print(f"   - Run: psql 'YOUR_CONNECTION_STRING' -f {migration_path}")
        print("\n3️⃣  Supabase CLI:")
        print("   - Install: brew install supabase/tap/supabase")
        print("   - Link: supabase link --project-ref YOUR_PROJECT_REF")
        print(f"   - Run: supabase db push")

        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def list_migrations():
    """List all available migrations."""
    migrations_dir = Path(__file__).parent.parent / "database" / "migrations"

    if not migrations_dir.exists():
        print("❌ No migrations directory found")
        return

    migrations = sorted([f.name for f in migrations_dir.glob("*.sql")])

    if not migrations:
        print("📋 No migrations found")
        return

    print("📋 Available migrations:\n")
    for i, migration in enumerate(migrations, 1):
        print(f"  {i}. {migration}")
    print()


def main():
    """Main entry point."""
    print("=" * 60)
    print("🗄️  Database Migration Tool")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/migrate.py list          - List migrations")
        print("  python3 scripts/migrate.py 001_name.sql  - View migration")
        print()
        print("Note: For Supabase, use Dashboard or psql to run migrations")
        print()
        list_migrations()
        return

    command = sys.argv[1]

    if command == "list":
        list_migrations()
    else:
        # Assume it's a migration file
        run_migration(command)


if __name__ == "__main__":
    main()

