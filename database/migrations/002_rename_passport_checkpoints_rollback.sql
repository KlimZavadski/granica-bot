-- Rollback for 002_rename_passport_checkpoints.sql
-- Reverts checkpoint names back to "invited"

-- Revert checkpoint #1 passport control
UPDATE checkpoints
SET name = 'invited_passport_control_1'
WHERE name = 'passed_passport_control_1';

-- Revert checkpoint #2 passport control
UPDATE checkpoints
SET name = 'invited_passport_control_2'
WHERE name = 'passed_passport_control_2';

-- Verify the rollback
SELECT name, type, order_index, required
FROM checkpoints
WHERE name LIKE '%passport_control%'
ORDER BY order_index;

