# Development Guide

## Hot Reload / Auto-restart

### Quick Start

```bash
# Recommended way
./scripts/dev.sh
```

This will:
- ✅ Auto-activate virtual environment
- ✅ Install watchfiles if needed
- ✅ Watch all `.py` files for changes
- ✅ Automatically restart bot on save

---

## Methods

### Method 1: Custom Dev Script (Recommended)

**Run:**
```bash
python3 dev.py
```

**Features:**
- Fast restarts
- Shows which files changed
- Filters only `.py` files
- Clean shutdown on Ctrl+C

**How it works:**
Uses `watchfiles` library to monitor filesystem changes and restart the bot process.

---

### Method 2: Watchfiles CLI

**Install:**
```bash
pip install watchfiles
```

**Run:**
```bash
watchfiles 'python3 bot.py' .
```

**Pros:** Simple one-liner
**Cons:** Less control over restart behavior

---

### Method 3: Nodemon (if you have Node.js)

**Install:**
```bash
npm install -g nodemon
```

**Run:**
```bash
nodemon --exec python3 bot.py --ext py
```

**Pros:** Popular tool, works well
**Cons:** Requires Node.js

---

### Method 4: Watchdog

**Install:**
```bash
pip install watchdog
```

**Create `watch.sh`:**
```bash
#!/bin/bash
watchmedo auto-restart --patterns="*.py" --recursive -- python3 bot.py
```

**Run:**
```bash
chmod +x watch.sh
./watch.sh
```

---

## Configuration

### Ignore Files

Edit `.watchignore` to exclude files/directories:

```
__pycache__/
*.pyc
venv/
.git/
*.log
```

### Custom Watch Patterns

Edit `dev.py` to watch specific patterns:

```python
# Watch only handlers and utils
for changes in watch("handlers", "utils", recursive=True):
    # ...
```

---

## Development Dependencies

Install all dev tools:

```bash
pip install -r requirements-dev.txt
```

This includes:
- `watchfiles` - Hot reload
- `black` - Code formatter
- `flake8` - Linter
- `mypy` - Type checker
- `pytest` - Testing framework

---

## Code Quality Tools

### Format Code

```bash
black .
```

### Lint Code

```bash
flake8 .
```

### Type Check

```bash
mypy .
```

### Run Tests

```bash
pytest
```

---

## Development Workflow

1. **Start dev server:**
   ```bash
   ./scripts/dev.sh
   ```

2. **Edit code** - bot auto-restarts on save

3. **Test changes** in Telegram

4. **Format & lint** before commit:
   ```bash
   black . && flake8 .
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: your feature"
   ```

---

## Debugging

### Enable Debug Logging

Edit `bot.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Use Python Debugger

Add breakpoint in code:

```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with launch configuration.

---

## VS Code Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Bot",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/bot.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    },
    {
      "name": "Python: Dev (Hot Reload)",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/dev.py",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Troubleshooting

### Bot doesn't restart
- Check if watchfiles is installed: `pip list | grep watchfiles`
- Try restarting dev script
- Check file permissions

### Multiple bot instances running
- Make sure to stop old instance: `pkill -f bot.py`
- Use dev script which handles cleanup

### Changes not detected
- Check `.watchignore` isn't blocking files
- Try saving file again (Cmd/Ctrl+S)
- Verify file path is correct

---

## Production vs Development

| Feature | Development | Production |
|---------|-------------|------------|
| Run command | `./scripts/dev.sh` | `python3 bot.py` |
| Hot reload | ✅ Yes | ❌ No |
| Debug logging | ✅ Enabled | ⚠️ Minimal |
| Auto-restart | ✅ On save | ⚠️ On crash |
| Performance | Normal | Optimized |

---

## Tips

1. **Use hot reload** during active development
2. **Test without hot reload** before deploying
3. **Keep dev dependencies separate** (`requirements-dev.txt`)
4. **Format on save** in your editor
5. **Run tests** before committing
6. **Use environment variables** for different configs

---

## Next Steps

- Add unit tests in `tests/`
- Setup CI/CD pipeline
- Configure pre-commit hooks
- Add integration tests

See `TESTING.md` (coming soon) for testing guide.

