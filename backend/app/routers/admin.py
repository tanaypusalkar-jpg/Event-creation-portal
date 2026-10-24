from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_admin
from app.models import Event, Registration
from app.schemas import DashboardOut, EventCreate, EventOut, EventUpdate, RegistrationOut
from app.services import events_out, registration_counts, to_event_out

router = APIRouter(dependencies=[Depends(require_admin)])


def _check_dates(starts_at, ends_at):
    if ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="End time must be after the start time")


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Event.id))) or 0
    upcoming = db.scalar(select(func.count(Event.id)).where(Event.status == "upcoming")) or 0
    completed = db.scalar(select(func.count(Event.id)).where(Event.status == "completed")) or 0
    regs = db.scalar(select(func.count(Registration.id))) or 0
    return DashboardOut(
        total_events=total,
        upcoming_events=upcoming,
        total_registrations=regs,
        completed_events=completed,
    )


@router.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return events_out(db, list(db.scalars(select(Event).order_by(Event.starts_at.desc()))))


@router.post("/events", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    _check_dates(payload.starts_at, payload.ends_at)
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return to_event_out(event, 0)


@router.patch("/events/{event_id}", response_model=EventOut)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    data = payload.model_dump(exclude_unset=True)
    for required in ("title", "venue", "category", "starts_at", "ends_at", "capacity", "status"):
        if required in data and data[required] is None:
            raise HTTPException(status_code=422, detail=f"{required} cannot be empty")
    for key, value in data.items():
        if key in ("title", "venue") and isinstance(value, str):
            value = value.strip()
        setattr(event, key, value)
    _check_dates(event.starts_at, event.ends_at)
    count = registration_counts(db, [event.id]).get(event.id, 0)
    if event.capacity < count:
        raise HTTPException(
            status_code=409, detail=f"Capacity cannot be lower than current registrations ({count})"
        )
    db.commit()
    db.refresh(event)
    return to_event_out(event, count)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return Response(status_code=204)


@router.get("/events/{event_id}/registrations", response_model=list[RegistrationOut])
def event_registrations(event_id: int, db: Session = Depends(get_db)):
    if not db.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    rows = db.scalars(
        select(Registration).where(Registration.event_id == event_id).order_by(Registration.created_at.desc())
    )
    return [RegistrationOut.model_validate(r, from_attributes=True) for r in rows]
