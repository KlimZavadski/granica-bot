Below is a **clean, production-ready AGENTS.md** description for your repository.
It defines **all system agents**, their responsibilities, workflows, triggers, data contracts, and safety rules.

You can drop this file directly into your repo.

---

# **AGENTS.md**

# GranicaBot — Autonomous Agents Specification

This document describes the autonomous agents powering GranicaBot.
Agents handle background processing, analytics, scraping, notifications, and geolocation inference.
Each agent is designed to operate deterministically, idempotently, and in full UTC.

---

# **1. Principles**

All agents must follow these core rules:

1. **Deterministic state transitions**

   * No random behavior.
   * Same input → same output.

2. **All timestamps in UTC**

   * Never store local time.
   * Convert on input, normalize on write.

3. **Idempotent operations**

   * Re-running an agent must produce the same resulting state.

4. **Graceful failure**

   * Log errors.
   * Never crash the system.
   * Retry where applicable.

5. **Data validation before write**

   * Validate all input (scraped data, GPS events, user data).

6. **Never delete user data**

   * Errors are marked as anomalies, not removed.

7. **Separation of concerns**

   * Agents do not interact with Telegram directly.
   * They communicate via Supabase tables and flags.

---

# **2. Agents Overview**

GranicaBot uses the following agents:

| Agent                           | Purpose                                           |
| ------------------------------- | ------------------------------------------------- |
| **Schedule Fetch Agent**        | Collects & normalizes bus schedules.              |
| **GPS Inference Agent**         | Matches user coordinates to border checkpoints.   |
| **Analytics Aggregation Agent** | Computes statistics and cached analytics.         |
| **Alert Trigger Agent**         | Sends notifications based on time deviations.     |
| **Data Integrity Agent**        | Ensures DB consistency and validates event flows. |
| **Cleanup/Archival Agent**      | Archives old analytics and optimizes storage.     |

---

# **3. Agents in Detail**

---

## **3.1. Schedule Fetch Agent**

**Purpose:**
Continuously import, normalize, and store bus schedules from carriers’ websites or APIs.

**Trigger:**

* Periodic (every 2–4 hours)
* Manual admin trigger

**Inputs:**

* HTML/JSON pages from carriers
* Existing schedule entries in DB

**Outputs:**

* `schedules` table rows
* Updated `carrier` metadata
* Logs of parsing errors

**Responsibilities:**

* Scrape or fetch schedule sources.
* Normalize to unified structure:

  * carrier_id
  * origin/destination
  * departure_time_utc
* Deduplicate using:

  * carrier_id + departure_time_utc + direction
* If schedule source is down → retry 3 times → log failure.

**Validation Rules:**

* Reject entries where UTC time conflicts with historical values.
* Reject entries with missing carrier or malformed routes.

---

## **3.2. GPS Inference Agent**

**Purpose:**
Convert user GPS coordinates into automatic checkpoint events.

**Trigger:**

* Every time a user shares location
* Background polling (if enabled)

**Inputs:**

* User lat/lon
* Geofence definitions (from DB)
* Active journeys

**Outputs:**

* `journey_events` (auto-generated)
* Flags for journey progress
* Anomaly markers if data is inconsistent

**Responsibilities:**

* Detect if coordinates fall into known border areas:

  * border approach
  * checkpoint #1
  * neutral zone
  * checkpoint #2
* For each matched geofence, create an event only if:

  * previous checkpoint exists
  * timestamp > last checkpoint
  * not already recorded (idempotency)

**Noise Handling:**

* Ignore if user moves too fast/unrealistically.
* Ignore points < minimal distance threshold.
* Apply smoothing filter (median of last N points).

**Validation Rules:**

* If GPS-derived timestamp < departure → mark anomaly.
* If checkpoint order is broken → log and skip creation.

---

## **3.3. Analytics Aggregation Agent**

**Purpose:**
Compute time-related metrics for border crossing.

**Trigger:**

* Periodic (every 10–30 minutes)
* After a batch of journeys completes

**Inputs:**

