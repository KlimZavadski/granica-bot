-- Rename passport control checkpoints from "invited" to "passed"
-- This migration updates checkpoint names to better reflect when time should be recorded

-- Update checkpoint #1 passport control
UPDATE checkpoints
SET name = 'passed_passport_control_1'
WHERE name = 'invited_passport_control_1';

-- Update checkpoint #2 passport control
UPDATE checkpoints
SET name = 'passed_passport_control_2'
WHERE name = 'invited_passport_control_2';

-- Verify the changes
SELECT name, type, order_index, required
FROM checkpoints
WHERE name LIKE '%passport_control%'
ORDER BY order_index;

