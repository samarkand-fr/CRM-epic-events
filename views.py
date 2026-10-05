"""
Rich CLI Terminal Presentation View Module (views.py).

This module manages terminal output formatting using the Rich library:
1. Success, Error, and Warning message panels.
2. User profile session viewer (whoami).
3. Formatted tables for Users, Clients, Contracts, and Events.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from models import User, Client, Contract, Event

console = Console()


def display_success(message: str):
    """
    Displays a styled success message panel.

    Args:
        message (str): Success text to display.
    """
    console.print(Panel(Text(f"✅ {message}", style="bold green"), border_style="green", title="Success"))


def display_error(message: str):
    """
    Displays a styled error message panel.

    Args:
        message (str): Error message to display.
    """
    console.print(Panel(Text(f"❌ {message}", style="bold red"), border_style="red", title="Error"))


def display_warning(message: str):
    """
    Displays a styled warning message panel.

    Args:
        message (str): Warning text to display.
    """
    console.print(Panel(Text(f"⚠️ {message}", style="bold yellow"), border_style="yellow", title="Warning"))


def display_whoami_view(user: User):
    """
    Displays active authenticated user profile details in a Rich Panel.

    Args:
        user (User): Currently logged-in User instance.
    """
    if not user:
        return

    role_name = user.role.name if user.role else "NO ROLE"
    role_color = "cyan" if role_name == "COMMERCIAL" else "magenta" if role_name == "SUPPORT" else "gold1"

    content = Text()
    content.append("🔑 Active Session (Valid JWT Token)\n\n", style="bold green")
    content.append("Employee ID: ", style="bold white")
    content.append(f"{user.employee_number}\n", style="cyan")
    content.append("Full Name  : ", style="bold white")
    content.append(f"{user.full_name}\n", style="white")
    content.append("Email      : ", style="bold white")
    content.append(f"{user.email}\n", style="white")
    content.append("Department : ", style="bold white")
    content.append(f"{role_name}", style=f"bold {role_color}")
    if user.role and user.role.description:
        content.append(f" ({user.role.description})", style="italic dim")

    console.print(Panel(content, border_style=role_color, title="Collaborator Profile", expand=False))


def display_users_view(users: list[User]):
    """
    Formats and prints the list of employee users in a Rich Table.

    Args:
        users (list[User]): List of user records.
    """
    if not users:
        display_warning("No collaborators found.")
        return

    table = Table(title="👥 EPIC EVENTS COLLABORATOR LIST", header_style="bold cyan", border_style="blue")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Employee N°", style="bold cyan")
    table.add_column("Full Name", style="bold white")
    table.add_column("Pro Email", style="white")
    table.add_column("Department / Role", justify="center")

    for u in users:
        r_name = u.role.name if u.role else "No role"
        r_style = "cyan" if r_name == "COMMERCIAL" else "magenta" if r_name == "SUPPORT" else "gold1"
        table.add_row(
            str(u.id),
            u.employee_number,
            u.full_name,
            u.email,
            Text(r_name, style=f"bold {r_style}"),
        )

    console.print(table)
    console.print(f"[dim cyan]Total: {len(users)} collaborator(s)[/dim cyan]\n")


def display_clients_view(clients: list[Client]):
    """
    Formats and prints the list of clients in a Rich Table.

    Args:
        clients (list[Client]): List of client records.
    """
    if not clients:
        display_warning("No clients found.")
        return

    table = Table(title="🏢 EPIC EVENTS CLIENT LIST", header_style="bold cyan", border_style="cyan")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Full Name", style="bold white")
    table.add_column("Email", style="blue")
    table.add_column("Phone", style="white")
    table.add_column("Company", style="bold yellow")
    table.add_column("Commercial Contact", style="green")

    for c in clients:
        comm_name = c.commercial_contact.full_name if c.commercial_contact else "Unassigned"
        table.add_row(
            str(c.id),
            c.full_name,
            c.email,
            c.phone or "-",
            c.company_name or "-",
            comm_name,
        )

    console.print(table)
    console.print(f"[dim cyan]Total: {len(clients)} client(s)[/dim cyan]\n")


def display_contracts_view(contracts: list[Contract], filter_title: str = ""):
    """
    Formats and prints the list of contracts in a Rich Table.

    Args:
        contracts (list[Contract]): List of contract records.
        filter_title (str): Subtitle indicating applied filters.
    """
    if not contracts:
        display_warning(f"No contracts found {filter_title}.")
        return

    table_title = f"📜 EPIC EVENTS CONTRACT LIST {filter_title}".strip()
    table = Table(title=table_title, header_style="bold green", border_style="green")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Client", style="bold white")
    table.add_column("Commercial Contact", style="cyan")
    table.add_column("Total Amount", justify="right", style="bold white")
    table.add_column("Balance Due", justify="right")
    table.add_column("Signature Status", justify="center")
    table.add_column("Creation Date", justify="center", style="dim")

    for k in contracts:
        client_name = k.client.full_name if k.client else "Unknown"
        comm_name = k.commercial_contact.full_name if k.commercial_contact else "Unknown"
        
        status_text = Text("✅ Signed", style="bold green") if k.is_signed else Text("❌ Unsigned", style="bold red")
        due_style = "bold red" if k.amount_due > 0 else "bold green"
        date_str = k.creation_date.strftime("%Y-%m-%d") if k.creation_date else "-"

        table.add_row(
            str(k.id),
            client_name,
            comm_name,
            f"{k.total_amount:,.2f} €",
            Text(f"{k.amount_due:,.2f} €", style=due_style),
            status_text,
            date_str,
        )

    console.print(table)
    console.print(f"[dim green]Total: {len(contracts)} contract(s)[/dim green]\n")


def display_events_view(events: list[Event], filter_title: str = ""):
    """
    Formats and prints the list of events in a Rich Table.

    Args:
        events (list[Event]): List of event records.
        filter_title (str): Subtitle indicating applied filters.
    """
    if not events:
        display_warning(f"No events found {filter_title}.")
        return

    table_title = f"🎉 EPIC EVENTS EVENT LIST {filter_title}".strip()
    table = Table(title=table_title, header_style="bold magenta", border_style="magenta")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Event Title", style="bold white")
    table.add_column("Contract N°", justify="center", style="cyan")
    table.add_column("Client", style="white")
    table.add_column("Start Date", justify="center", style="dim")
    table.add_column("End Date", justify="center", style="dim")
    table.add_column("Assigned Support", justify="center")
    table.add_column("Venue Location", style="yellow")
    table.add_column("Attendees", justify="right", style="bold white")

    for e in events:
        client_name = e.client.full_name if e.client else "Unknown"
        support_text = (
            Text(e.support_contact.full_name, style="bold magenta")
            if e.support_contact
            else Text("⚠️ Unassigned", style="bold yellow")
        )
        start_str = e.event_date_start.strftime("%Y-%m-%d %H:%M") if e.event_date_start else "-"
        end_str = e.event_date_end.strftime("%Y-%m-%d %H:%M") if e.event_date_end else "-"

        table.add_row(
            str(e.id),
            e.title,
            str(e.contract_id),
            client_name,
            start_str,
            end_str,
            support_text,
            e.location,
            str(e.attendees),
        )

    console.print(table)
    console.print(f"[dim magenta]Total: {len(events)} event(s)[/dim magenta]\n")