* All completed journeys
* Their events

**Outputs:**

* `analytics_cached` table entries
* Precomputed metrics for dashboards

**Metrics Calculated:**

* Total border crossing duration
* Time at each checkpoint
* Statistical metrics:

  * mean
  * median
  * p50
  * p90
  * p99

**Responsibilities:**

* Group journeys by:

  * direction
  * checkpoint → checkpoint delta
  * date
* Calculate rolling averages (6h, 12h, daily).
* Store aggregated values in cache table.

**Validation Rules:**

* Require minimum sample size (≥ 5 journeys).
* Exclude journeys marked “anomalous”.
* Exclude durations above extreme thresholds unless consistent.

---

## **3.4. Alert Trigger Agent**

**Purpose:**
Notify users when border crossing time significantly increases or decreases.

**Trigger:**

* After new analytics aggregation
* Periodic (hourly)

**Inputs:**

* Cached analytics
* User subscriptions
* Historical baselines

**Outputs:**

* Notifications (queued, not sent directly)
* Log entries

**Trigger Conditions Example:**

* p50 or p90 deviates from the 12h moving average by X%
* Spike persists longer than 1 measurement cycle
* Sample size ≥ required threshold

**Responsibilities:**

* Detect deviations:

  * increase in wait times
  * decrease in wait times
* Prevent false positives:

  * require stable trend
  * skip if sample size too small
  * skip if anomalies dominate dataset
* Queue messages to users who:

  * opted-in
  * match specific route/direction

**Validation Rules:**

* Never notify based on single outlier.
* Never send more than N alerts per day per user.

---

## **3.5. Data Integrity Agent**

**Purpose:**
Ensure data consistency across the DB.

**Trigger:**

* Periodic (daily)
* Manual admin trigger

**Inputs:**

* All tables

**Outputs:**

* Corrected statuses
* Logged anomalies
* Cleanup queue entries

**Responsibilities:**

* Check sequential ordering of checkpoints per journey.
* Detect and flag:

  * duplicated events
  * reversed timestamps
  * inconsistent geolocation jumps
  * missing mandatory checkpoints
* Soft-correct:

  * reorder events if possible
  * merge small duplicates
* Mark questionable entries with `anomalous=true`.

**Validation Rules:**

* Never delete user data.
* Never override timestamps.
* Only add metadata or flags.

---

## **3.6. Cleanup / Archival Agent**

**Purpose:**
Reduce DB load and maintain long-term performance.

**Trigger:**

* Weekly
* On-demand

**Inputs:**

* Completed journeys
* Old analytics

**Outputs:**

* Archived data to cold storage
* Compact tables in Supabase

**Responsibilities:**

* Move old journeys (> X months) to:

  * cold storage bucket
  * lightweight archive tables
* Clean temporary tables and caches.
* Back up analytics and logs.

---

# **4. Data Contracts**

All agents must adhere to unified schemas:

### **Timestamps**

* `timestamp_utc`: RFC3339, UTC only
* No local offsets allowed
* Only `TIMESTAMP WITHOUT TIME ZONE` in DB

### **Geolocation**

* `lat`, `lon` as floats
* If accuracy provided → use for validation

### **Anomalies**

* `anomalous` boolean
* `notes` text field for debugging

### **Events**

All journey events must contain:

* journey_id
* checkpoint_id
* timestamp_utc
* source: “manual” | “gps” | “system”

---

# **5. Operational Safety**

* Agents must never block bot operation.
* All agent failures must log with full traceback.
* No agent may ever override:

  * user manually entered checkpoint times
  * journey identifiers
  * historical analytics
* Agents must support graceful restart.

---

# **6. Versioning & Migration**

* Each agent has its own version tag:
  `AGENT_NAME_VERSION`
* On schema migration:

  * increase agent version
  * run migration script
  * perform dry-run validation

---

If you'd like, I can also generate:

✅ `agents/` folder structure
✅ ready-to-run Python stubs for each agent
✅ Supabase SQL migrations
✅ integration flow diagrams (Mermaid)
Just tell me.
