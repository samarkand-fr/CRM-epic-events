"""
Epic Events CRM - Main CLI Entry Point (epicevents.py).

This module is the application's command-line interface built with Click.
It initializes the Sentry.io logging SDK and orchestrates all CLI commands,
organized into five management areas:

  1. Authentication   : login, logout, whoami
  2. Users            : display-users, create-user, update-user    (GESTION only)
  3. Clients          : display-clients, create-client, update-client (COMMERCIAL only)
  4. Contracts        : display-contracts, create-contract, update-contract (GESTION / COMMERCIAL)
  5. Events           : display-events, create-event, update-event  (COMMERCIAL / GESTION / SUPPORT)

Architecture follows strict MVC separation:
  - Views   : Rich-formatted terminal output (views.py)
  - Controllers: Domain logic and DB access (controllers/)
  - Validators: Input validation before write operations (validators.py)
  - Permissions: RBAC enforcement via decorators (permissions.py)

Usage:
    python epicevents.py --help
    python epicevents.py login
    python epicevents.py display-clients
"""

import click
from logger import init_sentry, log_exception

# Step 1: Initialize Sentry.io SDK at application startup (before any controller imports)
init_sentry()

# Step 2: Import controllers (after Sentry is initialized to catch import-time errors)
from controllers.auth_controller import login_user, logout_user
from controllers.user_controller import get_all_users, create_user, update_user
from controllers.client_controller import get_all_clients, create_client, update_client
from controllers.contract_controller import get_all_contracts, create_contract, update_contract
from controllers.event_controller import get_all_events, create_event, update_event
from permissions import get_current_user, require_login, require_role
from validators import (
    validate_email,
    validate_employee_number,
    validate_date_format,
    validate_positive_amount,
)
from views import (
    display_success,
    display_error,
    display_warning,
    display_whoami_view,
    display_users_view,
    display_clients_view,
    display_contracts_view,
    display_events_view,
)


