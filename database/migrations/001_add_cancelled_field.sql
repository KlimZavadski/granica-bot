-- Add cancelled field to journeys table
-- This migration adds ability to distinguish cancelled journeys from completed ones

-- Add cancelled column
ALTER TABLE journeys
ADD COLUMN IF NOT EXISTS cancelled BOOLEAN DEFAULT false;

-- Add index for querying non-cancelled completed journeys
CREATE INDEX IF NOT EXISTS idx_journeys_completed_not_cancelled
ON journeys(completed, cancelled)
WHERE completed = true AND cancelled = false;

-- Update notes for better tracking
COMMENT ON COLUMN journeys.cancelled IS 'Whether journey was cancelled by user (vs completed normally)';

