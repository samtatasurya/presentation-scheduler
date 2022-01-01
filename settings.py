import os

from starlette.config import Config

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
_ENV_FILE = os.path.join(_THIS_DIR, ".env")

if os.path.isfile(_ENV_FILE):
    config = Config(".env")
else:
    import google.auth
    from google.cloud import secretmanager
    try:
        _, os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default()
    except google.auth.exceptions.DefaultCredentialsError:
        pass
    if os.environ.get("GOOGLE_CLOUD_PROJECT", None):
        # Pull secrets from Secret Manager
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        settings_name = os.environ.get("SETTINGS_NAME", "fastapi_settings")
        name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
        client = secretmanager.SecretManagerServiceClient()
        payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")

        envs = dict(s.split('=', 1) for s in payload.split('\n'))
        config = Config(environ=envs)
    else:
        raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")

API_USER = config("API_USER")
API_HASHED_PASSWORD = config("API_HASHED_PASSWORD")
DB_COLLECTION = config("DB_COLLECTION")
