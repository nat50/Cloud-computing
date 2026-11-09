-- Paste into the BigQuery console. Set run_id to the value the producer printed.
-- Wait ~1 minute after the run: the export subscriptions write with a small delay.
-- Replace PROJECT_ID.yolo_pipeline with your dataset.

DECLARE run_id STRING DEFAULT '20261109-101010';

WITH
pub AS (
  SELECT DISTINCT frame_id FROM `PROJECT_ID.yolo_pipeline.frames_published_v`
  WHERE frame_id LIKE CONCAT('%-', run_id, '-%')
),
det AS (
  SELECT frame_id, COUNT(*) AS n FROM `PROJECT_ID.yolo_pipeline.detections`
  WHERE frame_id LIKE CONCAT('%-', run_id, '-%')
  GROUP BY frame_id
),
dead AS (
  SELECT DISTINCT frame_id FROM `PROJECT_ID.yolo_pipeline.dead_letters_v`
  WHERE frame_id LIKE CONCAT('%-', run_id, '-%')
)
SELECT
  (SELECT COUNT(*) FROM pub) AS published,
  (SELECT COUNT(*) FROM det) AS processed,
  (SELECT IFNULL(SUM(n), 0) FROM det) AS raw_rows,
  (SELECT COUNTIF(n > 1) FROM det) AS frames_written_twice,  -- at-least-once in action; the dedup view hides these
  (SELECT COUNT(*) FROM dead) AS dead_lettered,
  (SELECT COUNT(*) FROM pub
     WHERE frame_id NOT IN (SELECT frame_id FROM det)
       AND frame_id NOT IN (SELECT frame_id FROM dead)) AS lost;  -- must be 0
