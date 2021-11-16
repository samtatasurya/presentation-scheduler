# Presentation Scheduler

A simple Python web application to manage presentation schedule.
The application is based on FastAPI, Piccolo, and PostgreSQL.

## Installation

1. Install required dependencies.
```
pip install -r requirements.txt
```

## Setup

1. Create PostgreSQL database.
2. Perform database migration.
```
piccolo migrations forwards schedule
```
3. Create '.env' file with the following values:
```
API_USER=
API_HASHED_PASSWORD=
DB_URL=
```
