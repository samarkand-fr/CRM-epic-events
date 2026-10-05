"""
Event Domain Controller Module (controllers/event_controller.py).

This module handles domain logic for Event scheduling and assignments:
1. Listing events with support and ownership filters.
2. Creating events for SIGNED contracts (Restricted to COMMERCIAL department).
3. Updating event information (Restricted to assigned SUPPORT or GESTION department).
"""

from datetime import datetime
from db import SessionLocal
from models import Event, Contract, User
from permissions import check_permission, has_role
from logger import log_exception


def get_all_events(filter_no_support: bool = False, filter_my_events: bool = False, current_user=None) -> list[Event]:
    """
    Retrieves event records with optional query filters.

    Args:
        filter_no_support (bool): If True, filters events where support_contact_id is None.
        filter_my_events (bool): If True, filters events assigned to current_user.
        current_user: Active authenticated user session.

    Returns:
        list[Event]: List of Event ORM entities.
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


def create_event(
    title: str,
    contract_id: int,
    event_date_start: datetime,
    event_date_end: datetime,
    location: str,
    attendees: int = 0,
    notes: str | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Creates a new event associated with a SIGNED commercial contract.

    Step 1: Verify permissions (Restricted to COMMERCIAL department).
    Step 2: Validate mandatory title, location, and date logic (start < end).
    Step 3: Retrieve contract and verify commercial responsibility ownership.
    Step 4: CRITICAL BUSINESS RULE: Verify contract signature status (is_signed == True).
    Step 5: Persist Event record to PostgreSQL database.

    Args:
        title (str): Title/Name of the event.
        contract_id (int): ID of associated signed contract.
        event_date_start (datetime): Event start timestamp.
        event_date_end (datetime): Event end timestamp.
        location (str): Physical or virtual venue address.
        attendees (int): Expected guest count.
        notes (str | None): Optional organizational details.
        current_user (User): Authenticated active commercial representative.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: RBAC Permission Verification
    allowed, msg = check_permission(current_user, ["COMMERCIAL"])
    if not allowed:
        return False, msg

    # Step 2: Validate required fields and dates
    if not title or not location:
        return False, "Event title and location are required."

    if event_date_start >= event_date_end:
        return False, "Start date and time must be prior to end date and time."

    db = SessionLocal()
    try:
        # Step 3: Retrieve contract and check ownership
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False, f"Contract ID #{contract_id} not found."

        if contract.commercial_contact_id != current_user.id and contract.client.commercial_contact_id != current_user.id:
            return False, f"Access denied: You are not the commercial contact responsible for contract #{contract.id}."

        # Step 4: CRITICAL BUSINESS RULE - Contract MUST be signed!
        if not contract.is_signed:
            return False, f"Cannot create event: Contract #{contract.id} has not been signed by the client yet."

        # Step 5: Save Event entity
        new_event = Event(
            title=title,
            contract_id=contract.id,
            client_id=contract.client_id,
            event_date_start=event_date_start,
            event_date_end=event_date_end,
            support_contact_id=None,  # Unassigned initially; GESTION team assigns support later
            location=location,
            attendees=attendees,
            notes=notes,
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return True, f"Event '{new_event.title}' (ID #{new_event.id}) created successfully for contract #{contract.id}."
    except Exception as e:
        db.rollback()
        log_exception(e, extra={"action": "create_event", "contract_id": contract_id})
        return False, f"Error creating event: {e}"
    finally:
        db.close()


def update_event(
    event_id: int,
    title: str | None = None,
    event_date_start: datetime | None = None,
    event_date_end: datetime | None = None,
    location: str | None = None,
    attendees: int | None = None,
    notes: str | None = None,
    support_contact_id: int | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Updates an existing event.

    Step 1: Check permissions (Restricted to GESTION or SUPPORT teams).
    Step 2: Fetch event record from database.
    Step 3: If user is SUPPORT, verify assignment ownership to this event.
    Step 4: Update fields and allow GESTION department to assign/change Support contact.
    Step 5: Commit changes to PostgreSQL database.

    Args:
        event_id (int): Target event database ID.
        title (str | None): Optional updated title.
        event_date_start (datetime | None): Optional updated start timestamp.
        event_date_end (datetime | None): Optional updated end timestamp.
        location (str | None): Optional updated location.
        attendees (int | None): Optional updated attendee count.
        notes (str | None): Optional updated event notes.
        support_contact_id (int | None): Optional assigned Support employee ID (GESTION only).
        current_user (User): Authenticated user session.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: Permission check
    allowed, msg = check_permission(current_user, ["GESTION", "SUPPORT"])
    if not allowed:
        return False, msg

    if (
        title is None
        and event_date_start is None
        and event_date_end is None
        and location is None
        and attendees is None
        and notes is None
        and support_contact_id is None
    ):
        return False, "No update parameters provided. Please specify at least one attribute to update (e.g. --location, --notes, --attendees)."

    db = SessionLocal()
    try:
        # Step 2: Retrieve Event record
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return False, f"Event ID #{event_id} not found."

        # Step 3: Check Support user ownership
        if has_role(current_user, "SUPPORT") and not has_role(current_user, "GESTION"):
            if event.support_contact_id != current_user.id:
                return False, f"Access denied: You are not the assigned support contact for event #{event.id}."
            if support_contact_id is not None:
                return False, "Only GESTION department can re-assign the support contact for an event."

        # Step 4: Apply field updates
        if title:
            event.title = title
        if location:
            event.location = location
        if attendees is not None:
            if attendees < 0:
                return False, "Attendee count must be a positive number or zero."
            event.attendees = attendees
        if notes is not None:
            event.notes = notes

        # Date validation check
        new_start = event_date_start if event_date_start else event.event_date_start
        new_end = event_date_end if event_date_end else event.event_date_end
        if new_start >= new_end:
            return False, "Start date and time must be prior to end date and time."
        event.event_date_start = new_start
        event.event_date_end = new_end

        # GESTION department assigning support contact
        if support_contact_id is not None:
            if not has_role(current_user, "GESTION"):
                return False, "Only GESTION department can assign support contacts to events."
            support_user = db.query(User).filter(User.id == support_contact_id).first()
            if not support_user:
                return False, f"Collaborator ID #{support_contact_id} not found."
            if not has_role(support_user, "SUPPORT"):
                return False, f"Collaborator {support_user.full_name} does not belong to the SUPPORT department."
            event.support_contact_id = support_user.id

        # Step 5: Save updates
        db.commit()
        db.refresh(event)
        support_str = event.support_contact.full_name if event.support_contact else "Unassigned"
        return True, f"Event #{event.id} ({event.title}) updated successfully (Assigned Support: {support_str})."
    except Exception as e:
        db.rollback()
        log_exception(e, extra={"action": "update_event", "event_id": event_id})
        return False, f"Error updating event: {e}"
    finally:
        db.close()

