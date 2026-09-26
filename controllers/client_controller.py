from db import SessionLocal
from models import Client, User
from permissions import check_permission


def get_all_clients() -> list[Client]:
    """Retrieves all clients from database with their assigned commercial contact."""
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
    Restricted to COMMERCIAL department.
    Client is automatically assigned to current_user (commercial).
    """
    allowed, msg = check_permission(current_user, ["COMMERCIAL"])
    if not allowed:
        return False, msg

    if not full_name or not email:
        return False, "Le nom complet et l'email du client sont obligatoires."

    db = SessionLocal()
    try:
        existing = db.query(Client).filter(Client.email == email).first()
        if existing:
            return False, f"Un client avec l'email '{email}' existe déjà."

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
        return True, f"Client '{new_client.full_name}' créé avec succès et attribué à {current_user.full_name}."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la création du client : {e}"
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
    Restricted to COMMERCIAL department (must be the assigned commercial for this client).
    """
    allowed, msg = check_permission(current_user, ["COMMERCIAL"])
    if not allowed:
        return False, msg

    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False, f"Client ID #{client_id} introuvable."

        if client.commercial_contact_id != current_user.id:
            return False, f"Accès refusé : Vous n'êtes pas le commercial responsable du client #{client.id} ({client.full_name})."

        if full_name:
            client.full_name = full_name
        if email and email != client.email:
            existing = db.query(Client).filter(Client.email == email).first()
            if existing:
                return False, f"L'email '{email}' est déjà utilisé par un autre client."
            client.email = email
        if phone:
            client.phone = phone
        if company_name:
            client.company_name = company_name

        db.commit()
        db.refresh(client)
        return True, f"Client #{client.id} ({client.full_name}) mis à jour avec succès."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la mise à jour du client : {e}"
    finally:
        db.close()
