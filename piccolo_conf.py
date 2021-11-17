import os

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from settings import DB_URL

pg_conf = {"dsn": DB_URL}
if os.environ.get("GOOGLE_CLOUD_PROJECT", None):
    pg_conf["ssl"] = "disable"  # using cloud_sql_proxy

DB = PostgresEngine(config=pg_conf)

# A list of paths to piccolo apps
APP_REGISTRY = AppRegistry(apps=[
    "schedule.piccolo_app",
])
