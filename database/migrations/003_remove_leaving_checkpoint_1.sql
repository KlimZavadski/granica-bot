-- Remove leaving_checkpoint_1 from mandatory checkpoints
-- Simplifies the journey tracking by removing intermediate checkpoint between two border controls

-- Mark as optional (not required) instead of deleting for data integrity
UPDATE checkpoints
SET required = false, type = 'optional'
WHERE name = 'leaving_checkpoint_1';

-- Update leaving_checkpoint_2 display order if needed
-- (keeping order_index as is for now to maintain data consistency)

-- Verify the changes
SELECT name, type, order_index, required
FROM checkpoints
ORDER BY order_index;

