-- Add user_timezone field to journey_events to preserve timezone at the time of event creation
ALTER TABLE journey_events
ADD COLUMN IF NOT EXISTS user_timezone TEXT DEFAULT 'Europe/Minsk';

-- Add comment explaining the field
COMMENT ON COLUMN journey_events.user_timezone IS 'Timezone active at the time this event was recorded by the user';
