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

from asyncpg.exceptions import PostgresError
from piccolo.engine import engine_finder
from piccolo.query import Max

from passlib.context import CryptContext

from schedule.tables import ScheduleTable, TABLE_NAME
from settings import API_USER, API_HASHED_PASSWORD

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

def user_id_parse(user_id_str: str) -> int:
    """ Convert frontend user ID to DB-compatible ID. """
    return int(user_id_str.split("-")[1])


def date_parse(date_str: str) -> date:
    """ Convert input-format date string to datetime.date object. """
    return datetime.strptime(date_str, "%m/%d/%Y").date()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

###############################################################################
# Event handlers
###############################################################################

@app.on_event("startup")
async def open_database_connection_pool():
    engine = engine_finder()
    await engine.start_connnection_pool()


@app.on_event("shutdown")
async def close_database_connection_pool():
    engine = engine_finder()
    await engine.close_connnection_pool()

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
    all_sched = await ScheduleTable.select().order_by(ScheduleTable.date).run()
    for sched in all_sched:
        formatted_sched["users"].append({"id": sched["id"], "name": sched["name"]})
        formatted_sched["dates"].append(sched["date"])
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
        async with ScheduleTable._meta.db.transaction():
            for idx in range(len(users)):
                await ScheduleTable.update({
                        ScheduleTable.date: dates[idx]
                    }).where(ScheduleTable.id == users[idx]).run()
    return {"count": len(sched.users)}


@app.put("/schedule", status_code=status.HTTP_202_ACCEPTED,
         dependencies=[Depends(verify_credentials)])
async def rotate_schedule():
    """ Rotate dates that are older than current date. """
    old_schedules = await ScheduleTable.select(
        ScheduleTable.id, ScheduleTable.date).where(
        ScheduleTable.date < date.today()).order_by(
        ScheduleTable.date).run()
    if old_schedules is None:
        return {"count": 0}

    resp = await ScheduleTable.select(
        Max(ScheduleTable.date)).first().run()
    ref_date = resp["max"]

    # Atomic (all-or-nothing) updates
    async with ScheduleTable._meta.db.transaction():
        for sched in old_schedules:
            ref_date += timedelta(days=7)
            await ScheduleTable.update({
                    ScheduleTable.date: ref_date
                }).where(ScheduleTable.id == sched["id"]).run()
    return {"count": len(old_schedules)}


@app.post("/users", status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(verify_credentials)])
async def create_user(new_user: NewUser):
    """ Add a new user. """
    if not new_user or not new_user.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User's name is empty.",
        )
    resp = await ScheduleTable.select(
        Max(ScheduleTable.date)).first().run()
    max_date = resp["max"]
    if not max_date:
        new_date = date.today()
    else:
        new_date = max_date + timedelta(days=7)
    try:
        result = await ScheduleTable.insert(
            ScheduleTable(name=new_user.name, date=new_date)).run()
        result = result[0]
    except PostgresError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create a new user.",
        )
    return result


@app.delete("/users/{user_id}", status_code=status.HTTP_202_ACCEPTED,
            dependencies=[Depends(verify_credentials)])
async def delete_user(user_id: int):
    resp = await ScheduleTable.select().where(ScheduleTable.id == user_id).first().run()
    if resp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with the given ID not found.",
        )
    """ Remove an existing user. """
    # Atomic (all-or-nothing) update dates and delete the specified user
    async with ScheduleTable._meta.db.transaction():
        # Update dates of other users whose dates come after the user to be deleted
        await ScheduleTable.raw("CREATE VIEW view_schedules AS SELECT * FROM " + TABLE_NAME + " ORDER BY date ASC").run()
        await ScheduleTable.raw("CREATE RULE rule_schedules AS ON UPDATE TO view_schedules DO INSTEAD UPDATE " + TABLE_NAME +
                                "  SET date = NEW.date WHERE id = NEW.id").run()
        await ScheduleTable.raw("UPDATE view_schedules AS uold SET date = unew.new_date"
                                "  FROM ("
                                "    SELECT id, LAG(date) OVER (ORDER BY date ASC) AS new_date"
                                "    FROM view_schedules"
                                "  ) unew"
                                "  WHERE uold.id = unew.id AND date > {}", resp["date"]).run()
        await ScheduleTable.raw("DROP RULE rule_schedules ON view_schedules").run()
        await ScheduleTable.raw("DROP VIEW view_schedules").run()
        # Delete the specified user
        await ScheduleTable.delete().where(ScheduleTable.name == resp["name"]).run()
    return {"id": resp["id"]}
