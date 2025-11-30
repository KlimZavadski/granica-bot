# GranicaBot — Engineering Rules for Cursor

All text visible for user must be in Russian.
Run migration scripts via `scripts/run_migration.sh <migration_file>`.

## Architecture
- The codebase is organized into layers:
  - `bot/` — FSM, handlers, routers.
  - `services/` — business logic.
  - `db/` — Supabase client and queries.
  - `agents/` — background jobs.
  - `core/` — models, utils, datetime functions.

- All Supabase interactions must go through the service layer.
- Do not mix business logic with Telegram handlers.

## Time Handling
- Always use UTC.
- Convert user input with:
  `datetime.fromisoformat(...).astimezone(timezone.utc)`.
- Store in DB as TIMESTAMP WITHOUT TIME ZONE.

## Naming
- Directories & files: snake_case
- Classes: PascalCase
- Functions: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE

## Code Style
- Use black + isort for formatting.
- Follow PEP8.
- Avoid wildcard imports.
- Use Python logging with INFO level.

## Telegram Bot (aiogram)
- Use aiogram 3.x.
- Keep FSM state in Redis or MemoryStorage.
- Each handler must be a pure function (no side effects).

## Data Validation
- All input must pass through Pydantic models.
- For checkpoint events:
  - Validate required checkpoints.
  - Validate ordering.
  - Log warnings on ordering violations.

## Error Handling
- For Supabase errors → log → retry if applicable.
- Never expose internal errors to users.
- Agents must never crash — fail softly.

## Security
- Store Telegram token in `.env`.
- Store Supabase keys in env variables only.
- Never log secrets.

## Testing
- Provide unit tests for:
  - timezone conversion
  - checkpoint ordering
  - analytics calculations

## Future-Proofing
- Checkpoints must be configurable via DB — not hardcoded.
- Agents must be configurable.
- All analytics code should live in a separate module.
