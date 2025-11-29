# Quick Start Guide

Get Granica Bot running in 5 minutes.

## Step 1: Get Your Credentials

### Telegram Bot Token
1. Open Telegram
2. Search for [@BotFather](https://t.me/botfather)
3. Send `/newbot`
4. Follow instructions to create your bot
5. Copy the token (looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

### Supabase Credentials
1. Go to [supabase.com](https://supabase.com)
2. Create a new project (or use existing)
3. Go to Settings → API
4. Copy:
   - Project URL (e.g., `https://xxxxx.supabase.co`)
   - `anon` `public` key (long string starting with `eyJ...`)

---

## Step 2: Setup Project

```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 3: Configure

Create `.env` file:

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

Add your credentials:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ENVIRONMENT=development
```

---

## Step 4: Setup Database

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Open `database/schema.sql` from this project
4. Copy all content
5. Paste in Supabase SQL Editor
6. Click "RUN"

You should see:
- ✅ Tables created
- ✅ Indexes created
- ✅ Default data inserted

---

## Step 5: Test Setup

```bash
python3 test_setup.py
```

Expected output:
```
✅ aiogram
✅ supabase
✅ pytz
✅ python-dotenv
✅ TELEGRAM_BOT_TOKEN is set
✅ SUPABASE_URL is set
✅ SUPABASE_KEY is set
✅ Database connection successful
🎉 All tests passed!
```

---

## Step 6: Run the Bot

```bash
python3 bot.py
```

You should see:
```
INFO - Starting Granica Bot...
INFO - Environment: development
```

---

## Step 7: Test in Telegram

1. Open Telegram
2. Search for your bot (use the username you set with BotFather)
3. Send `/start`
4. Follow the flow!

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Connection refused" (Supabase)
- Check SUPABASE_URL is correct
- Check SUPABASE_KEY is correct
- Verify your Supabase project is active

### "Unauthorized" (Telegram)
- Check TELEGRAM_BOT_TOKEN is correct
- Make sure you copied the full token from BotFather

### "Table doesn't exist"
- Run `database/schema.sql` in Supabase SQL Editor
- Check for errors in the SQL execution

### Bot doesn't respond
- Make sure bot is running (`python3 bot.py`)
- Check terminal for error messages
- Try `/start` command again

---

## Next Steps

Once working:

1. **Track a journey**: Use `/new` to start
2. **View stats**: Use `/stats` to see data
3. **Deploy**: See `DEPLOYMENT.md` for production setup
4. **Customize**: Edit handlers to add features

---

## Common Commands

```bash
# Start bot
python3 bot.py

# Run tests
python3 test_setup.py

# Update dependencies
pip install --upgrade -r requirements.txt

# View bot in Telegram
# Search for: @your_bot_username
```

---

## Support

Issues? Check:
- README.md - Full documentation
- DEPLOYMENT.md - Production setup
- GitHub Issues - Known problems

---

**That's it! You're ready to track border crossings.** 🚌🛂

