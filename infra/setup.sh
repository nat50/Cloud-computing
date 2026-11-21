#!/usr/bin/env bash
# Create everything except the GKE cluster. Safe to re-run (existing resources are skipped).
# Costs ~0 while no cluster is running.
#   bash infra/setup.sh
source "$(dirname "$0")/lib.sh"
trap 'rm -f "$ROOT/.tmp-lifecycle.json" "$ROOT/.tmp-dashboard.json"' EXIT
PUBSUB_AGENT="service-$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')@gcp-sa-pubsub.iam.gserviceaccount.com"

step "Enable APIs"
gcloud services enable pubsub.googleapis.com storage.googleapis.com bigquery.googleapis.com \
  container.googleapis.com artifactregistry.googleapis.com monitoring.googleapis.com

step "Bucket gs://$BUCKET (images auto-deleted after 7 days)"
exists gcloud storage buckets describe "gs://$BUCKET" ||
  gcloud storage buckets create "gs://$BUCKET" --location="$REGION" --uniform-bucket-level-access
echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":7}}]}' > "$ROOT/.tmp-lifecycle.json"
gcloud storage buckets update "gs://$BUCKET" --lifecycle-file="$ROOT/.tmp-lifecycle.json"
rm -f "$ROOT/.tmp-lifecycle.json"

step "Topics $TOPIC, $DLQ_TOPIC"
for t in "$TOPIC" "$DLQ_TOPIC"; do exists gcloud pubsub topics describe "$t" || gcloud pubsub topics create "$t"; done

step "BigQuery dataset $DATASET: tables and views"
exists bq show "$PROJECT_ID:$DATASET" || bq --location="$REGION" mk --dataset "$PROJECT_ID:$DATASET"
exists bq show "$PROJECT_ID:$DATASET.detections" ||
  bq mk --table --time_partitioning_field=processed_at "$PROJECT_ID:$DATASET.detections" "$ROOT/infra/bigquery/detections.json"
for t in frames_published dead_letters; do
  exists bq show "$PROJECT_ID:$DATASET.$t" ||
    bq mk --table --time_partitioning_field=publish_time "$PROJECT_ID:$DATASET.$t" "$ROOT/infra/bigquery/pubsub_export.json"
done
sed "s|__DATASET__|$PROJECT_ID.$DATASET|g" "$ROOT/infra/bigquery/views.sql" | bq query --use_legacy_sql=false --quiet >/dev/null

step "Pub/Sub's own service account: may write to BigQuery and publish dead letters"
gcloud beta services identity create --service=pubsub.googleapis.com >/dev/null 2>&1 || true
retry gcloud projects add-iam-policy-binding "$PROJECT_ID" --condition=None --quiet \
  --member="serviceAccount:$PUBSUB_AGENT" --role=roles/bigquery.dataEditor >/dev/null
retry gcloud pubsub topics add-iam-policy-binding "$DLQ_TOPIC" \
  --member="serviceAccount:$PUBSUB_AGENT" --role=roles/pubsub.publisher >/dev/null

step "Subscription $SUBSCRIPTION: pull, ack deadline 60 s, dead-letter after 5 attempts"
exists gcloud pubsub subscriptions describe "$SUBSCRIPTION" ||
  gcloud pubsub subscriptions create "$SUBSCRIPTION" --topic="$TOPIC" --ack-deadline=60 \
    --dead-letter-topic="$DLQ_TOPIC" --max-delivery-attempts=5 --min-retry-delay=5s --max-retry-delay=60s
retry gcloud pubsub subscriptions add-iam-policy-binding "$SUBSCRIPTION" \
  --member="serviceAccount:$PUBSUB_AGENT" --role=roles/pubsub.subscriber >/dev/null

step "Export subscriptions: $TOPIC -> frames_published, $DLQ_TOPIC -> dead_letters"
exists gcloud pubsub subscriptions describe "$AUDIT_SUBSCRIPTION" ||
  retry gcloud pubsub subscriptions create "$AUDIT_SUBSCRIPTION" --topic="$TOPIC" \
    --bigquery-table="$PROJECT_ID.$DATASET.frames_published" --write-metadata
exists gcloud pubsub subscriptions describe "$DLQ_AUDIT_SUBSCRIPTION" ||
  retry gcloud pubsub subscriptions create "$DLQ_AUDIT_SUBSCRIPTION" --topic="$DLQ_TOPIC" \
    --bigquery-table="$PROJECT_ID.$DATASET.dead_letters" --write-metadata

step "Artifact Registry repo $AR_REPO"
exists gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" ||
  gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location="$REGION"

step "Service accounts: yolo-worker (Pub/Sub, Storage, BigQuery), keda-operator (Monitoring)"
exists gcloud iam service-accounts describe "$WORKER_GSA" || gcloud iam service-accounts create yolo-worker
exists gcloud iam service-accounts describe "$KEDA_GSA" || gcloud iam service-accounts create keda-operator
for role in roles/pubsub.subscriber roles/storage.objectViewer roles/bigquery.dataEditor; do
  retry gcloud projects add-iam-policy-binding "$PROJECT_ID" --condition=None --quiet \
    --member="serviceAccount:$WORKER_GSA" --role="$role" >/dev/null
done
retry gcloud projects add-iam-policy-binding "$PROJECT_ID" --condition=None --quiet \
  --member="serviceAccount:$KEDA_GSA" --role=roles/monitoring.viewer >/dev/null

step "Monitoring dashboard"
if [[ -z "$(gcloud monitoring dashboards list --filter='displayName="YOLO26 Stream Pipeline"' --format='value(name)')" ]]; then
  render "$ROOT/monitoring/dashboard.json" > "$ROOT/.tmp-dashboard.json"
  gcloud monitoring dashboards create --config-from-file="$ROOT/.tmp-dashboard.json"
  rm -f "$ROOT/.tmp-dashboard.json"
fi

step "Done. Next: python models/export_yolo26.py, then bash infra/cluster.sh build"
