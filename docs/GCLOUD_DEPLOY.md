# Google Cloud Deployment

The following guide is for the deployment of this application on Google Cloud.
It follows the [Django on Cloud Run](https://cloud.google.com/python/django/run), with modifications explained below.

## Services Used

1. Cloud SQL
2. Secret Manager
3. Cloud Build
4. Container Registry
5. Cloud Run
6. Cloud Scheduler

## Modifications

1. We skip the section [Set up a Cloud Storage bucket](https://cloud.google.com/python/django/run#set-up-a-cloud-storage-bucket) since we do not have any static files.
2. While for local development we store the values below in a ".env" file, for cloud deployment we store these values using Secret Manager. _Pay particular attention to the format of `database_url`_.
```
API_USER=<plain_username>
API_HASHED_PASSWORD=<hashed_password>
DB_URL=<database_url>
DB_MAX_POOL_SIZE=<max_size>
```
- `plain_username`
  - Username (plain string) to be used in accessing some API routes.
- `hashed_password`
  - Password (hashed) to be used in accessing some API routes.
- `database_url`
  - Database URL. For PostgreSQL instance on Cloud SQL, it is in the following format:
```
postgres:///<DB_NAME>?host=/cloudsql/<PROJECT_ID>:<REGION>:<INSTANCE_NAME>/.s.PGSQL.5432&user=<DB_USER>&password=<DB_PASS>
```
- `max_size`
  - Maximum number of database connections in the pool.
  - Cloud SQL has [limits](https://cloud.google.com/sql/docs/postgres/quotas#fixed-limits) depending on the machine type.
3. In `cloudbuild.yaml`, modify the "substitutions" values to match your own values.
```
substitutions:
  _INSTANCE_NAME: <cloudsql-instance-name>
  _REGION: <your-target-region>
  _SECRET_SETTINGS_NAME: <secret-name-in-secret-manager>
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
    --add-cloudsql-instances <PROJECT_ID>:<REGION>:<INSTANCE_NAME> \
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
