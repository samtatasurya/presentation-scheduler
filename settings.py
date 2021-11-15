from starlette.config import Config

# Configuration from environment variables or '.env' file.
config = Config(".env")
API_USER = config("API_USER")
API_HASHED_PASSWORD = config("API_HASHED_PASSWORD")
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST")
DB_PORT = config("DB_PORT")