def safe_cli_wrapper(fn):
    """
    Decorator that wraps CLI functions with a global exception handler.

    Captures and logs any unexpected exceptions to Sentry.io, then
    displays a user-friendly error message without crashing the CLI.

    Args:
        fn (callable): Click command function to wrap.

    Returns:
        callable: Wrapped function with Sentry exception capture.
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except click.Abort:
            raise
        except Exception as e:
            log_exception(e)
            display_error(f"An unexpected error occurred: {e}")
    return wrapper


# Step 3: Define the root Click CLI group
@click.group()
def cli():
    """Epic Events CRM - Command Line Interface (CLI)."""
    pass


# ==========================================
# SECTION 1: AUTHENTICATION COMMANDS
# ==========================================

@cli.command()
@click.option("--identifier", prompt="Email or employee number", help="Email address or employee number (e.g. EMP001)")
@click.option("--password", prompt="Password", hide_input=True, help="Employee account password")
def login(identifier, password):
    """
    Authenticate to the Epic Events CRM platform and obtain a JWT session token.

    Step 1: Validate that both identifier and password are provided.
    Step 2: Call auth_controller.login_user() to verify credentials.
    Step 3: On success, the JWT session token is saved to ~/.epic_events_token.
    """
    try:
        # Step 1: Basic input presence check
        if not identifier or not password:
            display_error("Identifier and password are both required.")
            return

        # Step 2-3: Authenticate and store session token
        success, message = login_user(identifier, password)
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "login", "identifier": identifier})
        display_error(f"An error occurred during login: {e}")


@cli.command()
def logout():
    """
    Logout from the Epic Events CRM and delete the local JWT session token file.

    Removes ~/.epic_events_token so subsequent commands will require re-authentication.
    """
    try:
        logout_user()
        display_success("Logged out successfully. Session token removed.")
    except Exception as e:
        log_exception(e, extra={"action": "logout"})
        display_error(f"Error during logout: {e}")


@cli.command()
def whoami():
    """
    Display the currently authenticated user and validate the active session.

    Step 1: Read the persistent JWT session token from local file.
    Step 2: Decode and validate the token.
    Step 3: Load and display the user profile from the database.
    """
    try:
        user, err_code = get_current_user()
        if err_code == "TOKEN_EXPIRED":
            display_warning("Your session has expired. Please re-authenticate using 'python epicevents.py login'.")
        elif user:
            display_whoami_view(user)
        else:
            display_warning("No authenticated user found.")
    except Exception as e:
        log_exception(e, extra={"action": "whoami"})
        display_error(f"Error checking session: {e}")


# ==========================================
# SECTION 2: COLLABORATOR MANAGEMENT (GESTION TEAM)
# ==========================================

@cli.command(name="display-users")
@require_login  # Decorator: enforces active login session
def display_users():
    """
    Display the full list of all Epic Events collaborators (employees).

    Accessible to all authenticated users.
    """
    try:
        users = get_all_users()
        display_users_view(users)
    except Exception as e:
        log_exception(e, extra={"action": "display_users"})
        display_error(f"Error retrieving collaborators: {e}")


@cli.command(name="create-user")
@click.option("--emp-num", prompt="Employee number (e.g. EMP004)", help="Unique employee number")
@click.option("--full-name", prompt="Full name", help="Full name of the collaborator")
@click.option("--email", prompt="Professional email", help="Email address")
@click.option("--password", prompt="Initial password", hide_input=True, help="Account password")
@click.option("--role", prompt="Role (COMMERCIAL, SUPPORT, GESTION)", help="Department role")
@require_role("GESTION")  # Decorator: restricts access to GESTION department only
def cli_create_user(emp_num, full_name, email, password, role):
    """
    Create a new collaborator account (GESTION department only).

    Step 1: Validate employee number format.
    Step 2: Validate email format using regex.
    Step 3: Delegate to user_controller.create_user() with current authenticated user context.
    """
    try:
        # Step 1: Validate employee number format
        valid_emp, msg_emp = validate_employee_number(emp_num)
        if not valid_emp:
            display_error(msg_emp)
            return

        # Step 2: Validate email format
        valid_email, msg_email = validate_email(email)
        if not valid_email:
            display_error(msg_email)
            return

        # Step 3: Retrieve current user and create the collaborator
        user, _ = get_current_user()
        success, message = create_user(emp_num, full_name, email, password, role, current_user=user)
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "create_user", "emp_num": emp_num, "email": email})
        display_error(f"An error occurred: {e}")


@cli.command(name="update-user")
@click.option("--user-id", prompt="Collaborator ID to update", type=int, help="Collaborator database ID")
@click.option("--full-name", default=None, help="Updated full name")
@click.option("--email", default=None, help="Updated email address")
@click.option("--password", default=None, help="Updated password")
@click.option("--role", default=None, help="Updated role (COMMERCIAL, SUPPORT, GESTION)")
@require_role("GESTION")  # Decorator: restricts access to GESTION department only
def cli_update_user(user_id, full_name, email, password, role):
    """
    Update an existing collaborator account (GESTION department only).

    Step 1: Validate email format if provided.
    Step 2: Delegate to user_controller.update_user() with current user session.
    """
    try:
        # Step 1: Validate email if provided
        if email:
            valid_email, msg_email = validate_email(email)
            if not valid_email:
                display_error(msg_email)
                return

        # Step 2: Execute update
        user, _ = get_current_user()
        success, message = update_user(user_id, full_name, email, password, role, current_user=user)
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "update_user", "target_user_id": user_id})
        display_error(f"An error occurred: {e}")


# ==========================================
# SECTION 3: CLIENT MANAGEMENT (COMMERCIAL TEAM)
# ==========================================

@cli.command(name="display-clients")
@require_login  # Decorator: enforces active login session
def display_clients():
    """
    Display the full list of all Epic Events clients.

    Accessible to all authenticated users.
    """
    try:
        clients = get_all_clients()
        display_clients_view(clients)
    except Exception as e:
        log_exception(e, extra={"action": "display_clients"})
        display_error(f"Error retrieving clients: {e}")


@cli.command(name="create-client")
@click.option("--full-name", prompt="Client full name", help="Full name of the client")
@click.option("--email", prompt="Client email", help="Client email address")
@click.option("--phone", default=None, help="Contact phone number")
@click.option("--company", default=None, help="Company or organization name")
@require_role("COMMERCIAL")  # Decorator: restricts access to COMMERCIAL department only
def cli_create_client(full_name, email, phone, company):
    """
    Create a new client (COMMERCIAL department only).

    Step 1: Validate email format.
    Step 2: Create client and assign it to the current commercial representative.
    """
    try:
        # Step 1: Validate email
        valid_email, msg_email = validate_email(email)
        if not valid_email:
            display_error(msg_email)
            return

        # Step 2: Delegate to controller
        user, _ = get_current_user()
        success, message = create_client(full_name, email, phone, company, current_user=user)
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "create_client", "email": email})
        display_error(f"An error occurred: {e}")


@cli.command(name="update-client")
@click.option("--client-id", prompt="Client ID to update", type=int, help="Client database ID")
@click.option("--full-name", default=None, help="Updated full name")
@click.option("--email", default=None, help="Updated email address")
@click.option("--phone", default=None, help="Updated phone number")
@click.option("--company", default=None, help="Updated company name")
@require_role("COMMERCIAL")  # Decorator: restricts access to COMMERCIAL department only
def cli_update_client(client_id, full_name, email, phone, company):
    """
    Update a client account (COMMERCIAL - responsible representative only).

    Step 1: Validate email format if provided.
    Step 2: Verify commercial ownership in controller before applying changes.
    """
    try:
        # Step 1: Validate email if provided
        if email:
            valid_email, msg_email = validate_email(email)
            if not valid_email:
                display_error(msg_email)
                return

        # Step 2: Execute update
        user, _ = get_current_user()
        success, message = update_client(client_id, full_name, email, phone, company, current_user=user)
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "update_client", "client_id": client_id})
        display_error(f"An error occurred: {e}")


# ==========================================
# SECTION 4: CONTRACT MANAGEMENT (GESTION & COMMERCIAL)
# ==========================================

@cli.command(name="display-contracts")
@click.option("--unsigned", is_flag=True, help="Filter to unsigned contracts only")
@click.option("--unpaid", is_flag=True, help="Filter to contracts with balance due only")
@require_login  # Decorator: enforces active login session
def display_contracts(unsigned, unpaid):
    """
    Display the list of commercial contracts with optional status filters.

    Filters can be combined (e.g. --unsigned --unpaid).
    """
    try:
        contracts = get_all_contracts(filter_unsigned=unsigned, filter_unpaid=unpaid)
        # Build filter label for the table header
        filter_title = ""
        if unsigned and unpaid:
            filter_title = "(Unsigned & With Balance Due)"
        elif unsigned:
            filter_title = "(Unsigned Only)"
        elif unpaid:
            filter_title = "(With Balance Due)"

        display_contracts_view(contracts, filter_title=filter_title)
    except Exception as e:
        log_exception(e, extra={"action": "display_contracts"})
        display_error(f"Error retrieving contracts: {e}")


@cli.command(name="create-contract")
@click.option("--client-id", prompt="Client ID", type=int, help="Target client database ID")
@click.option("--total-amount", prompt="Total amount (€)", type=float, help="Total contract value")
@click.option("--amount-due", prompt="Balance due (€)", type=float, help="Remaining amount to be paid")
@click.option("--signed/--unsigned", default=False, help="Initial signature status")
@click.option("--commercial-id", type=int, default=None, help="Assigned commercial ID (optional)")
@require_role("GESTION")  # Decorator: restricts access to GESTION department only
def cli_create_contract(client_id, total_amount, amount_due, signed, commercial_id):
    """
    Create a new commercial contract (GESTION department only).

    Step 1: Validate total amount is non-negative.
    Step 2: Validate balance due is non-negative.
    Step 3: Delegate creation to contract_controller.
    Note: Sentry.io logs a signature audit event if contract is created as signed.
    """
    try:
        # Step 1: Validate total amount
        valid_tot, msg_tot = validate_positive_amount(total_amount, "Total amount")
        if not valid_tot:
            display_error(msg_tot)
            return

        # Step 2: Validate balance due
        valid_due, msg_due = validate_positive_amount(amount_due, "Balance due")
        if not valid_due:
            display_error(msg_due)
            return

        # Step 3: Create contract
        user, _ = get_current_user()
        success, message = create_contract(
            client_id, total_amount, amount_due, is_signed=signed, commercial_contact_id=commercial_id, current_user=user
        )
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "create_contract", "client_id": client_id})
        display_error(f"An error occurred: {e}")


@cli.command(name="update-contract")
@click.option("--contract-id", prompt="Contract ID to update", type=int, help="Contract database ID")
@click.option("--total-amount", type=float, default=None, help="Updated total amount (€)")
@click.option("--amount-due", type=float, default=None, help="Updated balance due (€)")
@click.option("--signed", is_flag=True, default=None, help="Mark contract as signed")
@click.option("--commercial-id", type=int, default=None, help="Re-assign commercial representative (GESTION only)")
@require_role("GESTION", "COMMERCIAL")  # Both roles allowed; ownership checked in controller
def cli_update_contract(contract_id, total_amount, amount_due, signed, commercial_id):
    """
    Update an existing contract (GESTION team or responsible COMMERCIAL representative).

    Step 1: Validate amount fields if provided.
    Step 2: Delegate to contract_controller with current user context.
    Note: Sentry.io logs an audit event if the contract signature changes to signed.
    """
    try:
        # Step 1a: Validate total amount if provided
        if total_amount is not None:
            valid_tot, msg_tot = validate_positive_amount(total_amount, "Total amount")
            if not valid_tot:
                display_error(msg_tot)
                return

        # Step 1b: Validate balance due if provided
        if amount_due is not None:
            valid_due, msg_due = validate_positive_amount(amount_due, "Balance due")
            if not valid_due:
                display_error(msg_due)
                return

        # Step 2: Execute update
        user, _ = get_current_user()
        is_signed_val = True if signed else None
        success, message = update_contract(
            contract_id,
            total_amount=total_amount,
            amount_due=amount_due,
            is_signed=is_signed_val,
            commercial_contact_id=commercial_id,
            current_user=user,
        )
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "update_contract", "contract_id": contract_id})
        display_error(f"An error occurred: {e}")


# ==========================================
# SECTION 5: EVENT MANAGEMENT (COMMERCIAL / GESTION / SUPPORT)
# ==========================================

@cli.command(name="display-events")
@click.option("--no-support", is_flag=True, help="Filter events with no assigned support contact")
@click.option("--my-events", is_flag=True, help="Filter events assigned to me (Support team)")
@require_login  # Decorator: enforces active login session
def display_events(no_support, my_events):
    """
    Display the list of events with optional filters.

    --no-support: Useful for GESTION to identify events needing support assignment.
    --my-events: Useful for SUPPORT to see their own assigned events.
    """
    try:
        user, _ = get_current_user()
        events = get_all_events(filter_no_support=no_support, filter_my_events=my_events, current_user=user)

        # Build filter label for display
        filter_title = ""
        if no_support:
            filter_title = "(No Support Assigned)"
        elif my_events:
            filter_title = "(My Assigned Events)"

        display_events_view(events, filter_title=filter_title)
    except Exception as e:
        log_exception(e, extra={"action": "display_events"})
        display_error(f"Error retrieving events: {e}")


@cli.command(name="create-event")
@click.option("--title", prompt="Event title", help="Title of the event")
@click.option("--contract-id", prompt="Associated contract ID", type=int, help="ID of the signed contract")
@click.option("--start", prompt="Start date (YYYY-MM-DD HH:MM)", help="Event start date and time")
@click.option("--end", prompt="End date (YYYY-MM-DD HH:MM)", help="Event end date and time")
@click.option("--location", prompt="Event location", help="Physical or virtual venue")
@click.option("--attendees", default=0, type=int, help="Expected attendee count")
@click.option("--notes", default=None, help="Organizational notes")
@require_role("COMMERCIAL")  # Decorator: restricts access to COMMERCIAL department only
def cli_create_event(title, contract_id, start, end, location, attendees, notes):
    """
    Create an event for a signed contract (COMMERCIAL department only).

    Step 1: Validate start date string format.
    Step 2: Validate end date string format.
    Step 3: Ensure start date is strictly before end date.
    Step 4: Delegate to event_controller.create_event().
    Note: Contract MUST be signed for event creation to succeed (enforced in controller).
    """
    try:
        # Step 1: Parse and validate start date
        valid_start, dt_start, msg_start = validate_date_format(start)
        if not valid_start:
            display_error(msg_start)
            return

        # Step 2: Parse and validate end date
        valid_end, dt_end, msg_end = validate_date_format(end)
        if not valid_end:
            display_error(msg_end)
            return

        # Step 3: Chronological date check
        if dt_start >= dt_end:
            display_error("Start date and time must be strictly before end date and time.")
            return

        # Step 4: Delegate to controller
        user, _ = get_current_user()
        success, message = create_event(
            title, contract_id, dt_start, dt_end, location, attendees=attendees, notes=notes, current_user=user
        )
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "create_event", "title": title, "contract_id": contract_id})
        display_error(f"An error occurred: {e}")


@cli.command(name="update-event")
@click.option("--event-id", prompt="Event ID to update", type=int, help="Event database ID")
@click.option("--title", default=None, help="Updated title")
@click.option("--start", default=None, help="Updated start date (YYYY-MM-DD HH:MM)")
@click.option("--end", default=None, help="Updated end date (YYYY-MM-DD HH:MM)")
@click.option("--location", default=None, help="Updated location")
@click.option("--attendees", type=int, default=None, help="Updated attendee count")
@click.option("--notes", default=None, help="Updated notes")
@click.option("--support-id", type=int, default=None, help="Assign a support contact (GESTION only)")
@require_role("GESTION", "SUPPORT")  # Both roles allowed; ownership checked in controller
def cli_update_event(event_id, title, start, end, location, attendees, notes, support_id):
    """
    Update an event (assigned SUPPORT or GESTION team to assign support contact).

    Step 1: Parse and validate start/end date strings if provided.
    Step 2: Delegate to event_controller.update_event() with current user context.
    Note: Only GESTION can assign/reassign the support contact field.
    """
    try:
        dt_start = None
        dt_end = None

        # Step 1a: Parse and validate start date if provided
        if start:
            valid_start, dt_start, msg_start = validate_date_format(start)
            if not valid_start:
                display_error(msg_start)
                return

        # Step 1b: Parse and validate end date if provided
        if end:
            valid_end, dt_end, msg_end = validate_date_format(end)
            if not valid_end:
                display_error(msg_end)
                return

        # Step 2: Execute update
        user, _ = get_current_user()
        success, message = update_event(
            event_id,
            title=title,
            event_date_start=dt_start,
            event_date_end=dt_end,
            location=location,
            attendees=attendees,
            notes=notes,
            support_contact_id=support_id,
            current_user=user,
        )
        if success:
            display_success(message)
        else:
            display_error(message)
    except Exception as e:
        log_exception(e, extra={"action": "update_event", "event_id": event_id})
        display_error(f"An error occurred: {e}")


# Entry point: run the CLI group
if __name__ == "__main__":
    cli()

