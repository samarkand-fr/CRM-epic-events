from datetime import datetime
from db import SessionLocal
from models import Event, Contract, User
from permissions import check_permission, has_role


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
    Creates a new event for a signed contract.
    Restricted to COMMERCIAL department.
    Commercial must be responsible for the contract/client.
    Contract MUST be signed (is_signed == True).
    """
    allowed, msg = check_permission(current_user, ["COMMERCIAL"])
    if not allowed:
        return False, msg

    if not title or not location:
        return False, "Le titre et le lieu de l'événement sont obligatoires."

    if event_date_start >= event_date_end:
        return False, "La date de début doit être antérieure à la date de fin."

    db = SessionLocal()
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False, f"Contrat ID #{contract_id} introuvable."

        # Check commercial ownership
        if contract.commercial_contact_id != current_user.id and contract.client.commercial_contact_id != current_user.id:
            return False, f"Accès refusé : Vous n'êtes pas le commercial responsable du contrat #{contract.id}."

        # CRITICAL BUSINESS RULE: Contract MUST be signed!
        if not contract.is_signed:
            return False, f"Impossible de créer un événement : Le contrat #{contract.id} n'est pas encore signé par le client."

        new_event = Event(
            title=title,
            contract_id=contract.id,
            client_id=contract.client_id,
            event_date_start=event_date_start,
            event_date_end=event_date_end,
            support_contact_id=None,  # Initially no support assigned; assigned later by GESTION
            location=location,
            attendees=attendees,
            notes=notes,
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return True, f"Événement '{new_event.title}' (ID #{new_event.id}) créé avec succès pour le contrat #{contract.id}."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la création de l'événement : {e}"
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
    - GESTION: Can assign/change support_contact_id or update details.
    - SUPPORT: Can update event details (location, dates, notes, attendees) IF assigned to the event.
    """
    allowed, msg = check_permission(current_user, ["GESTION", "SUPPORT"])
    if not allowed:
        return False, msg

    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return False, f"Événement ID #{event_id} introuvable."

        # If user is SUPPORT, check if assigned to this event
        if has_role(current_user, "SUPPORT") and not has_role(current_user, "GESTION"):
            if event.support_contact_id != current_user.id:
                return False, f"Accès refusé : Vous n'êtes pas le collaborateur support responsable de l'événement #{event.id}."
            if support_contact_id is not None:
                return False, "Seule l'équipe de Gestion peut ré-attribuer le contact support d'un événement."

        if title:
            event.title = title
        if location:
            event.location = location
        if attendees is not None:
            if attendees < 0:
                return False, "Le nombre de participants doit être positif ou nul."
            event.attendees = attendees
        if notes is not None:
            event.notes = notes

        # Dates validation
        new_start = event_date_start if event_date_start else event.event_date_start
        new_end = event_date_end if event_date_end else event.event_date_end
        if new_start >= new_end:
            return False, "La date de début doit être antérieure à la date de fin."
        event.event_date_start = new_start
        event.event_date_end = new_end

        # GESTION role assigning support contact
        if support_contact_id is not None:
            if not has_role(current_user, "GESTION"):
                return False, "Seule l'équipe de Gestion peut désigner le support responsable d'un événement."
            support_user = db.query(User).filter(User.id == support_contact_id).first()
            if not support_user:
                return False, f"Collaborateur ID #{support_contact_id} introuvable."
            if not has_role(support_user, "SUPPORT"):
                return False, f"Le collaborateur {support_user.full_name} n'appartient pas au département SUPPORT."
            event.support_contact_id = support_user.id

        db.commit()
        db.refresh(event)
        support_str = event.support_contact.full_name if event.support_contact else "Non attribué"
        return True, f"Événement #{event.id} ({event.title}) mis à jour avec succès (Support: {support_str})."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la mise à jour de l'événement : {e}"
    finally:
        db.close()
