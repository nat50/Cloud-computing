#!/usr/bin/env bash
# Worker image, GKE cluster and scaling mode.
#
#   bash infra/cluster.sh build          build the worker image and push it to Artifact Registry
#   bash infra/cluster.sh up             create the Autopilot cluster, install KEDA, deploy with KEDA
#   bash infra/cluster.sh keda           switch to autoscaling on the Pub/Sub backlog
#   bash infra/cluster.sh fixed 8        switch to exactly 8 pods (comparison runs)
#   bash infra/cluster.sh down           delete the cluster: do this after EVERY session
source "$(dirname "$0")/lib.sh"

build() {
  [[ -f "$ROOT/models/yolo26n.onnx" ]] || { echo "Run python models/export_yolo26.py first" >&2; exit 1; }
  gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
  docker build -t "$IMAGE" "$ROOT"
  docker push "$IMAGE"
}

up() {
  step "Autopilot cluster $CLUSTER (first time ~10 min)"
  exists gcloud container clusters describe "$CLUSTER" --region="$REGION" ||
    gcloud container clusters create-auto "$CLUSTER" --region="$REGION"
  gcloud container clusters get-credentials "$CLUSTER" --region="$REGION"

  step "Workload Identity: Kubernetes service accounts -> Google service accounts"
  for pair in "$WORKER_GSA=$NAMESPACE/worker" "$KEDA_GSA=keda/keda-operator"; do
    retry gcloud iam service-accounts add-iam-policy-binding "${pair%%=*}" --quiet \
      --role=roles/iam.workloadIdentityUser \
      --member="serviceAccount:$PROJECT_ID.svc.id.goog[${pair#*=}]" >/dev/null
  done

  step "Install KEDA (needs helm; preinstalled in Cloud Shell)"
  helm repo add kedacore https://kedacore.github.io/charts >/dev/null 2>&1 || true
  helm repo update kedacore >/dev/null
  helm upgrade --install keda kedacore/keda --namespace keda --create-namespace --wait
  kubectl annotate serviceaccount keda-operator -n keda --overwrite "iam.gke.io/gcp-service-account=$KEDA_GSA"
  kubectl rollout restart deployment/keda-operator -n keda
  kubectl rollout status deployment/keda-operator -n keda --timeout=300s
}

deploy() {  # mode [pods]
  if [[ "$1" == fixed ]]; then
    REPLICAS="${2:?usage: cluster.sh fixed <pods>}"
    kubectl delete scaledobject worker -n "$NAMESPACE" --ignore-not-found 2>/dev/null || true
  else
    REPLICAS="$KEDA_MIN_REPLICAS"
  fi
  step "Deploy worker ($IMAGE), mode: $1 ${2:-}"
  render "$ROOT/k8s/worker.yaml" | kubectl apply -f -
  [[ "$1" == keda ]] && render "$ROOT/k8s/keda.yaml" | kubectl apply -f -
  [[ "$1" == fixed ]] && kubectl scale deployment worker -n "$NAMESPACE" --replicas="$REPLICAS"
  kubectl rollout status deployment/worker -n "$NAMESPACE" --timeout=900s
  kubectl get pods -n "$NAMESPACE"
}

case "${1:-}" in
  build) build ;;
  up)    up; deploy keda ;;
  keda)  deploy keda ;;
  fixed) deploy fixed "${2:-}" ;;
  down)  gcloud container clusters delete "$CLUSTER" --region="$REGION" --quiet ;;
  *)     sed -n '2,9p' "$0"; exit 1 ;;
esac
