# Loaded by setup.sh and cluster.sh: reads .env and derives resource names.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$ROOT/.env" ]] || { echo "Missing .env -> cp .env.example .env and set PROJECT_ID" >&2; exit 1; }
set -a; source <(sed 's/\r$//' "$ROOT/.env"); set +a   # tolerate Windows line endings
[[ "$PROJECT_ID" != "your-project-id" ]] || { echo "Set PROJECT_ID in .env" >&2; exit 1; }

gcloud config set project "$PROJECT_ID" >/dev/null 2>&1
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/worker:${IMAGE_TAG}"
BQ_TABLE="${PROJECT_ID}.${DATASET}.detections"
WORKER_GSA="yolo-worker@${PROJECT_ID}.iam.gserviceaccount.com"
KEDA_GSA="keda-operator@${PROJECT_ID}.iam.gserviceaccount.com"

step()   { printf '\n==> %s\n' "$*"; }
exists() { "$@" >/dev/null 2>&1; }
retry()  {  # IAM changes take up to a minute to apply
  for i in 1 2 3 4 5 6; do "$@" && return 0; echo "  retry $i/6 in 15s..."; sleep 15; done; return 1
}

# Fill __NAME__ placeholders in a manifest with values from .env
render() {
  sed -e "s|__PROJECT_ID__|$PROJECT_ID|g" -e "s|__NAMESPACE__|$NAMESPACE|g" -e "s|__IMAGE__|$IMAGE|g" \
      -e "s|__WORKER_GSA__|$WORKER_GSA|g" -e "s|__SUBSCRIPTION__|$SUBSCRIPTION|g" -e "s|__TOPIC__|$TOPIC|g" \
      -e "s|__BQ_TABLE__|$BQ_TABLE|g" -e "s|__REPLICAS__|${REPLICAS:-1}|g" \
      -e "s|__KEDA_TARGET__|$KEDA_TARGET_BACKLOG|g" -e "s|__KEDA_MIN__|$KEDA_MIN_REPLICAS|g" \
      -e "s|__KEDA_MAX__|$KEDA_MAX_REPLICAS|g" "$1"
}
