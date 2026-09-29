from db import SessionLocal
from models import Contract, Client, User
from permissions import check_permission, has_role
from logger import log_event


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


def create_contract(
    client_id: int,
    total_amount: float,
    amount_due: float,
    is_signed: bool = False,
    commercial_contact_id: int | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Creates a new contract for a client.
    Restricted to GESTION department.
    Logs Sentry audit event if the contract is signed at creation.
    """
    allowed, msg = check_permission(current_user, ["GESTION"])
    if not allowed:
        return False, msg

    if total_amount < 0 or amount_due < 0:
        return False, "Les montants (total et reste à payer) doivent être positifs ou nuls."

    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False, f"Client ID #{client_id} introuvable."

        comm_id = commercial_contact_id if commercial_contact_id else client.commercial_contact_id
        commercial = db.query(User).filter(User.id == comm_id).first()
        if not commercial:
            return False, f"Contact commercial ID #{comm_id} introuvable."

        new_contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial.id,
            total_amount=total_amount,
            amount_due=amount_due,
            is_signed=is_signed,
        )
        db.add(new_contract)
        db.commit()
        db.refresh(new_contract)

        # Audit Event Logging to Sentry if contract created as signed
        if is_signed:
            log_event(
                message=f"Signature de contrat : Contrat #{new_contract.id} signé pour le client '{client.full_name}' (Montant: {new_contract.total_amount:.2f}€)",
                level="info",
                extra={
                    "contract_id": new_contract.id,
                    "client_id": client.id,
                    "client_name": client.full_name,
                    "total_amount": new_contract.total_amount,
                    "author_emp_num": current_user.employee_number if current_user else "System",
                },
            )

        return True, f"Contrat #{new_contract.id} créé avec succès pour le client '{client.full_name}' (Total: {new_contract.total_amount:.2f}€)."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la création du contrat : {e}"
    finally:
        db.close()


def update_contract(
    contract_id: int,
    total_amount: float | None = None,
    amount_due: float | None = None,
    is_signed: bool | None = None,
    commercial_contact_id: int | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Updates an existing contract.
    Restricted to GESTION or COMMERCIAL (responsible for the contract).
    Logs Sentry audit event when contract is signed (is_signed passes to True).
    """
    allowed, msg = check_permission(current_user, ["GESTION", "COMMERCIAL"])
    if not allowed:
        return False, msg

    db = SessionLocal()
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False, f"Contrat ID #{contract_id} introuvable."

        if has_role(current_user, "COMMERCIAL") and not has_role(current_user, "GESTION"):
            if contract.commercial_contact_id != current_user.id and contract.client.commercial_contact_id != current_user.id:
                return False, f"Accès refusé : Vous n'êtes pas le commercial responsable du contrat #{contract.id}."

        was_signed_before = contract.is_signed

        if total_amount is not None:
            if total_amount < 0:
                return False, "Le montant total doit être positif."
            contract.total_amount = total_amount

        if amount_due is not None:
            if amount_due < 0:
                return False, "Le reste à payer doit être positif ou nul."
            contract.amount_due = amount_due

        if is_signed is not None:
            contract.is_signed = is_signed

        if commercial_contact_id is not None:
            if not has_role(current_user, "GESTION"):
                return False, "Seule l'équipe de Gestion peut modifier le commercial attribué au contrat."
            comm = db.query(User).filter(User.id == commercial_contact_id).first()
            if not comm:
                return False, f"Commercial ID #{commercial_contact_id} introuvable."
            contract.commercial_contact_id = comm.id

        db.commit()
        db.refresh(contract)

        # Audit Event Logging to Sentry on Contract Signature
        if not was_signed_before and contract.is_signed:
            log_event(
                message=f"Signature de contrat : Contrat #{contract.id} signé pour le client '{contract.client.full_name}' (Montant: {contract.total_amount:.2f}€)",
                level="info",
                extra={
                    "contract_id": contract.id,
                    "client_id": contract.client_id,
                    "client_name": contract.client.full_name,
                    "total_amount": contract.total_amount,
                    "author_emp_num": current_user.employee_number if current_user else "System",
                },
            )

        status_str = "Signé" if contract.is_signed else "Non signé"
        return True, f"Contrat #{contract.id} mis à jour avec succès (Statut: {status_str}, Reste à payer: {contract.amount_due:.2f}€)."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la mise à jour du contrat : {e}"
    finally:
        db.close()
