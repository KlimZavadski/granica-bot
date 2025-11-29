-- Granica Bot Database Schema (Iteration 1 - MVP)
-- All timestamps are UTC (TIMESTAMP WITHOUT TIME ZONE)

-- Carriers (bus companies)
CREATE TABLE IF NOT EXISTS carriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- Routes
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    carrier_id UUID NOT NULL REFERENCES carriers(id),
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- Checkpoints (predefined border checkpoints)
CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('mandatory', 'optional')),
    order_index INTEGER NOT NULL,
    required BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
    UNIQUE(name, order_index)
);

-- Journeys (user trips)
CREATE TABLE IF NOT EXISTS journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL, -- Telegram user ID
    carrier_id UUID NOT NULL REFERENCES carriers(id),
    departure_utc TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
    completed BOOLEAN DEFAULT false,
    anomalous BOOLEAN DEFAULT false,
    notes TEXT
);

-- Journey Events (checkpoint timestamps)
CREATE TABLE IF NOT EXISTS journey_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    checkpoint_id UUID NOT NULL REFERENCES checkpoints(id),
    timestamp_utc TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual', 'gps', 'system')),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
    UNIQUE(journey_id, checkpoint_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_journeys_user_id ON journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_journeys_departure ON journeys(departure_utc);
CREATE INDEX IF NOT EXISTS idx_journey_events_journey_id ON journey_events(journey_id);
CREATE INDEX IF NOT EXISTS idx_journey_events_timestamp ON journey_events(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_routes_carrier ON routes(carrier_id);

-- Insert default mandatory checkpoints
INSERT INTO checkpoints (name, type, order_index, required) VALUES
    ('approaching_border', 'mandatory', 1, true),
    ('entering_checkpoint_1', 'mandatory', 2, true),
    ('invited_passport_control_1', 'mandatory', 3, true),
    ('leaving_checkpoint_1', 'mandatory', 4, true),
    ('entering_checkpoint_2', 'mandatory', 5, true),
    ('invited_passport_control_2', 'mandatory', 6, true),
    ('leaving_checkpoint_2', 'mandatory', 7, true)
ON CONFLICT (name, order_index) DO NOTHING;

-- Insert sample carriers
INSERT INTO carriers (name) VALUES
    ('FlixBus'),
    ('Ecolines'),
    ('Lux Express'),
    ('Simple Express'),
    ('Other')
ON CONFLICT (name) DO NOTHING;

