#!/usr/bin/env bash
set -euo pipefail

required_vars=(
  GCP_PROJECT_ID
  GCP_REGION
  HF_ARTIFACT_REGISTRY_REPO
  HF_SERVICE_PREFIX
  HF_GCP_STORAGE_BUCKET
  HF_GCP_PUBSUB_RUN_TOPIC
  HF_GCP_PUBSUB_RUN_SUBSCRIPTION
  HF_GCP_PUBSUB_AGENT_TOPIC
  HF_GCP_PUBSUB_AGENT_SUBSCRIPTION
  HF_CLOUD_SQL_INSTANCE
  HF_CLOUD_SQL_DATABASE
  HF_CLOUD_SQL_USER
  HF_CLOUD_SQL_PASSWORD
  HF_API_SERVICE_ACCOUNT
  HF_AGENT_SERVICE_ACCOUNT
  HF_WORKER_SERVICE_ACCOUNT
  HF_PUBSUB_PUSH_SERVICE_ACCOUNT
  HF_LLM_MODEL
  HF_PLANNER_MODE
)

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required but was not found in PATH." >&2
  exit 1
fi

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required environment variable: ${var_name}" >&2
    exit 1
  fi
done

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
if [[ -z "${ACTIVE_ACCOUNT}" ]]; then
  echo "No active gcloud account is configured. Run 'gcloud auth login' first." >&2
  exit 1
fi

IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
REGISTRY_HOST="${GCP_REGION}-docker.pkg.dev"
IMAGE_PREFIX="${REGISTRY_HOST}/${GCP_PROJECT_ID}/${HF_ARTIFACT_REGISTRY_REPO}"

API_IMAGE="${IMAGE_PREFIX}/api:${IMAGE_TAG}"
AGENT_IMAGE="${IMAGE_PREFIX}/agent:${IMAGE_TAG}"
WORKER_IMAGE="${IMAGE_PREFIX}/worker:${IMAGE_TAG}"

API_SERVICE_NAME="${HF_SERVICE_PREFIX}-api"
AGENT_SERVICE_NAME="${HF_SERVICE_PREFIX}-agent"
WORKER_SERVICE_NAME="${HF_SERVICE_PREFIX}-worker"

CLOUD_SQL_CONNECTION="${GCP_PROJECT_ID}:${GCP_REGION}:${HF_CLOUD_SQL_INSTANCE}"
HF_METADATA_DATABASE_URL="postgresql+psycopg://${HF_CLOUD_SQL_USER}:${HF_CLOUD_SQL_PASSWORD}@/${HF_CLOUD_SQL_DATABASE}?host=/cloudsql/${CLOUD_SQL_CONNECTION}"

COMMON_ENV_VARS=(
  "HF_ENVIRONMENT=gcp"
  "HF_METADATA_DATABASE_URL=${HF_METADATA_DATABASE_URL}"
  "HF_ARTIFACT_BACKEND=gcs"
  "HF_GCP_PROJECT_ID=${GCP_PROJECT_ID}"
  "HF_GCP_LOCATION=${GCP_REGION}"
  "HF_GCP_STORAGE_BUCKET=${HF_GCP_STORAGE_BUCKET}"
  "HF_QUEUE_BACKEND=gcp_pubsub"
  "HF_GCP_PUBSUB_RUN_TOPIC=${HF_GCP_PUBSUB_RUN_TOPIC}"
  "HF_GCP_PUBSUB_RUN_SUBSCRIPTION=${HF_GCP_PUBSUB_RUN_SUBSCRIPTION}"
  "HF_GCP_PUBSUB_AGENT_TOPIC=${HF_GCP_PUBSUB_AGENT_TOPIC}"
  "HF_GCP_PUBSUB_AGENT_SUBSCRIPTION=${HF_GCP_PUBSUB_AGENT_SUBSCRIPTION}"
  "HF_PLACEHOLDER_WORKER_MODE=false"
  "HF_LLM_PROVIDER=vertex_ai"
  "HF_LLM_MODEL=${HF_LLM_MODEL}"
  "HF_PLANNER_MODE=${HF_PLANNER_MODE}"
)

TEMP_ENV_FILE="$(mktemp -t hound-forward-gcp-env.XXXXXX.yaml)"
TEMP_CLOUDBUILD_FILE="$(mktemp -t hound-forward-cloudbuild.XXXXXX.yaml)"
cleanup() {
  rm -f "${TEMP_ENV_FILE}"
  rm -f "${TEMP_CLOUDBUILD_FILE}"
}
trap cleanup EXIT

