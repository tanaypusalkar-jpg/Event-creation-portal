from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Event, Registration
from app.schemas import EventOut


def registration_counts(db: Session, event_ids: list[int]) -> dict[int, int]:
    if not event_ids:
        return {}
    rows = db.execute(
        select(Registration.event_id, func.count(Registration.id))
        .where(Registration.event_id.in_(event_ids))
        .group_by(Registration.event_id)
    ).all()
    return {event_id: count for event_id, count in rows}


def to_event_out(event: Event, count: int) -> EventOut:
    out = EventOut.model_validate(event)
    out.registration_count = count
    out.available_seats = max(event.capacity - count, 0)
    return out


def events_out(db: Session, events: list[Event]) -> list[EventOut]:
    counts = registration_counts(db, [e.id for e in events])
    return [to_event_out(e, counts.get(e.id, 0)) for e in events]
