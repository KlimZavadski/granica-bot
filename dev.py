"""Development server with hot reload."""
import sys
import subprocess
import time
from pathlib import Path
from watchfiles import watch


def run_bot():
    """Run the bot process."""
    return subprocess.Popen([sys.executable, "bot.py"])


def main():
    """Watch for file changes and restart bot."""
    print("🔥 Hot reload enabled!")
    print("📁 Watching for changes in: *.py files")
    print("Press Ctrl+C to stop\n")

    process = run_bot()

    try:
        for changes in watch(".", recursive=True):
            # Filter only Python files
            py_changes = [c for c in changes if str(c[1]).endswith('.py')]

            if py_changes:
                print(f"\n🔄 Detected changes:")
                for change_type, path in py_changes:
                    print(f"  - {path}")

                print("♻️  Restarting bot...\n")

                # Kill old process
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

                # Start new process
                time.sleep(0.5)
                process = run_bot()

    except KeyboardInterrupt:
        print("\n\n👋 Stopping bot...")
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()