{
  for item in "${COMMON_ENV_VARS[@]}"; do
    key="${item%%=*}"
    value="${item#*=}"
    printf "%s: \"%s\"\n" "${key}" "${value//\"/\\\"}"
  done
} > "${TEMP_ENV_FILE}"

gcloud config set project "${GCP_PROJECT_ID}" >/dev/null

build_and_push_image() {
  local dockerfile_path="$1"
  local image_ref="$2"

  cat > "${TEMP_CLOUDBUILD_FILE}" <<EOF
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - --file
      - ${dockerfile_path}
      - --tag
      - ${image_ref}
      - .
images:
  - ${image_ref}
EOF

  gcloud builds submit \
    --config "${TEMP_CLOUDBUILD_FILE}" \
    .
}

build_and_push_image Dockerfile.api "${API_IMAGE}"
build_and_push_image Dockerfile.agent "${AGENT_IMAGE}"
build_and_push_image Dockerfile.worker "${WORKER_IMAGE}"

gcloud run deploy "${API_SERVICE_NAME}" \
  --image "${API_IMAGE}" \
  --region "${GCP_REGION}" \
  --service-account "${HF_API_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --port 8000 \
  --env-vars-file "${TEMP_ENV_FILE}" \
  --add-cloudsql-instances "${CLOUD_SQL_CONNECTION}"

gcloud run deploy "${AGENT_SERVICE_NAME}" \
  --image "${AGENT_IMAGE}" \
  --region "${GCP_REGION}" \
  --service-account "${HF_AGENT_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --no-allow-unauthenticated \
  --port 8080 \
  --command uvicorn \
  --args "hound_forward.agent.service:app,--host,0.0.0.0,--port,8080" \
  --env-vars-file "${TEMP_ENV_FILE}" \
  --add-cloudsql-instances "${CLOUD_SQL_CONNECTION}"

gcloud run deploy "${WORKER_SERVICE_NAME}" \
  --image "${WORKER_IMAGE}" \
  --region "${GCP_REGION}" \
  --service-account "${HF_WORKER_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --no-allow-unauthenticated \
  --port 8080 \
  --command uvicorn \
  --args "hound_forward.worker.service:app,--host,0.0.0.0,--port,8080" \
  --env-vars-file "${TEMP_ENV_FILE}" \
  --add-cloudsql-instances "${CLOUD_SQL_CONNECTION}"

PUSH_MEMBER="serviceAccount:${HF_PUBSUB_PUSH_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

gcloud run services add-iam-policy-binding "${AGENT_SERVICE_NAME}" \
  --region "${GCP_REGION}" \
  --member "${PUSH_MEMBER}" \
  --role roles/run.invoker >/dev/null

gcloud run services add-iam-policy-binding "${WORKER_SERVICE_NAME}" \
  --region "${GCP_REGION}" \
  --member "${PUSH_MEMBER}" \
  --role roles/run.invoker >/dev/null

AGENT_URL="$(gcloud run services describe "${AGENT_SERVICE_NAME}" --region "${GCP_REGION}" --format 'value(status.url)')"
WORKER_URL="$(gcloud run services describe "${WORKER_SERVICE_NAME}" --region "${GCP_REGION}" --format 'value(status.url)')"

create_or_update_push_subscription() {
  local subscription_name="$1"
  local topic_name="$2"
  local push_endpoint="$3"

  if gcloud pubsub subscriptions describe "${subscription_name}" >/dev/null 2>&1; then
    gcloud pubsub subscriptions update "${subscription_name}" \
      --push-endpoint "${push_endpoint}" \
      --push-auth-service-account "${HF_PUBSUB_PUSH_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  else
    gcloud pubsub subscriptions create "${subscription_name}" \
      --topic "${topic_name}" \
      --push-endpoint "${push_endpoint}" \
      --push-auth-service-account "${HF_PUBSUB_PUSH_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  fi
}

create_or_update_push_subscription \
  "${HF_GCP_PUBSUB_AGENT_SUBSCRIPTION}" \
  "${HF_GCP_PUBSUB_AGENT_TOPIC}" \
  "${AGENT_URL}/pubsub/agent-jobs"

create_or_update_push_subscription \
  "${HF_GCP_PUBSUB_RUN_SUBSCRIPTION}" \
  "${HF_GCP_PUBSUB_RUN_TOPIC}" \
  "${WORKER_URL}/pubsub/run-jobs"
