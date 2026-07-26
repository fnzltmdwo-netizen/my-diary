import os
import secrets
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)

from fastapi.responses import FileResponse

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from sqlalchemy import inspect, text

from sqlalchemy.orm import Session

from starlette.middleware.sessions import (
    SessionMiddleware,
)

from backend.database import (
    Base,
    engine,
    get_db,
)

from backend.models import (
    DailyNote,
    Schedule,
    ScheduleOccurrence,
    Todo,
)


# =========================================================
# 경로 / ENV
# =========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

FRONTEND_DIR = (
    BASE_DIR
    / "frontend"
)

load_dotenv(
    BASE_DIR
    / ".env"
)


DIARY_USERNAME = os.getenv(
    "DIARY_USERNAME",
    "admin",
)


DIARY_PASSWORD = os.getenv(
    "DIARY_PASSWORD",
    "1234",
)


SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "change-this-secret",
)


# =========================================================
# 기존 DB 보완
# =========================================================

def ensure_schedule_columns():

    inspector = inspect(engine)

    if (
        "schedules"
        not in
        inspector.get_table_names()
    ):
        return


    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "schedules"
        )
    }


    with engine.begin() as connection:

        if (
            "category"
            not in columns
        ):

            connection.execute(
                text(
                    """
                    ALTER TABLE schedules
                    ADD COLUMN category
                    VARCHAR DEFAULT 'daily'
                    """
                )
            )


        if (
            "important"
            not in columns
        ):

            connection.execute(
                text(
                    """
                    ALTER TABLE schedules
                    ADD COLUMN important
                    BOOLEAN DEFAULT 0
                    """
                )
            )


        if (
            "repeat_type"
            not in columns
        ):

            connection.execute(
                text(
                    """
                    ALTER TABLE schedules
                    ADD COLUMN repeat_type
                    VARCHAR DEFAULT 'none'
                    """
                )
            )


        if (
            "repeat_until"
            not in columns
        ):

            connection.execute(
                text(
                    """
                    ALTER TABLE schedules
                    ADD COLUMN repeat_until
                    VARCHAR
                    """
                )
            )


ensure_schedule_columns()


Base.metadata.create_all(
    bind=engine
)


# =========================================================
# FastAPI
# =========================================================

app = FastAPI()


IS_RENDER = (
    os.getenv(
        "RENDER",
        "false"
    ).lower()
    == "true"
)


app.add_middleware(
    SessionMiddleware,

    secret_key=SESSION_SECRET,

    session_cookie="my_diary_session",

    max_age=60 * 60 * 24 * 30,

    same_site="lax",

    https_only=IS_RENDER,
)


app.mount(
    "/static",

    StaticFiles(
        directory=FRONTEND_DIR,
    ),

    name="static",
)


# =========================================================
# 로그인
# =========================================================

class LoginRequest(BaseModel):
    username: str
    password: str


def require_login(
    request: Request,
):

    if not request.session.get(
        "logged_in"
    ):

        raise HTTPException(
            status_code=401,
            detail="로그인이 필요합니다.",
        )


@app.get("/")
def home(
    request: Request,
):

    if request.session.get(
        "logged_in"
    ):

        return FileResponse(
            FRONTEND_DIR
            / "index.html"
        )


    return FileResponse(
        FRONTEND_DIR
        / "login.html"
    )


@app.get("/login")
def login_page(
    request: Request,
):

    if request.session.get(
        "logged_in"
    ):

        return FileResponse(
            FRONTEND_DIR
            / "index.html"
        )


    return FileResponse(
        FRONTEND_DIR
        / "login.html"
    )


@app.post("/api/login")
def login(
    data: LoginRequest,
    request: Request,
):

    username_ok = (
        secrets.compare_digest(
            data.username,
            DIARY_USERNAME,
        )
    )


    password_ok = (
        secrets.compare_digest(
            data.password,
            DIARY_PASSWORD,
        )
    )


    if not (
        username_ok
        and
        password_ok
    ):

        raise HTTPException(
            status_code=401,
            detail=(
                "아이디 또는 비밀번호가 "
                "올바르지 않습니다."
            ),
        )


    request.session[
        "logged_in"
    ] = True


    return {
        "success": True
    }


