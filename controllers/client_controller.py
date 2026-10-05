"""
Client Domain Controller Module (controllers/client_controller.py).

This module handles business operations and persistence for Client entities:
1. Fetching all client records from PostgreSQL.
2. Creating new client entries (Restricted to COMMERCIAL department; auto-assigned to author).
3. Updating client contact details (Restricted to assigned COMMERCIAL representative).
"""

from db import SessionLocal
from models import Client, User
from permissions import check_permission
from logger import log_exception


def get_all_clients() -> list[Client]:
    """
    Retrieves all clients ordered by ID ascending with eager loaded commercial contact.

    Returns:
        list[Client]: List of Client ORM instances.
    """
    db = SessionLocal()
    try:
        clients = db.query(Client).order_by(Client.id.asc()).all()
        return clients
    finally:
        db.close()


def create_client(
    full_name: str,
    email: str,
    phone: str | None = None,
    company_name: str | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Creates a new client account.

    Step 1: Verify user permissions (Restricted to COMMERCIAL team).
    Step 2: Check required input fields (full name and email).
    Step 3: Ensure email uniqueness across client records.
    Step 4: Save Client record automatically assigned to active commercial representative.

    Args:
        full_name (str): Client full name.
        email (str): Client contact email.
        phone (str | None): Optional contact phone number.
        company_name (str | None): Optional organization/company name.
        current_user (User): Authenticated commercial representative.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: Permission check
    allowed, msg = check_permission(current_user, ["COMMERCIAL"])
    if not allowed:
        return False, msg

    # Step 2: Input validation
    if not full_name or not email:
        return False, "Client full name and email address are required."

    db = SessionLocal()
    try:
        # Step 3: Check email uniqueness
        existing = db.query(Client).filter(Client.email == email).first()
        if existing:
            return False, f"A client with email '{email}' already exists."

        # Step 4: Add and commit new client
        new_client = Client(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            commercial_contact_id=current_user.id,
        )
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return True, f"Client '{new_client.full_name}' created successfully and assigned to {current_user.full_name}."
    except Exception as e:
        db.rollback()
        log_exception(e, extra={"action": "create_client", "email": email})
        return False, f"Error creating client: {e}"
    finally:
        db.close()


def update_client(
    client_id: int,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    company_name: str | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Updates an existing client account.

    Step 1: Check permissions (Restricted to COMMERCIAL department).
    Step 2: Verify that the current user is the commercial representative responsible for this client.
    Step 3: Apply modifications to client fields.
    Step 4: Commit changes to PostgreSQL database.

    Args:
        client_id (int): Target client database ID.
        full_name (str | None): Optional updated full name.
        email (str | None): Optional updated email address.
        phone (str | None): Optional updated phone number.
        company_name (str | None): Optional updated company name.
        current_user (User): Authenticated active user session.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: Permission check
    allowed, msg = check_permission(current_user, ["COMMERCIAL"])
    if not allowed:
        return False, msg

    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False, f"Client ID #{client_id} not found."

        # Step 2: Commercial ownership verification
        if client.commercial_contact_id != current_user.id:
            return False, f"Access denied: You are not the commercial contact assigned to client #{client.id} ({client.full_name})."

        # Step 3: Apply updates
        if full_name:
            client.full_name = full_name
        if email and email != client.email:
            existing = db.query(Client).filter(Client.email == email).first()
            if existing:
                return False, f"Email '{email}' is already in use by another client."
            client.email = email
        if phone:
            client.phone = phone
        if company_name:
            client.company_name = company_name

        # Step 4: Commit transaction
        db.commit()
        db.refresh(client)
        return True, f"Client #{client.id} ({client.full_name}) updated successfully."
    except Exception as e:
        db.rollback()
        log_exception(e, extra={"action": "update_client", "client_id": client_id})
        return False, f"Error updating client: {e}"
    finally:
        db.close()

