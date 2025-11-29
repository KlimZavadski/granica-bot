"""Test script to verify setup is correct."""
import sys
from datetime import datetime


def test_imports():
    """Test if all required packages are installed."""
    print("Testing imports...")
    try:
        import aiogram
        print(f"✅ aiogram {aiogram.__version__}")
    except ImportError as e:
        print(f"❌ aiogram not installed: {e}")
        return False

    try:
        import supabase
        print("✅ supabase")
    except ImportError as e:
        print(f"❌ supabase not installed: {e}")
        return False

    try:
        import pytz
        print("✅ pytz")
    except ImportError as e:
        print(f"❌ pytz not installed: {e}")
        return False

    try:
        import dotenv
        print("✅ python-dotenv")
    except ImportError as e:
        print(f"❌ python-dotenv not installed: {e}")
        return False

    return True


def test_config():
    """Test if configuration is valid."""
    print("\nTesting configuration...")
    try:
        from config import settings

        if not settings.telegram_bot_token or settings.telegram_bot_token == "your_bot_token_here":
            print("❌ TELEGRAM_BOT_TOKEN not set in .env")
            return False
        print("✅ TELEGRAM_BOT_TOKEN is set")

        if not settings.supabase_url or settings.supabase_url == "your_supabase_url_here":
            print("❌ SUPABASE_URL not set in .env")
            return False
        print("✅ SUPABASE_URL is set")

        if not settings.supabase_key or settings.supabase_key == "your_supabase_anon_key_here":
            print("❌ SUPABASE_KEY not set in .env")
            return False
        print("✅ SUPABASE_KEY is set")

        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_database():
    """Test database connection."""
    print("\nTesting database connection...")
    try:
        from database import db

        # Try to get carriers
        carriers = db.client.table("carriers").select("*").limit(1).execute()
        print(f"✅ Database connection successful")
        print(f"✅ Found {len(carriers.data)} carrier(s) in database")

        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure you've run database/schema.sql in Supabase")
        return False


def test_timezone():
    """Test timezone utilities."""
    print("\nTesting timezone utilities...")
    try:
        from utils import now_utc, parse_user_datetime, format_datetime_for_user

        # Test now_utc
        now = now_utc()
        print(f"✅ Current UTC time: {now}")

        # Test parsing
        test_dt = parse_user_datetime("2024-11-29", "14:30", "Europe/Minsk")
        print(f"✅ Parsed datetime: {test_dt}")

        # Test formatting
        formatted = format_datetime_for_user(test_dt, "Europe/Minsk")
        print(f"✅ Formatted datetime: {formatted}")

        return True
    except Exception as e:
        print(f"❌ Timezone utilities error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Granica Bot - Setup Verification")
    print("=" * 50)
    print()

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Database", test_database()))
    results.append(("Timezone", test_timezone()))

    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(result[1] for result in results)

    print()
    if all_passed:
        print("🎉 All tests passed! You're ready to run the bot.")
        print("\nStart the bot with: python3 bot.py")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

