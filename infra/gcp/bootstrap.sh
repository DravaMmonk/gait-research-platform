#!/usr/bin/env bash
set -euo pipefail

required_vars=(
  GCP_PROJECT_ID
  GCP_REGION
  HF_ARTIFACT_REGISTRY_REPO
  HF_GCP_STORAGE_BUCKET
  HF_GCP_PUBSUB_RUN_TOPIC
  HF_GCP_PUBSUB_AGENT_TOPIC
  HF_CLOUD_SQL_INSTANCE
  HF_CLOUD_SQL_DATABASE
  HF_CLOUD_SQL_USER
  HF_CLOUD_SQL_PASSWORD
  HF_CLOUD_SQL_TIER
  HF_CLOUD_SQL_VERSION
  HF_API_SERVICE_ACCOUNT
  HF_AGENT_SERVICE_ACCOUNT
  HF_WORKER_SERVICE_ACCOUNT
  HF_PUBSUB_PUSH_SERVICE_ACCOUNT
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

HF_CLOUD_SQL_EDITION="${HF_CLOUD_SQL_EDITION:-ENTERPRISE}"
CLOUDBUILD_BUCKET="${HF_CLOUDBUILD_BUCKET:-${GCP_PROJECT_ID}_cloudbuild}"

gcloud config set project "${GCP_PROJECT_ID}" >/dev/null

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
if [[ -z "${ACTIVE_ACCOUNT}" ]]; then
  echo "No active gcloud account is configured. Run 'gcloud auth login' first." >&2
  exit 1
fi

gcloud services enable \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com

if ! gcloud artifacts repositories describe "${HF_ARTIFACT_REGISTRY_REPO}" --location "${GCP_REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${HF_ARTIFACT_REGISTRY_REPO}" \
    --location "${GCP_REGION}" \
    --repository-format docker \
    --description "Hound Forward runtime images"
fi

if ! gcloud storage buckets describe "gs://${HF_GCP_STORAGE_BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${HF_GCP_STORAGE_BUCKET}" --location "${GCP_REGION}"
fi

if ! gcloud storage buckets describe "gs://${CLOUDBUILD_BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${CLOUDBUILD_BUCKET}" --location us
fi

for topic_name in "${HF_GCP_PUBSUB_RUN_TOPIC}" "${HF_GCP_PUBSUB_AGENT_TOPIC}"; do
  if ! gcloud pubsub topics describe "${topic_name}" >/dev/null 2>&1; then
    gcloud pubsub topics create "${topic_name}"
  fi
done

PROJECT_NUMBER="$(gcloud projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')"
PUBSUB_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"
COMPUTE_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for service_account_name in \
  "${HF_API_SERVICE_ACCOUNT}" \
  "${HF_AGENT_SERVICE_ACCOUNT}" \
  "${HF_WORKER_SERVICE_ACCOUNT}" \
  "${HF_PUBSUB_PUSH_SERVICE_ACCOUNT}"
do
  if ! gcloud iam service-accounts describe "${service_account_name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${service_account_name}" \
      --display-name "${service_account_name}"
  fi
done

gcloud iam service-accounts add-iam-policy-binding \
  "${HF_PUBSUB_PUSH_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --member "serviceAccount:${PUBSUB_SERVICE_AGENT}" \
  --role roles/iam.serviceAccountTokenCreator >/dev/null

for project_role in roles/artifactregistry.writer roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member "serviceAccount:${COMPUTE_SERVICE_ACCOUNT}" \
    --role "${project_role}" >/dev/null
done

gcloud storage buckets add-iam-policy-binding "gs://${CLOUDBUILD_BUCKET}" \
  --member "serviceAccount:${COMPUTE_SERVICE_ACCOUNT}" \
  --role roles/storage.objectAdmin >/dev/null

if ! gcloud sql instances describe "${HF_CLOUD_SQL_INSTANCE}" >/dev/null 2>&1; then
  gcloud sql instances create "${HF_CLOUD_SQL_INSTANCE}" \
    --database-version "${HF_CLOUD_SQL_VERSION}" \
    --edition "${HF_CLOUD_SQL_EDITION}" \
    --tier "${HF_CLOUD_SQL_TIER}" \
    --region "${GCP_REGION}"
fi

if ! gcloud sql databases describe "${HF_CLOUD_SQL_DATABASE}" --instance "${HF_CLOUD_SQL_INSTANCE}" >/dev/null 2>&1; then
  gcloud sql databases create "${HF_CLOUD_SQL_DATABASE}" --instance "${HF_CLOUD_SQL_INSTANCE}"
fi

if ! gcloud sql users describe "${HF_CLOUD_SQL_USER}" --instance "${HF_CLOUD_SQL_INSTANCE}" >/dev/null 2>&1; then
  gcloud sql users create "${HF_CLOUD_SQL_USER}" \
    --instance "${HF_CLOUD_SQL_INSTANCE}" \
    --password "${HF_CLOUD_SQL_PASSWORD}"
else
  gcloud sql users set-password "${HF_CLOUD_SQL_USER}" \
    --instance "${HF_CLOUD_SQL_INSTANCE}" \
    --password "${HF_CLOUD_SQL_PASSWORD}"
fi

for runtime_account in \
  "${HF_API_SERVICE_ACCOUNT}" \
  "${HF_AGENT_SERVICE_ACCOUNT}" \
  "${HF_WORKER_SERVICE_ACCOUNT}"
do
  member="serviceAccount:${runtime_account}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member "${member}" \
    --role roles/cloudsql.client >/dev/null
  gcloud storage buckets add-iam-policy-binding "gs://${HF_GCP_STORAGE_BUCKET}" \
    --member "${member}" \
    --role roles/storage.objectAdmin >/dev/null
done

for llm_account in \
  "${HF_API_SERVICE_ACCOUNT}" \
  "${HF_AGENT_SERVICE_ACCOUNT}"
do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member "serviceAccount:${llm_account}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role roles/aiplatform.user >/dev/null
done

for publisher_account in \
  "${HF_API_SERVICE_ACCOUNT}" \
  "${HF_AGENT_SERVICE_ACCOUNT}"
do
  member="serviceAccount:${publisher_account}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  for topic_name in "${HF_GCP_PUBSUB_RUN_TOPIC}" "${HF_GCP_PUBSUB_AGENT_TOPIC}"; do
    gcloud pubsub topics add-iam-policy-binding "${topic_name}" \
      --member "${member}" \
      --role roles/pubsub.publisher >/dev/null
  done
done
