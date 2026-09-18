from db import SessionLocal
from models import Contract


def get_all_contracts(filter_unsigned: bool = False, filter_unpaid: bool = False) -> list[Contract]:
    """
    Retrieves all contracts with optional filters:
    - filter_unsigned: return contracts where is_signed is False.
    - filter_unpaid: return contracts where amount_due > 0.
    """
    db = SessionLocal()
    try:
        query = db.query(Contract)
        if filter_unsigned:
            query = query.filter(Contract.is_signed == False)
        if filter_unpaid:
            query = query.filter(Contract.amount_due > 0)
        contracts = query.order_by(Contract.id.asc()).all()
        return contracts
    finally:
        db.close()
