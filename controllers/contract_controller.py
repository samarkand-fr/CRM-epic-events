"""
Contract Domain Controller Module (controllers/contract_controller.py).

This module manages financial commercial contracts:
1. Fetching contracts with optional status filters (unsigned, balance due).
2. Creating new contracts (Restricted to GESTION department; logs Sentry event on signature).
3. Updating contracts (Restricted to GESTION or responsible COMMERCIAL representative; logs Sentry event on signature).
"""

from db import SessionLocal
from models import Contract, Client, User
from permissions import check_permission, has_role
from logger import log_event


def get_all_contracts(filter_unsigned: bool = False, filter_unpaid: bool = False) -> list[Contract]:
    """
    Retrieves all commercial contracts with optional query filters.

    Args:
        filter_unsigned (bool): If True, filters contracts where is_signed is False.
        filter_unpaid (bool): If True, filters contracts with amount_due > 0.

    Returns:
        list[Contract]: Filtered Contract ORM entities.
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
    Creates a new commercial contract.

    Step 1: Check permissions (Restricted to GESTION department).
    Step 2: Validate positive numeric values for total amount and amount due.
    Step 3: Resolve Client and assigned Commercial representative.
    Step 4: Save contract record to PostgreSQL DB.
    Step 5: Log audit event to Sentry.io if contract is signed upon creation.

    Args:
        client_id (int): Target client database ID.
        total_amount (float): Total contract price (€).
        amount_due (float): Outstanding balance due (€).
        is_signed (bool): Initial signature status.
        commercial_contact_id (int | None): Optional assigned commercial user ID.
        current_user (User): Authenticated user session.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: Permission check
    allowed, msg = check_permission(current_user, ["GESTION"])
    if not allowed:
        return False, msg

    # Step 2: Validate amounts
    if total_amount < 0 or amount_due < 0:
        return False, "Financial amounts (total and balance due) must be positive numbers or zero."

    db = SessionLocal()
    try:
        # Step 3: Resolve Client entity
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False, f"Client ID #{client_id} not found."

        comm_id = commercial_contact_id if commercial_contact_id else client.commercial_contact_id
        commercial = db.query(User).filter(User.id == comm_id).first()
        if not commercial:
            return False, f"Commercial contact ID #{comm_id} not found."

        # Step 4: Create Contract record
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

        # Step 5: Audit Event Logging to Sentry.io if created as signed
        if is_signed:
            log_event(
                message=f"Contract Signed: Contract #{new_contract.id} signed for client '{client.full_name}' (Total: {new_contract.total_amount:.2f}€)",
                level="info",
                extra={
                    "contract_id": new_contract.id,
                    "client_id": client.id,
                    "client_name": client.full_name,
                    "total_amount": new_contract.total_amount,
                    "author_emp_num": current_user.employee_number if current_user else "System",
                },
            )

        return True, f"Contract #{new_contract.id} created successfully for client '{client.full_name}' (Total: {new_contract.total_amount:.2f}€)."
    except Exception as e:
        db.rollback()
        return False, f"Error creating contract: {e}"
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
    Updates an existing commercial contract.

    Step 1: Verify permissions (Allowed: GESTION or responsible COMMERCIAL representative).
    Step 2: Retrieve target Contract record.
    Step 3: Track signature transition state (unsigned -> signed).
    Step 4: Update fields and commit database transaction.
    Step 5: Trigger Sentry.io audit event if contract signature status changed to signed.

    Args:
        contract_id (int): Target contract database ID.
        total_amount (float | None): Optional updated total price.
        amount_due (float | None): Optional updated balance due.
        is_signed (bool | None): Optional updated signature state.
        commercial_contact_id (int | None): Optional re-assigned commercial ID (GESTION only).
        current_user (User): Authenticated active user session.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: Permission verification
    allowed, msg = check_permission(current_user, ["GESTION", "COMMERCIAL"])
    if not allowed:
        return False, msg

    if total_amount is None and amount_due is None and is_signed is None and commercial_contact_id is None:
        return False, "No update parameters provided. Please specify at least one attribute to update (e.g. --total-amount, --amount-due, --signed)."

    db = SessionLocal()
    try:
        # Step 2: Fetch contract
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False, f"Contract ID #{contract_id} not found."

        # Verify commercial ownership restriction
        if has_role(current_user, "COMMERCIAL") and not has_role(current_user, "GESTION"):
            if contract.commercial_contact_id != current_user.id and contract.client.commercial_contact_id != current_user.id:
                return False, f"Access denied: You are not the commercial contact responsible for contract #{contract.id}."

        # Step 3: Track signature status change
        was_signed_before = contract.is_signed

        if total_amount is not None:
            if total_amount < 0:
                return False, "Total contract amount must be a positive number."
            contract.total_amount = total_amount

        if amount_due is not None:
            if amount_due < 0:
                return False, "Amount due must be a positive number or zero."
            contract.amount_due = amount_due

        if is_signed is not None:
            contract.is_signed = is_signed

        if commercial_contact_id is not None:
            if not has_role(current_user, "GESTION"):
                return False, "Only GESTION department can re-assign the commercial contact of a contract."
            comm = db.query(User).filter(User.id == commercial_contact_id).first()
            if not comm:
                return False, f"Commercial ID #{commercial_contact_id} not found."
            contract.commercial_contact_id = comm.id

        # Step 4: Save updates
        db.commit()
        db.refresh(contract)

        # Step 5: Audit Event Logging to Sentry.io on signature transition
        if not was_signed_before and contract.is_signed:
            log_event(
                message=f"Contract Signed: Contract #{contract.id} signed for client '{contract.client.full_name}' (Total: {contract.total_amount:.2f}€)",
                level="info",
                extra={
                    "contract_id": contract.id,
                    "client_id": contract.client_id,
                    "client_name": contract.client.full_name,
                    "total_amount": contract.total_amount,
                    "author_emp_num": current_user.employee_number if current_user else "System",
                },
            )

        status_str = "Signed" if contract.is_signed else "Unsigned"
        return True, f"Contract #{contract.id} updated successfully (Status: {status_str}, Balance Due: {contract.amount_due:.2f}€)."
    except Exception as e:
        db.rollback()
        return False, f"Error updating contract: {e}"
    finally:
        db.close()

