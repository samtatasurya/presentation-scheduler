import os
import secrets
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from google.api_core import datetime_helpers as dh
from google.cloud import firestore

from passlib.context import CryptContext

from settings import API_USER, API_HASHED_PASSWORD, DB_COLLECTION

###############################################################################
# Schema
###############################################################################

class Schedule(BaseModel):
    users: List[str]
    dates: List[str]


class NewUser(BaseModel):
    name: str

###############################################################################
# Setup
###############################################################################

security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Presentation Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))
templates = Jinja2Templates(directory=template_dir)

def date_format(value: date, format: Optional[str] = "%a, %b %-d, %Y") -> str:
    """ Convert datetime.date object to human-readable date string. """
    return value.strftime(format)
templates.env.filters["date_format"] = date_format

###############################################################################
# Helper functions
###############################################################################

def user_id_parse(user_id_str: str) -> str:
    """ Convert frontend user ID to Firestore-compatible ID. """
    return user_id_str.split("-")[1]


def date_parse(date_str: str) -> date:
    """ Convert input-format date string to datetime.date object. """
    return datetime.strptime(date_str, "%m/%d/%Y").date()


def date_to_firestore_timestamp(date_obj: date) -> dh.DatetimeWithNanoseconds:
    """ Convert datetime.date object to Firestore-compatible timestamp. """
    datetime_obj = datetime.combine(date_obj, datetime.min.time())
    rfc3339_str = dh.to_rfc3339(datetime_obj)
    return dh.DatetimeWithNanoseconds.from_rfc3339(rfc3339_str)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_async_client():
    """ Get an async client for interacting with Google Cloud Firestore. """
    if os.environ.get("GOOGLE_CLOUD_PROJECT", None) is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to establish database connection.",
        )
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    return firestore.AsyncClient(project=project_id)

###############################################################################
# Dependencies
###############################################################################

async def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """ Verify that the credentials passed for write access are correct. """
    correct_username = secrets.compare_digest(credentials.username, API_USER)
    correct_password = pwd_context.verify(credentials.password, API_HASHED_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )

###############################################################################
# Routes
###############################################################################

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    schedule = await get_schedule()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "users": schedule["users"],
        "dates": schedule["dates"],
    })


@app.get("/schedule", status_code=status.HTTP_200_OK)
async def get_schedule():
    """ Retrieve saved schedule. """
    formatted_sched = {
        "users": [],
        "dates": [],
    }
    db = get_async_client()
    query = db.collection(DB_COLLECTION).order_by("datetime")
    async for res in query.stream():
        sched = res.to_dict()
        formatted_sched["users"].append({"id": res.id, "name": sched["name"]})
        formatted_sched["dates"].append(sched["datetime"].date())
    return formatted_sched


@app.post("/schedule", status_code=status.HTTP_202_ACCEPTED,
          dependencies=[Depends(verify_credentials)])
async def update_schedule(sched: Schedule):
    """ Update schedule. """
    if len(sched.users) != len(sched.dates):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Length mismatch between users and dates.",
        )
    else:
        users = [user_id_parse(u) for u in sched.users]
        dates = [date_parse(d) for d in sched.dates]
        # Atomic (all-or-nothing) updates
        db = get_async_client()
        count = 0
        batch = db.batch()
        for idx in range(len(users)):
            sched_ref = db.collection(DB_COLLECTION).document(users[idx])
            batch.update(sched_ref, {"datetime": date_to_firestore_timestamp(dates[idx])})
            count += 1
        if count > 0:
            await batch.commit()
    return {"count": len(sched.users)}


@app.put("/schedule", status_code=status.HTTP_202_ACCEPTED,
         dependencies=[Depends(verify_credentials)])
async def rotate_schedule():
    """ Rotate dates that are older than current date. """
    db = get_async_client()
    # Get maximum
    ref_date = None
    query = db.collection(DB_COLLECTION).order_by("datetime", direction=firestore.Query.DESCENDING).limit(1)
    async for res in query.stream():
        sched = res.to_dict()
        ref_date = sched["datetime"].date()

    # Atomic (all-or-nothing) updates
    today_ts = date_to_firestore_timestamp(date.today())
    query = db.collection(DB_COLLECTION).where("datetime", "<", today_ts).order_by("datetime")
    count = 0
    batch = db.batch()
    async for res in query.stream():
        ref_date += timedelta(days=7)
        sched_ref = db.collection(DB_COLLECTION).document(res.id)
        batch.update(sched_ref, {"datetime": date_to_firestore_timestamp(ref_date)})
        count += 1
    if count > 0:
        await batch.commit()

    return {"count": count}


@app.post("/users", status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(verify_credentials)])
async def create_user(new_user: NewUser):
    """ Add a new user. """
    if not new_user or not new_user.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User's name is empty.",
        )

    db = get_async_client()
    # Get maximum
    max_date = None
    query = db.collection(DB_COLLECTION).order_by("datetime", direction=firestore.Query.DESCENDING).limit(1)
    async for res in query.stream():
        sched = res.to_dict()
        max_date = sched["datetime"].date()

    if max_date is None:
        new_date = date.today()
    else:
        new_date = max_date + timedelta(days=7)

    try:
        new_sched_ref = db.collection(DB_COLLECTION).document()
        await new_sched_ref.set({
            "name": new_user.name,
            "datetime": date_to_firestore_timestamp(new_date),
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create a new user.",
        )
    return {"id": new_sched_ref.id}


@app.delete("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED,
            dependencies=[Depends(verify_credentials)])
async def delete_user(user_id: str):
    """ Remove an existing user. """
    db = get_async_client()
    target_ref = db.collection(DB_COLLECTION).document(user_id)
    doc = await target_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with the given ID not found.",
        )

    target_id = doc.id
    target = doc.to_dict()
    prev_date = target["datetime"].date()
    prev_date_ts = date_to_firestore_timestamp(prev_date)

    # Atomic (all-or-nothing) update dates and delete the specified user
    query = db.collection(DB_COLLECTION).where("datetime", ">", prev_date_ts).order_by("datetime")
    batch = db.batch()
    # Update dates of other users whose dates come after the user to be deleted
    async for res in query.stream():
        sched = res.to_dict()
        tmp_date = sched["datetime"].date()
        sched_ref = db.collection(DB_COLLECTION).document(res.id)
        batch.update(sched_ref, {"datetime": date_to_firestore_timestamp(prev_date)})
        prev_date = tmp_date
    # Delete the specified user
    batch.delete(target_ref)
    await batch.commit()

    return {"id": target_id}