@app.post("/api/logout")
def logout(
    request: Request,
):

    request.session.clear()


    return {
        "success": True
    }


@app.get("/api/auth")
def auth_status(
    request: Request,
):

    return {
        "logged_in":
            bool(
                request.session.get(
                    "logged_in"
                )
            )
    }


# =========================================================
# Pydantic
# =========================================================

class ScheduleCreate(BaseModel):

    date: str

    time: str

    text: str

    category: str = "daily"

    important: bool = False

    repeat_type: str = "none"

    repeat_until: Optional[str] = None


class ScheduleEdit(BaseModel):

    time: Optional[str] = None

    text: Optional[str] = None

    category: Optional[str] = None

    important: Optional[bool] = None

    repeat_type: Optional[str] = None

    repeat_until: Optional[str] = None


class ScheduleCompleteUpdate(
    BaseModel
):

    completed: bool

    date: Optional[str] = None


class TodoCreate(BaseModel):

    date: str

    text: str


class TodoEdit(BaseModel):

    text: Optional[str] = None


class TodoCompleteUpdate(
    BaseModel
):

    completed: bool


class NoteUpdate(BaseModel):

    date: str

    text: str


# =========================================================
# 반복 일정
# =========================================================

ALLOWED_REPEAT_TYPES = {
    "none",
    "daily",
    "weekly",
    "monthly",
}


def parse_date(
    value: str,
) -> date:

    try:

        return date.fromisoformat(
            value
        )


    except ValueError:

        raise HTTPException(
            status_code=400,
            detail=(
                "날짜 형식이 "
                "올바르지 않습니다."
            ),
        )


def schedule_occurs_on(
    schedule: Schedule,
    target_string: str,
):

    start_date = parse_date(
        schedule.date
    )


    target_date = parse_date(
        target_string
    )


    if (
        target_date
        < start_date
    ):

        return False


    if schedule.repeat_until:

        end_date = parse_date(
            schedule.repeat_until
        )


        if (
            target_date
            > end_date
        ):

            return False


    repeat_type = (
        schedule.repeat_type
        or
        "none"
    )


    if (
        repeat_type
        == "none"
    ):

        return (
            schedule.date
            == target_string
        )


    if (
        repeat_type
        == "daily"
    ):

        return True


    if (
        repeat_type
        == "weekly"
    ):

        return (
            start_date.weekday()
            ==
            target_date.weekday()
        )


    if (
        repeat_type
        == "monthly"
    ):

        return (
            start_date.day
            ==
            target_date.day
        )


    return False


def schedule_to_dict(
    schedule: Schedule,
    target_date: str,
    db: Session,
):

    repeat_type = (
        schedule.repeat_type
        or
        "none"
    )


    completed = (
        schedule.completed
    )


    if (
        repeat_type
        != "none"
    ):

        occurrence = (
            db.query(
                ScheduleOccurrence
            )
            .filter(
                ScheduleOccurrence.schedule_id
                == schedule.id,

                ScheduleOccurrence.date
                == target_date,
            )
            .first()
        )


        completed = (
            occurrence.completed
            if occurrence
            else False
        )


    return {

        "id":
            schedule.id,

        "date":
            target_date,

        "start_date":
            schedule.date,

        "time":
            schedule.time,

        "text":
            schedule.text,

        "completed":
            bool(
                completed
            ),

        "category":
            schedule.category
            or
            "daily",

        "important":
            bool(
                schedule.important
            ),

        "repeat_type":
            repeat_type,

        "repeat_until":
            schedule.repeat_until,
    }


# =========================================================
# 일정
# =========================================================

