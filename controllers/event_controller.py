from db import SessionLocal
from models import Event


def get_all_events(filter_no_support: bool = False, filter_my_events: bool = False, current_user=None) -> list[Event]:
    """
    Retrieves all events with optional filters:
    - filter_no_support: return events where support_contact_id is None.
    - filter_my_events: return events assigned to current_user.
    """
    db = SessionLocal()
    try:
        query = db.query(Event)
        if filter_no_support:
            query = query.filter(Event.support_contact_id == None)
        if filter_my_events and current_user:
            query = query.filter(Event.support_contact_id == current_user.id)
        events = query.order_by(Event.id.asc()).all()
        return events
    finally:
        db.close()
