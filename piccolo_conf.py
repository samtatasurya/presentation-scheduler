from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from settings import DB_URL

DB = PostgresEngine(config={"dsn": DB_URL})

# A list of paths to piccolo apps
APP_REGISTRY = AppRegistry(apps=[
    "schedule.piccolo_app",
])