@app.get(
    "/api/schedules",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def get_schedules(
    date: str,
    db: Session = Depends(
        get_db
    ),
):

    parse_date(date)


    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.date
            <= date
        )
        .all()
    )


    result = []


    for schedule in schedules:

        if schedule_occurs_on(
            schedule,
            date,
        ):

            result.append(
                schedule_to_dict(
                    schedule,
                    date,
                    db,
                )
            )


    result.sort(
        key=lambda item: (
            item["time"],
            item["id"],
        )
    )


    return result


@app.post(
    "/api/schedules",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(
        get_db
    ),
):

    parse_date(
        data.date
    )


    if (
        data.repeat_type
        not in
        ALLOWED_REPEAT_TYPES
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "잘못된 반복 "
                "방식입니다."
            ),
        )


    if data.repeat_until:

        parse_date(
            data.repeat_until
        )


        if (
            data.repeat_until
            < data.date
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "반복 종료일은 "
                    "시작일보다 빠를 수 없습니다."
                ),
            )


    if (
        data.repeat_type
        == "none"
    ):

        data.repeat_until = None


    schedule = Schedule(

        date=data.date,

        time=data.time,

        text=data.text,

        completed=False,

        category=data.category,

        important=data.important,

        repeat_type=data.repeat_type,

        repeat_until=data.repeat_until,
    )


    db.add(schedule)

    db.commit()

    db.refresh(schedule)


    return schedule


@app.patch(
    "/api/schedules/{schedule_id}/complete",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def update_schedule_complete(
    schedule_id: int,
    data: ScheduleCompleteUpdate,
    db: Session = Depends(
        get_db
    ),
):

    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.id
            == schedule_id
        )
        .first()
    )


    if not schedule:

        raise HTTPException(
            status_code=404,
            detail=(
                "일정을 찾을 수 없습니다."
            ),
        )


    repeat_type = (
        schedule.repeat_type
        or
        "none"
    )


    if (
        repeat_type
        == "none"
    ):

        schedule.completed = (
            data.completed
        )


        db.commit()

        db.refresh(schedule)


        return schedule


    if not data.date:

        raise HTTPException(
            status_code=400,
            detail=(
                "반복 일정은 "
                "날짜가 필요합니다."
            ),
        )


    if not schedule_occurs_on(
        schedule,
        data.date,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "해당 날짜에는 "
                "이 일정이 없습니다."
            ),
        )


    occurrence = (
        db.query(
            ScheduleOccurrence
        )
        .filter(
            ScheduleOccurrence.schedule_id
            == schedule_id,

            ScheduleOccurrence.date
            == data.date,
        )
        .first()
    )


    if not occurrence:

        occurrence = (
            ScheduleOccurrence(
                schedule_id=
                    schedule_id,

                date=
                    data.date,

                completed=
                    data.completed,
            )
        )


        db.add(
            occurrence
        )


    else:

        occurrence.completed = (
            data.completed
        )


    db.commit()

    db.refresh(
        occurrence
    )


    return occurrence


@app.patch(
    "/api/schedules/{schedule_id}",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def edit_schedule(
    schedule_id: int,
    data: ScheduleEdit,
    db: Session = Depends(
        get_db
    ),
):

    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.id
            == schedule_id
        )
        .first()
    )


    if not schedule:

        raise HTTPException(
            status_code=404,
            detail=(
                "일정을 찾을 수 없습니다."
            ),
        )


    if (
        data.time
        is not None
    ):

        schedule.time = (
            data.time
        )


    if (
        data.text
        is not None
    ):

        schedule.text = (
            data.text
        )


    if (
        data.category
        is not None
    ):

        schedule.category = (
            data.category
        )


    if (
        data.important
        is not None
    ):

        schedule.important = (
            data.important
        )


    if (
        data.repeat_type
        is not None
    ):

        if (
            data.repeat_type
            not in
            ALLOWED_REPEAT_TYPES
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "잘못된 반복 "
                    "방식입니다."
                ),
            )


        schedule.repeat_type = (
            data.repeat_type
        )


    current_repeat_type = (
        schedule.repeat_type
        or
        "none"
    )


    if (
        current_repeat_type
        == "none"
    ):

        schedule.repeat_until = None


    else:

        if data.repeat_until:

            parse_date(
                data.repeat_until
            )


            if (
                data.repeat_until
                < schedule.date
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "반복 종료일은 "
                        "시작일보다 빠를 수 없습니다."
                    ),
                )


        schedule.repeat_until = (
            data.repeat_until
        )


    db.commit()

    db.refresh(schedule)


    return schedule


