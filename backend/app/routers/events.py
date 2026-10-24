from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Event, Registration
from app.schemas import EventOut, RegistrationCreate
from app.services import events_out, registration_counts, to_event_out

router = APIRouter()


@router.get("", response_model=list[EventOut])
def list_events(
    q: str = Query(default="", max_length=100),
    category: str = Query(default="", max_length=40),
    sort: str = Query(default="date", pattern="^(date|date_desc)$"),
    db: Session = Depends(get_db),
):
    stmt = select(Event).where(Event.status != "completed")
    q = q.strip()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Event.title.ilike(like) | Event.description.ilike(like) | Event.venue.ilike(like))
    if category and category != "All":
        stmt = stmt.where(Event.category == category)
    stmt = stmt.order_by(Event.starts_at.desc() if sort == "date_desc" else Event.starts_at.asc())
    return events_out(db, list(db.scalars(stmt)))


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return to_event_out(event, registration_counts(db, [event.id]).get(event.id, 0))


@router.post("/{event_id}/registrations", status_code=201)
def register(event_id: int, payload: RegistrationCreate, db: Session = Depends(get_db)):
    # Lock the event row so two people can't take the last seat at once.
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status == "completed":
        raise HTTPException(status_code=400, detail="Registration is closed for this event")
    count = registration_counts(db, [event.id]).get(event.id, 0)
    if count >= event.capacity:
        raise HTTPException(status_code=409, detail="This event is fully booked")
    normalized = str(payload.email).strip().lower()
    registration = Registration(
        event_id=event.id,
        full_name=payload.full_name,
        email=str(payload.email).strip(),
        normalized_email=normalized,
        contact_number=payload.contact_number,
    )
    db.add(registration)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This email is already registered for this event") from None
    return {"id": registration.id, "event_id": event.id, "message": "Registration confirmed"}
