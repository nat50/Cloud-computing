-- Created by infra/setup.sh. __DATASET__ is replaced with project.dataset.

-- One row per frame. Pub/Sub delivers at least once, so `detections` can hold
-- the same frame_id more than once; this view keeps the first result.
CREATE OR REPLACE VIEW `__DATASET__.detections_dedup` AS
SELECT * EXCEPT (rn)
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY frame_id ORDER BY processed_at) AS rn
  FROM `__DATASET__.detections`
)
WHERE rn = 1;

-- Every frame the producer published (written by the frames-audit BigQuery subscription).
CREATE OR REPLACE VIEW `__DATASET__.frames_published_v` AS
SELECT
  JSON_VALUE(data, '$.frame_id') AS frame_id,
  JSON_VALUE(data, '$.camera_id') AS camera_id,
  publish_time,
  message_id
FROM `__DATASET__.frames_published`;

-- Frames that failed 5 deliveries (written by the dlq-audit BigQuery subscription).
CREATE OR REPLACE VIEW `__DATASET__.dead_letters_v` AS
SELECT
  JSON_VALUE(data, '$.frame_id') AS frame_id,
  JSON_VALUE(data, '$.gcs_uri') AS gcs_uri,
  SAFE_CAST(JSON_VALUE(attributes, '$.CloudPubSubDeadLetterSourceDeliveryCount') AS INT64) AS delivery_count,
  publish_time AS dead_lettered_at
FROM `__DATASET__.dead_letters`;
