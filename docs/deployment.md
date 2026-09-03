# Deployment

## Target layout

The service is intended to run as a private Cloud Run service invoked on a schedule.

```text
Cloud Scheduler
    -> OIDC authenticated POST /sync
    -> private Cloud Run service
        -> HubSpot API
        -> Microsoft Entra ID / Dataverse
        -> Secret Manager
        -> Cloud Storage checkpoint (bidirectional mode only)
```

The examples below are a deployment template. Replace project, region, service-account, bucket, and secret names with values from your own environment.

## 1. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com
```

## 2. Create service accounts

Use a runtime identity for Cloud Run and a separate caller identity for Cloud Scheduler.

```bash
gcloud iam service-accounts create crm-sync-runtime \
  --display-name="CRM sync runtime"

gcloud iam service-accounts create crm-sync-scheduler \
  --display-name="CRM sync scheduler"
```

Keeping the two roles separate makes it easier to grant only the permissions each component needs.

## 3. Create secrets

Store credentials in Secret Manager rather than `.env` files or container images.

Example secret names:

```text
hubspot-access-token
dynamics-tenant-id
dynamics-client-id
dynamics-client-secret
dynamics-base-url
```

Create a secret and add its first version:

```bash
printf '%s' 'VALUE' | gcloud secrets create hubspot-access-token \
  --data-file=- \
  --replication-policy=automatic
```

For an existing secret, add a new version instead:

```bash
printf '%s' 'VALUE' | gcloud secrets versions add hubspot-access-token --data-file=-
```

Grant the runtime service account access only to the secrets it needs:

```bash
gcloud secrets add-iam-policy-binding hubspot-access-token \
  --member="serviceAccount:crm-sync-runtime@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Repeat for the Dataverse secrets.

## 4. Create checkpoint storage

This step is needed only for `SYNC_MODE=bidirectional`.

```bash
gcloud storage buckets create gs://CRM_SYNC_CHECKPOINT_BUCKET \
  --location=REGION \
  --uniform-bucket-level-access
```

Grant the runtime identity object access to that bucket. For a dedicated checkpoint bucket, `roles/storage.objectAdmin` at bucket scope is a simple deployment option:

```bash
gcloud storage buckets add-iam-policy-binding gs://CRM_SYNC_CHECKPOINT_BUCKET \
  --member="serviceAccount:crm-sync-runtime@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

A stricter custom role can be used if the deployment requires narrower permissions.

## 5. Build the container

One straightforward option is Cloud Build:

```bash
gcloud builds submit \
  --tag REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/crm-sync:latest
```

The Artifact Registry repository must already exist.

## 6. Deploy Cloud Run

### Forward-only mode

```bash
gcloud run deploy crm-sync \
  --image=REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/crm-sync:latest \
  --region=REGION \
  --service-account=crm-sync-runtime@PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --concurrency=1 \
  --max-instances=1 \
  --set-env-vars="HUBSPOT_LIST_ID=LIST_ID,DYNAMICS_API_VERSION=v9.2,MAPPING_FILE=config/mapping.example.json,SYNC_MODE=forward" \
  --set-secrets="HUBSPOT_ACCESS_TOKEN=hubspot-access-token:latest,DYNAMICS_TENANT_ID=dynamics-tenant-id:latest,DYNAMICS_CLIENT_ID=dynamics-client-id:latest,DYNAMICS_CLIENT_SECRET=dynamics-client-secret:latest,DYNAMICS_BASE_URL=dynamics-base-url:latest"
```

### Bidirectional contact mode

Add the checkpoint configuration and Dataverse integration user ID:

```bash
gcloud run deploy crm-sync \
  --image=REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/crm-sync:latest \
  --region=REGION \
  --service-account=crm-sync-runtime@PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --concurrency=1 \
  --max-instances=1 \
  --set-env-vars="HUBSPOT_LIST_ID=LIST_ID,DYNAMICS_API_VERSION=v9.2,MAPPING_FILE=config/mapping.example.json,SYNC_MODE=bidirectional,CHECKPOINT_BUCKET=CRM_SYNC_CHECKPOINT_BUCKET,CHECKPOINT_BLOB=checkpoints/reverse-contacts.txt,DYNAMICS_INTEGRATION_USER_ID=DATAVERSE_APPLICATION_USER_ID" \
  --set-secrets="HUBSPOT_ACCESS_TOKEN=hubspot-access-token:latest,DYNAMICS_TENANT_ID=dynamics-tenant-id:latest,DYNAMICS_CLIENT_ID=dynamics-client-id:latest,DYNAMICS_CLIENT_SECRET=dynamics-client-secret:latest,DYNAMICS_BASE_URL=dynamics-base-url:latest"
```

`--concurrency=1` and `--max-instances=1` are operational safeguards for this scheduled implementation. The checkpoint code does not implement a distributed lock, so horizontally concurrent bidirectional executions are intentionally avoided.

## 7. Grant Scheduler permission to invoke Cloud Run

```bash
gcloud run services add-iam-policy-binding crm-sync \
  --region=REGION \
  --member="serviceAccount:crm-sync-scheduler@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## 8. Create the Scheduler job

Get the Cloud Run service URL:

```bash
gcloud run services describe crm-sync \
  --region=REGION \
  --format='value(status.url)'
```

Then create an authenticated HTTP job. The following example runs every 15 minutes:

```bash
gcloud scheduler jobs create http crm-sync \
  --location=REGION \
  --schedule="*/15 * * * *" \
  --uri="https://SERVICE_URL/sync" \
  --http-method=POST \
  --oidc-service-account-email="crm-sync-scheduler@PROJECT_ID.iam.gserviceaccount.com" \
  --oidc-token-audience="https://SERVICE_URL"
```

Choose the schedule based on business requirements and expected CRM volume rather than treating the example frequency as a requirement.

## 9. Health check

`GET /health` returns:

```json
{"status":"ok"}
```

A private service requires an authenticated request. This endpoint confirms that the Flask/Gunicorn service is running; it does not perform live HubSpot or Dataverse dependency checks.

## 10. Logs

The application writes structured JSON to stdout/stderr, which Cloud Run collects through Cloud Logging.

Logs intentionally avoid:

- contact email addresses;
- phone numbers;
- CRM record payloads;
- HubSpot access tokens;
- Entra client secrets.

Useful operational signals are sync start/completion, processed counts, conflicts, skipped records, and exceptions.

## Deployment notes

- Keep Cloud Run private unless there is a specific reason to expose it.
- Use a Dataverse Application User with only the privileges the integration requires.
- Rotate secrets through Secret Manager versions rather than modifying source code.
- Keep the checkpoint bucket dedicated to the integration where practical.
- Run CI before deploying a new revision.
- Do not enable bidirectional mode until `DYNAMICS_INTEGRATION_USER_ID` and checkpoint storage are configured.
- This design reduces duplicate processing but does not claim exactly-once execution.
