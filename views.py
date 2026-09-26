from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from models import User, Client, Contract, Event

console = Console()


def display_success(message: str):
    """Displays a rich success message panel."""
    console.print(Panel(Text(f"✅ {message}", style="bold green"), border_style="green", title="Succès"))


def display_error(message: str):
    """Displays a rich error message panel."""
    console.print(Panel(Text(f"❌ {message}", style="bold red"), border_style="red", title="Erreur"))


def display_warning(message: str):
    """Displays a rich warning message panel."""
    console.print(Panel(Text(f"⚠️ {message}", style="bold yellow"), border_style="yellow", title="Attention"))


def display_whoami_view(user: User):
    """Displays user profile details in a rich styled Panel."""
    if not user:
        return

    role_name = user.role.name if user.role else "SANS RÔLE"
    role_color = "cyan" if role_name == "COMMERCIAL" else "magenta" if role_name == "SUPPORT" else "gold1"

    content = Text()
    content.append("🔑 Session Active (Jeton JWT Valide)\n\n", style="bold green")
    content.append(f"Employé N° : ", style="bold white")
    content.append(f"{user.employee_number}\n", style="cyan")
    content.append(f"Nom Complet: ", style="bold white")
    content.append(f"{user.full_name}\n", style="white")
    content.append(f"Email      : ", style="bold white")
    content.append(f"{user.email}\n", style="white")
    content.append(f"Département: ", style="bold white")
    content.append(f"{role_name}", style=f"bold {role_color}")
    if user.role and user.role.description:
        content.append(f" ({user.role.description})", style="italic dim")

    console.print(Panel(content, border_style=role_color, title="Profil Collaborateur", expand=False))


def display_users_view(users: list[User]):
    """Formats and prints users/collaborators list in a Rich Table."""
    if not users:
        display_warning("Aucun collaborateur trouvé.")
        return

    table = Table(title="👥 LISTE DES COLLABORATEURS EPIC EVENTS", header_style="bold cyan", border_style="blue")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("N° Employé", style="bold cyan")
    table.add_column("Nom Complet", style="bold white")
    table.add_column("Email Pro", style="white")
    table.add_column("Département / Rôle", justify="center")

    for u in users:
        r_name = u.role.name if u.role else "Sans rôle"
        r_style = "cyan" if r_name == "COMMERCIAL" else "magenta" if r_name == "SUPPORT" else "gold1"
        table.add_row(
            str(u.id),
            u.employee_number,
            u.full_name,
            u.email,
            Text(r_name, style=f"bold {r_style}"),
        )

    console.print(table)
    console.print(f"[dim cyan]Total: {len(users)} collaborateur(s)[/dim cyan]\n")


def display_clients_view(clients: list[Client]):
    """Formats and prints clients list in a Rich Table."""
    if not clients:
        display_warning("Aucun client trouvé.")
        return

    table = Table(title="🏢 LISTE DES CLIENTS EPIC EVENTS", header_style="bold cyan", border_style="cyan")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Nom Complet", style="bold white")
    table.add_column("Email", style="blue")
    table.add_column("Téléphone", style="white")
    table.add_column("Entreprise", style="bold yellow")
    table.add_column("Contact Commercial", style="green")

    for c in clients:
        comm_name = c.commercial_contact.full_name if c.commercial_contact else "Non attribué"
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
    """Formats and prints contracts list in a Rich Table."""
    if not contracts:
        display_warning(f"Aucun contrat trouvé {filter_title}.")
        return

    table_title = f"📜 LISTE DES CONTRATS EPIC EVENTS {filter_title}".strip()
    table = Table(title=table_title, header_style="bold green", border_style="green")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Client", style="bold white")
    table.add_column("Commercial", style="cyan")
    table.add_column("Montant Total", justify="right", style="bold white")
    table.add_column("Reste à Payer", justify="right")
    table.add_column("Statut Signature", justify="center")
    table.add_column("Date Création", justify="center", style="dim")

    for k in contracts:
        client_name = k.client.full_name if k.client else "Inconnu"
        comm_name = k.commercial_contact.full_name if k.commercial_contact else "Inconnu"
        
        status_text = Text("✅ Signé", style="bold green") if k.is_signed else Text("❌ Non signé", style="bold red")
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
    console.print(f"[dim green]Total: {len(contracts)} contrat(s)[/dim green]\n")


def display_events_view(events: list[Event], filter_title: str = ""):
    """Formats and prints events list in a Rich Table."""
    if not events:
        display_warning(f"Aucun événement trouvé {filter_title}.")
        return

    table_title = f"🎉 LISTE DES ÉVÉNEMENTS EPIC EVENTS {filter_title}".strip()
    table = Table(title=table_title, header_style="bold magenta", border_style="magenta")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Titre Événement", style="bold white")
    table.add_column("Contrat N°", justify="center", style="cyan")
    table.add_column("Client", style="white")
    table.add_column("Date Début", justify="center", style="dim")
    table.add_column("Date Fin", justify="center", style="dim")
    table.add_column("Support Responsable", justify="center")
    table.add_column("Lieu", style="yellow")
    table.add_column("Invités", justify="right", style="bold white")

    for e in events:
        client_name = e.client.full_name if e.client else "Inconnu"
        support_text = (
            Text(e.support_contact.full_name, style="bold magenta")
            if e.support_contact
            else Text("⚠️ Non attribué", style="bold yellow")
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
    console.print(f"[dim magenta]Total: {len(events)} événement(s)[/dim magenta]\n")
