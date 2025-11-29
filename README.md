# Granica Bot

Telegram bot for tracking border crossing times between Belarus and Poland/Lithuania.

## Features (MVP - Iteration 1)

- ✅ Track border crossing journeys with multiple checkpoints
- ✅ Support for multiple bus carriers (FlixBus, Ecolines, Lux Express, etc.)
- ✅ Automatic UTC timezone handling
- ✅ Sequential checkpoint validation
- ✅ Journey summaries with duration calculations
- ✅ Statistics on recent border crossings

## Tech Stack

- **Python 3.11+**
- **aiogram 3.x** - Telegram Bot framework
- **Supabase** - PostgreSQL database + backend
- **pytz** - Timezone handling

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- Supabase account
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 2. Installation

```bash
# Clone repository
cd granica-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
ENVIRONMENT=development
```

### 4. Database Setup

1. Go to your Supabase project
2. Navigate to SQL Editor
3. Run the schema from `database/schema.sql`

This will create:
- Tables: `carriers`, `routes`, `checkpoints`, `journeys`, `journey_events`
- Default checkpoints (7 mandatory border checkpoints)
- Sample carriers (FlixBus, Ecolines, etc.)

### 5. Run the Bot

**Production:**
```bash
python3 bot.py
```

**Development (with hot reload):**
```bash
# Option 1: Using dev script (recommended)
./scripts/dev.sh

# Option 2: Direct Python
python3 dev.py

# Option 3: Using watchfiles CLI
pip install watchfiles
watchfiles 'python3 bot.py' .
```

## Usage

### User Commands

- `/start` - Show welcome message and instructions
- `/new` - Start tracking a new journey
- `/stats` - View latest border crossing statistics
- `/cancel` - Cancel current journey

### Journey Flow

1. Choose bus carrier
2. Enter departure date (YYYY-MM-DD)
3. Enter departure time (HH:MM)
4. Record 7 mandatory checkpoints:
   - Approaching the border
   - Entering checkpoint #1
   - Invited to passport control #1
   - Leaving checkpoint #1 (neutral zone)
   - Entering checkpoint #2
   - Invited to passport control #2
   - Leaving checkpoint #2 (border exit)
5. View journey summary with durations

## Architecture

### Project Structure

```
granica-bot/
├── bot.py              # Main entry point
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── database/
│   ├── schema.sql     # Database schema
│   ├── db.py          # Database interface
│   └── __init__.py
├── handlers/
│   ├── journey.py     # Journey tracking handlers
│   ├── states.py      # FSM states
│   └── __init__.py
└── utils/
    ├── timezone.py    # Timezone utilities
    └── __init__.py
```

### Key Principles

1. **All timestamps in UTC** - User input is converted to UTC, stored as UTC, displayed in user's timezone
2. **Sequential validation** - Checkpoints must be recorded in order
3. **FSM-based flow** - Clean state management with aiogram FSM
4. **Idempotent operations** - Database operations can be safely retried

## Roadmap

### Iteration 2 (Planned)
- Automated bus schedule scraping
- GPS-based checkpoint detection
- Geofencing support

### Iteration 3 (Planned)
- Search by date/route
- Analytics graphs
- Statistical metrics (median, percentiles)

### Iteration 4 (Planned)
- Push notifications for border time changes
- User subscriptions
- Anomaly detection

## Development

### Adding New Checkpoints

Edit `database/schema.sql` and insert into `checkpoints` table:

```sql
INSERT INTO checkpoints (name, type, order_index, required) VALUES
    ('custom_checkpoint', 'optional', 100, false);
```

### Adding New Carriers

```sql
INSERT INTO carriers (name) VALUES ('New Carrier Name');
```

## Troubleshooting

### Bot doesn't respond
- Check if bot token is correct
- Verify bot is running (`python3 bot.py`)
- Check logs for errors

### Database connection issues
- Verify Supabase URL and key
- Check if tables are created
- Ensure network access to Supabase

### Timezone issues
- All times should be in UTC internally
- User input is converted from Europe/Minsk by default
- Check `utils/timezone.py` for conversion logic

## License

MIT

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.

## Support

For issues or questions, please open a GitHub issue.

