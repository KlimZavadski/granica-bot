-- DEV: Clear test journey data
-- ⚠️  WARNING: This will delete ALL journeys and events!
-- Use only during development for cleaning test data
--
-- This will also clear journey_events due to ON DELETE CASCADE

-- Clear journey_events first (optional, will be cleared by CASCADE anyway)
DELETE FROM journey_events;

-- Clear journeys
DELETE FROM journeys;

-- Verify
SELECT 'Journeys cleared: ' || COUNT(*) FROM journeys;
SELECT 'Events cleared: ' || COUNT(*) FROM journey_events;

