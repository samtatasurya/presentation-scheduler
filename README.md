# Presentation Scheduler

A simple Python web application to manage presentation schedule.
The application is based on FastAPI, Piccolo, and PostgreSQL.

## Local Development

Follow the steps below to develop this application on your local machine.

### Installation

1. Create a new Python virtual environment, e.g.
```
$ python -m virtualenv venv
```
2. Activate the virtual environment, e.g.
```
$ source ./venv/bin/activate
```
3. Install required dependencies.
```
(venv) $ pip install -r requirements.txt
```

### Setup

1. Create a new PostgreSQL database.
2. Create a ".env" file on the root directory of this project with the following values:
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
  - To generate the hash of a password, you can do the following:
```
(venv) $ python
>>> from app.main import get_password_hash
>>> get_password_hash('plain-password-here')
'copy-this-hashed-password-to-dotenv-file'
```
- `database_url`
  - Database URL. For PostgreSQL, it is in the following format:
```
postgres://[user[:password]@][host][:port][/dbname]
```
- `max_size`
  - Maximum number of database connections in the pool.
  - [Piccolo](https://piccolo-orm.readthedocs.io/en/latest/piccolo/engines/postgres_engine.html#id1)
  - [asyncpg](https://magicstack.github.io/asyncpg/current/api/index.html#connection-pools)
3. Perform database migration.
```
(venv) $ piccolo migrations forwards schedule
```

### Run

1. Activate the virtual environment (if you have not already), e.g.
```
source ./venv/bin/activate
```
2. Run the application.
```
(venv) $ uvicorn app.main:app --reload
```

## Google Cloud Deployment

For deployment on Google Cloud, see [this guide](docs/GCLOUD_DEPLOY.md).
