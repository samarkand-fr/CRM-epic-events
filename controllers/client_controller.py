from db import SessionLocal
from models import Client


def get_all_clients() -> list[Client]:
    """Retrieves all clients from database with their assigned commercial contact."""
    db = SessionLocal()
    try:
        clients = db.query(Client).order_by(Client.id.asc()).all()
        return clients
    finally:
        db.close()
