import click
from models import Client, Contract, Event


def display_clients_view(clients: list[Client]):
    """Formats and prints clients list in terminal."""
    if not clients:
        click.echo(click.style("ℹ️ Aucun client trouvé.", fg="yellow"))
        return

    click.echo(click.style("\n=== LISTE DES CLIENTS ===", fg="cyan", bold=True))
    header = f"{'ID':<4} | {'Nom Complet':<20} | {'Email':<25} | {'Téléphone':<16} | {'Entreprise':<20} | {'Contact Commercial':<20}"
    click.echo(click.style(header, bold=True))
    click.echo("-" * len(header))

    for c in clients:
        comm_name = c.commercial_contact.full_name if c.commercial_contact else "Non attribué"
        click.echo(
            f"{c.id:<4} | {c.full_name:<20} | {c.email:<25} | {c.phone or '-':<16} | {c.company_name or '-':<20} | {comm_name:<20}"
        )
    click.echo(click.style(f"Total: {len(clients)} client(s)\n", fg="cyan"))


def display_contracts_view(contracts: list[Contract], filter_title: str = ""):
    """Formats and prints contracts list in terminal."""
    if not contracts:
        click.echo(click.style(f"ℹ️ Aucun contrat trouvé {filter_title}.", fg="yellow"))
        return

    title = f"\n=== LISTE DES CONTRATS {filter_title} ==="
    click.echo(click.style(title, fg="cyan", bold=True))
    header = f"{'ID':<4} | {'Client':<20} | {'Commercial':<20} | {'Montant Total':<14} | {'Reste à Payer':<14} | {'Statut':<12} | {'Date Création':<12}"
    click.echo(click.style(header, bold=True))
    click.echo("-" * len(header))

    for k in contracts:
        client_name = k.client.full_name if k.client else "Inconnu"
        comm_name = k.commercial_contact.full_name if k.commercial_contact else "Inconnu"
        status = "✅ Signé" if k.is_signed else "❌ Non signé"
        date_str = k.creation_date.strftime("%Y-%m-%d") if k.creation_date else "-"
        click.echo(
            f"{k.id:<4} | {client_name:<20} | {comm_name:<20} | {k.total_amount:<14.2f}€ | {k.amount_due:<14.2f}€ | {status:<12} | {date_str:<12}"
        )
    click.echo(click.style(f"Total: {len(contracts)} contrat(s)\n", fg="cyan"))


def display_events_view(events: list[Event], filter_title: str = ""):
    """Formats and prints events list in terminal."""
    if not events:
        click.echo(click.style(f"ℹ️ Aucun événement trouvé {filter_title}.", fg="yellow"))
        return

    title = f"\n=== LISTE DES ÉVÉNEMENTS {filter_title} ==="
    click.echo(click.style(title, fg="cyan", bold=True))
    header = f"{'ID':<4} | {'Titre Événement':<25} | {'Contrat ID':<10} | {'Client':<18} | {'Début':<16} | {'Fin':<16} | {'Support Responsable':<20} | {'Lieu':<20}"
    click.echo(click.style(header, bold=True))
    click.echo("-" * len(header))

    for e in events:
        client_name = e.client.full_name if e.client else "Inconnu"
        support_name = e.support_contact.full_name if e.support_contact else "⚠️ Non attribué"
        start_str = e.event_date_start.strftime("%Y-%m-%d %H:%M") if e.event_date_start else "-"
        end_str = e.event_date_end.strftime("%Y-%m-%d %H:%M") if e.event_date_end else "-"
        click.echo(
            f"{e.id:<4} | {e.title:<25} | {e.contract_id:<10} | {client_name:<18} | {start_str:<16} | {end_str:<16} | {support_name:<20} | {e.location:<20}"
        )
    click.echo(click.style(f"Total: {len(events)} événement(s)\n", fg="cyan"))