@app.delete(
    "/api/schedules/{schedule_id}",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(
        get_db
    ),
):

    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.id
            == schedule_id
        )
        .first()
    )


    if not schedule:

        raise HTTPException(
            status_code=404,
            detail=(
                "일정을 찾을 수 없습니다."
            ),
        )


    (
        db.query(
            ScheduleOccurrence
        )
        .filter(
            ScheduleOccurrence.schedule_id
            == schedule_id
        )
        .delete(
            synchronize_session=False
        )
    )


    db.delete(
        schedule
    )


    db.commit()


    return {
        "success": True
    }


# =========================================================
# TODO
# =========================================================

@app.get(
    "/api/todos",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def get_todos(
    date: str,
    db: Session = Depends(
        get_db
    ),
):

    return (
        db.query(Todo)
        .filter(
            Todo.date == date
        )
        .order_by(
            Todo.id.asc()
        )
        .all()
    )


@app.post(
    "/api/todos",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def create_todo(
    data: TodoCreate,
    db: Session = Depends(
        get_db
    ),
):

    todo = Todo(

        date=data.date,

        text=data.text,

        completed=False,
    )


    db.add(todo)

    db.commit()

    db.refresh(todo)


    return todo


@app.patch(
    "/api/todos/{todo_id}/complete",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def update_todo_complete(
    todo_id: int,
    data: TodoCompleteUpdate,
    db: Session = Depends(
        get_db
    ),
):

    todo = (
        db.query(Todo)
        .filter(
            Todo.id
            == todo_id
        )
        .first()
    )


    if not todo:

        raise HTTPException(
            status_code=404,
            detail=(
                "할 일을 찾을 수 없습니다."
            ),
        )


    todo.completed = (
        data.completed
    )


    db.commit()

    db.refresh(todo)


    return todo


@app.patch(
    "/api/todos/{todo_id}",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def edit_todo(
    todo_id: int,
    data: TodoEdit,
    db: Session = Depends(
        get_db
    ),
):

    todo = (
        db.query(Todo)
        .filter(
            Todo.id
            == todo_id
        )
        .first()
    )


    if not todo:

        raise HTTPException(
            status_code=404,
            detail=(
                "할 일을 찾을 수 없습니다."
            ),
        )


    if (
        data.text
        is not None
    ):

        todo.text = (
            data.text
        )


    db.commit()

    db.refresh(todo)


    return todo


@app.delete(
    "/api/todos/{todo_id}",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def delete_todo(
    todo_id: int,
    db: Session = Depends(
        get_db
    ),
):

    todo = (
        db.query(Todo)
        .filter(
            Todo.id
            == todo_id
        )
        .first()
    )


    if not todo:

        raise HTTPException(
            status_code=404,
            detail=(
                "할 일을 찾을 수 없습니다."
            ),
        )


    db.delete(todo)

    db.commit()


    return {
        "success": True
    }


# =========================================================
# 메모
# =========================================================

@app.get(
    "/api/note",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def get_note(
    date: str,
    db: Session = Depends(
        get_db
    ),
):

    note = (
        db.query(DailyNote)
        .filter(
            DailyNote.date
            == date
        )
        .first()
    )


    if not note:

        return {
            "date": date,
            "text": "",
        }


    return note


@app.put(
    "/api/note",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def save_note(
    data: NoteUpdate,
    db: Session = Depends(
        get_db
    ),
):

    note = (
        db.query(DailyNote)
        .filter(
            DailyNote.date
            == data.date
        )
        .first()
    )


    if not note:

        note = DailyNote(

            date=data.date,

            text=data.text,
        )


        db.add(note)


    else:

        note.text = (
            data.text
        )


    db.commit()

    db.refresh(note)


    return note


# =========================================================
# 달력
# =========================================================

@app.get(
    "/api/calendar",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def get_calendar_data(
    year: int,
    month: int,
    db: Session = Depends(
        get_db
    ),
):

    try:

        first_day = date(
            year,
            month,
            1,
        )


    except ValueError:

        raise HTTPException(
            status_code=400,
            detail=(
                "잘못된 연도 또는 월입니다."
            ),
        )


    if month == 12:

        next_month = date(
            year + 1,
            1,
            1,
        )


    else:

        next_month = date(
            year,
            month + 1,
            1,
        )


    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.date
            < next_month.isoformat()
        )
        .all()
    )


    todos = (
        db.query(Todo)
        .filter(
            Todo.date
            >= first_day.isoformat(),

            Todo.date
            < next_month.isoformat(),
        )
        .all()
    )


    result = {}


    current_day = (
        first_day
    )


    while (
        current_day
        < next_month
    ):

        date_string = (
            current_day
            .isoformat()
        )


        schedule_count = 0

        important_count = 0


        for schedule in schedules:

            if schedule_occurs_on(
                schedule,
                date_string,
            ):

                schedule_count += 1


                if (
                    schedule.important
                ):

                    important_count += 1


        if (
            schedule_count > 0
        ):

            result[
                date_string
            ] = {

                "schedule_count":
                    schedule_count,

                "todo_count":
                    0,

                "important_count":
                    important_count,
            }


        current_day += timedelta(
            days=1
        )


    for todo in todos:

        if (
            todo.date
            not in result
        ):

            result[
                todo.date
            ] = {

                "schedule_count":
                    0,

                "todo_count":
                    0,

                "important_count":
                    0,
            }


        result[
            todo.date
        ][
            "todo_count"
        ] += 1


    return result


# =========================================================
# 검색
# =========================================================

@app.get(
    "/api/search",
    dependencies=[
        Depends(
            require_login
        )
    ],
)
def search_diary(
    q: str,
    db: Session = Depends(
        get_db
    ),
):

    keyword = (
        q.strip()
    )


    if not keyword:

        return []


    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.text.contains(
                keyword
            )
        )
        .all()
    )


    todos = (
        db.query(Todo)
        .filter(
            Todo.text.contains(
                keyword
            )
        )
        .all()
    )


    notes = (
        db.query(DailyNote)
        .filter(
            DailyNote.text.contains(
                keyword
            )
        )
        .all()
    )


    results = []


    for schedule in schedules:

        results.append({

            "type":
                "schedule",

            "id":
                schedule.id,

            "date":
                schedule.date,

            "time":
                schedule.time,

            "text":
                schedule.text,

            "completed":
                bool(
                    schedule.completed
                ),

            "category":
                schedule.category
                or
                "daily",

            "important":
                bool(
                    schedule.important
                ),

            "repeat_type":
                schedule.repeat_type
                or
                "none",

            "repeat_until":
                schedule.repeat_until,
        })


    for todo in todos:

        results.append({

            "type":
                "todo",

            "id":
                todo.id,

            "date":
                todo.date,

            "time":
                None,

            "text":
                todo.text,

            "completed":
                bool(
                    todo.completed
                ),

            "category":
                None,

            "important":
                False,

            "repeat_type":
                "none",

            "repeat_until":
                None,
        })


    for note in notes:

        results.append({

            "type":
                "note",

            "id":
                note.id,

            "date":
                note.date,

            "time":
                None,

            "text":
                note.text,

            "completed":
                False,

            "category":
                None,

            "important":
                False,

            "repeat_type":
                "none",

            "repeat_until":
                None,
        })


    results.sort(
        key=lambda item: (
            item["date"],
            item["time"] or "",
        ),
        reverse=True,
    )


    return results