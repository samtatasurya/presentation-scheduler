# Presentation Scheduler

A simple Python web application to manage presentation schedule.
The application is based on FastAPI and Google Cloud Firestore.

The difference between this branch and the main branch is the database layer.
This branch uses Firestore, whereas the main branch uses PostgreSQL with Piccolo as its ORM.

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
4. Install Firebase CLI according to [this documentation](https://firebase.google.com/docs/cli).

### Setup

1. Create a new Firestore in Native mode database.
2. Create a new Firestore collection.
3. Create a ".env" file on the root directory of this project with the following values:
```
API_USER=<plain_username>
API_HASHED_PASSWORD=<hashed_password>
DB_COLLECTION=<collection_name>
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
- `collection_name`
  - Firestore collection name created in the previous step to store documents.
4. Initialize a Firebase project using the following command on the root directory of this project, selecting only `Firestore` and `Emulators` features:
```
firebase init
```

### Run

1. On a terminal (Terminal #1), start Firebase emulator using the following command on the root directory of this project:
```
firebase emulators:start
```
2. On another terminal (Terminal #2), activate the virtual environment (if you have not already), e.g.
```
source ./venv/bin/activate
```
3. Run the application on Terminal #2.
```
(venv) $ uvicorn app.main:app --reload
```

## Google Cloud Deployment

For deployment on Google Cloud, see [this guide](docs/GCLOUD_DEPLOY.md).
