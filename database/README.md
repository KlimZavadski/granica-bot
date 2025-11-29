# Database Migrations

## Quick Setup (Dashboard)

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Click **SQL Editor** in sidebar
4. Copy & paste contents of `schema.sql`
5. Click **Run**

---

## Using Supabase CLI

### Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# Or with npm
npm install -g supabase
```

### Initialize Supabase in Project

```bash
# Link to your cloud project
supabase link --project-ref your-project-ref

# Your project ref is in the URL:
# https://app.supabase.com/project/YOUR-PROJECT-REF
```

### Run Migration

```bash
# Execute schema against linked project
supabase db push
```

### Alternative: Direct SQL Execution

```bash
# Execute schema.sql directly
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" < database/schema.sql
```

---

## Using psql (PostgreSQL Client)

### Install psql

```bash
# macOS
brew install libpq
brew link --force libpq

# Ubuntu/Debian
sudo apt install postgresql-client
```

### Get Connection String

1. Go to Supabase Dashboard
2. Settings → Database
3. Copy **Connection string** (Transaction mode)
4. Replace `[YOUR-PASSWORD]` with your database password

### Run Migration

```bash
psql "postgresql://postgres:YOUR-PASSWORD@db.YOUR-PROJECT-REF.supabase.co:5432/postgres" -f database/schema.sql
```

---

## Using Python Script

Create a migration script:

```python
# migrate.py
from supabase import create_client
from config import settings

def run_migration():
    client = create_client(settings.supabase_url, settings.supabase_key)

    with open('database/schema.sql', 'r') as f:
        sql = f.read()

    # Note: This requires service_role key, not anon key
    # Get it from Settings → API → service_role key
    response = client.rpc('exec_sql', {'query': sql}).execute()
    print("Migration completed!")

if __name__ == "__main__":
    run_migration()
```

⚠️ **Warning**: Direct SQL execution via Python requires `service_role` key with elevated permissions.

---

## Verify Migration

After running schema.sql, verify tables were created:

```sql
-- Run in SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

Expected tables:
- carriers
- routes
- checkpoints
- journeys
- journey_events

---

## Rollback (if needed)

If you need to start fresh:

```sql
-- ⚠️ DANGER: This drops all tables and data
DROP TABLE IF EXISTS journey_events CASCADE;
DROP TABLE IF EXISTS journeys CASCADE;
DROP TABLE IF EXISTS checkpoints CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS carriers CASCADE;
```

Then re-run `schema.sql`.

---

## Best Practices

1. **Always backup** before running migrations in production
2. **Test migrations** in a dev/staging project first
3. **Version your migrations** (e.g., `001_initial.sql`, `002_add_analytics.sql`)
4. Use **Supabase Migrations** feature for team collaboration
5. Never commit production credentials

---

## Troubleshooting

### "Table already exists"
- Comment out `CREATE TABLE` statements for existing tables
- Or add `IF NOT EXISTS` (already in schema.sql)

### "Permission denied"
- Using `anon` key won't work for DDL operations
- Use Dashboard SQL Editor or `service_role` key

### "Connection refused"
- Check your database password
- Verify project is not paused (free tier pauses after inactivity)
- Check IP allowlist in Database Settings

---

## Next Steps

After migration:
1. Run `python3 test_setup.py` to verify connection
2. Check that default data was inserted (carriers, checkpoints)
3. Start the bot with `python3 bot.py`

