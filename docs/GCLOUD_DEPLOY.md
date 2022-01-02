# Google Cloud Deployment

The following guide is for the deployment of this application on Google Cloud.
It follows the following guides, with modifications explained below:
- [Django on Cloud Run](https://cloud.google.com/python/django/run)
- [Using Firestore server client library](https://cloud.google.com/firestore/docs/quickstart-servers)

## Services Used

1. Cloud Firestore
2. Secret Manager
3. Cloud Build
4. Container Registry
5. Cloud Run
6. Cloud Scheduler

## Modifications

1. In [Django on Cloud Run](https://cloud.google.com/python/django/run) guide, we skip the sections related to Cloud SQL (since we use Firestore) and Cloud Storage (since we do not have any static files).
2. While for local development we store the values below in a ".env" file, for cloud deployment we store these values using Secret Manager.
```
API_USER=<plain_username>
API_HASHED_PASSWORD=<hashed_password>
DB_COLLECTION=<collection_name>
```
- `plain_username`
  - Username (plain string) to be used in accessing some API routes.
- `hashed_password`
  - Password (hashed) to be used in accessing some API routes.
- `collection_name`
  - Firestore collection name created in the previous step to store documents.
3. In `cloudbuild.yaml`, modify the "substitutions" values to match your own values.
```
substitutions:
  _SERVICE_NAME: <your-service-name>
```

## Commands

Some important `gcloud` commands.

### Initial Deployment

1. Cloud Build
```
gcloud builds submit --config cloudbuild.yaml
```
2. Cloud Run
```
gcloud run deploy <SERVICE_NAME> \
    --platform managed \
    --region <REGION> \
    --image gcr.io/<PROJECT_ID>/<SERVICE_NAME> \
    --allow-unauthenticated
```

### Updating Application

1. Cloud Build
```
gcloud builds submit --config cloudbuild.yaml
```
2. Cloud Run
```
gcloud run deploy <SERVICE_NAME> \
    --platform managed \
    --region <REGION> \
    --image gcr.io/<PROJECT_ID>/<SERVICE_NAME>
```

### Setting Up Scheduled Job

The command below will create a scheduled job named `rotate-schedule` which will
run everyday at 12.00 pm UTC. In `--headers`, `<BASE64>` refers to a base64-encoded
string of `<API_USER>:<API_PASSWORD>`, which is used for HTTP Basic authentication.

1. Cloud Scheduler
```
gcloud scheduler jobs create http rotate-schedule \
    --description="<YOUR_DESCRIPTION>" \
    --schedule="0 12 * * *" \
    --time-zone="utc" \
    --uri="https://<YOUR_URL>/schedule" \
    --headers="Authorization=Basic <BASE64>" \
    --http-method="put"
```
