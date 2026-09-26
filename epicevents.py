from datetime import datetime
import click

from controllers.auth_controller import login_user, logout_user
from controllers.user_controller import get_all_users, create_user, update_user
from controllers.client_controller import get_all_clients, create_client, update_client
from controllers.contract_controller import get_all_contracts, create_contract, update_contract
from controllers.event_controller import get_all_events, create_event, update_event
from permissions import get_current_user, require_login, require_role
from views import (
    display_users_view,
    display_clients_view,
    display_contracts_view,
    display_events_view,
)


@click.group()
def cli():
    """Epic Events CRM - Application en Ligne de Commande (CLI)"""
    pass


# ==========================================
# 1. COMMANDES D'AUTHENTIFICATION
# ==========================================

@cli.command()
@click.option("--identifier", prompt="Email ou numéro d'employé", help="Adresse email ou numéro d'employé (ex: EMP001)")
@click.option("--password", prompt="Mot de passe", hide_input=True, help="Mot de passe du collaborateur")
def login(identifier, password):
    """Se connecter à la plateforme CRM Epic Events et obtenir un jeton JWT."""
    success, message = login_user(identifier, password)
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


@cli.command()
def logout():
    """Se déconnecter de la plateforme CRM et supprimer le jeton local."""
    logout_user()
    click.echo(click.style("👋 Déconnexion réussie. Jeton de session supprimé.", fg="blue"))


@cli.command()
def whoami():
    """Afficher le collaborateur actuellement connecté et vérifier le jeton."""
    user, err_code = get_current_user()
    if err_code == "TOKEN_EXPIRED":
        click.echo(click.style("⏰ Votre session a expiré. Veuillez vous re-connecter avec 'python epicevents.py login'.", fg="yellow"))
    elif user:
        click.echo(click.style("🔑 Session active (Jeton JWT valide) :", fg="green"))
        click.echo(f"  Employé N° : {user.employee_number}")
        click.echo(f"  Nom        : {user.full_name}")
        click.echo(f"  Email      : {user.email}")
        click.echo(f"  Département: {user.role.name} ({user.role.description})")
    else:
        click.echo(click.style("ℹ️ Aucun collaborateur actuellement connecté.", fg="yellow"))


# ==========================================
# 2. GESTION DES COLLABORATEURS (GESTION)
# ==========================================

@cli.command(name="display-users")
@require_login
def display_users():
    """Afficher la liste de tous les collaborateurs."""
    users = get_all_users()
    display_users_view(users)


@cli.command(name="create-user")
@click.option("--emp-num", prompt="Numéro d'employé (ex: EMP004)", help="Numéro d'employé unique")
@click.option("--full-name", prompt="Nom complet du collaborateur", help="Nom complet")
@click.option("--email", prompt="Email professionnel", help="Adresse email")
@click.option("--password", prompt="Mot de passe initial", hide_input=True, help="Mot de passe")
@click.option("--role", prompt="Rôle (COMMERCIAL, SUPPORT, GESTION)", help="Département / Rôle")
@require_role("GESTION")
def cli_create_user(emp_num, full_name, email, password, role):
    """Créer un nouveau collaborateur (Équipe Gestion)."""
    user, _ = get_current_user()
    success, message = create_user(emp_num, full_name, email, password, role, current_user=user)
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


@cli.command(name="update-user")
@click.option("--user-id", prompt="ID du collaborateur à modifier", type=int, help="ID du collaborateur")
@click.option("--full-name", default=None, help="Nouveau nom complet")
@click.option("--email", default=None, help="Nouvelle adresse email")
@click.option("--password", default=None, help="Nouveau mot de passe")
@click.option("--role", default=None, help="Nouveau rôle (COMMERCIAL, SUPPORT, GESTION)")
@require_role("GESTION")
def cli_update_user(user_id, full_name, email, password, role):
    """Modifier un collaborateur existant (Équipe Gestion)."""
    user, _ = get_current_user()
    success, message = update_user(user_id, full_name, email, password, role, current_user=user)
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


# ==========================================
# 3. GESTION DES CLIENTS (COMMERCIAL)
# ==========================================

@cli.command(name="display-clients")
@require_login
def display_clients():
    """Afficher la liste de tous les clients."""
    clients = get_all_clients()
    display_clients_view(clients)


@cli.command(name="create-client")
@click.option("--full-name", prompt="Nom complet du client", help="Nom complet du client")
@click.option("--email", prompt="Email du client", help="Adresse email")
@click.option("--phone", default=None, help="Téléphone de contact")
@click.option("--company", default=None, help="Nom de l'entreprise")
@require_role("COMMERCIAL")
def cli_create_client(full_name, email, phone, company):
    """Créer un nouveau client (Équipe Commerciale)."""
    user, _ = get_current_user()
    success, message = create_client(full_name, email, phone, company, current_user=user)
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


@cli.command(name="update-client")
@click.option("--client-id", prompt="ID du client à modifier", type=int, help="ID du client")
@click.option("--full-name", default=None, help="Nouveau nom complet")
@click.option("--email", default=None, help="Nouvel email")
@click.option("--phone", default=None, help="Nouveau téléphone")
@click.option("--company", default=None, help="Nouvelle entreprise")
@require_role("COMMERCIAL")
def cli_update_client(client_id, full_name, email, phone, company):
    """Modifier un client sous sa responsabilité (Équipe Commerciale)."""
    user, _ = get_current_user()
    success, message = update_client(client_id, full_name, email, phone, company, current_user=user)
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


# ==========================================
# 4. GESTION DES CONTRATS (GESTION & COMMERCIAL)
# ==========================================

@cli.command(name="display-contracts")
@click.option("--unsigned", is_flag=True, help="Filtrer uniquement les contrats non signés")
@click.option("--unpaid", is_flag=True, help="Filtrer uniquement les contrats avec un reste à payer")
@require_login
def display_contracts(unsigned, unpaid):
    """Afficher la liste des contrats (avec filtres optionnels)."""
    contracts = get_all_contracts(filter_unsigned=unsigned, filter_unpaid=unpaid)
    filter_title = ""
    if unsigned and unpaid:
        filter_title = "(Non signés & Non entièrement payés)"
    elif unsigned:
        filter_title = "(Non signés)"
    elif unpaid:
        filter_title = "(Non entièrement payés)"

    display_contracts_view(contracts, filter_title=filter_title)


@cli.command(name="create-contract")
@click.option("--client-id", prompt="ID du client", type=int, help="ID du client concerné")
@click.option("--total-amount", prompt="Montant total (€)", type=float, help="Montant total du contrat")
@click.option("--amount-due", prompt="Reste à payer (€)", type=float, help="Reste à payer")
@click.option("--signed/--unsigned", default=False, help="Statut de signature du contrat")
@click.option("--commercial-id", type=int, default=None, help="ID du commercial rattaché (optionnel)")
@require_role("GESTION")
def cli_create_contract(client_id, total_amount, amount_due, signed, commercial_id):
    """Créer un nouveau contrat (Équipe Gestion)."""
    user, _ = get_current_user()
    success, message = create_contract(
        client_id, total_amount, amount_due, is_signed=signed, commercial_contact_id=commercial_id, current_user=user
    )
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


@cli.command(name="update-contract")
@click.option("--contract-id", prompt="ID du contrat à modifier", type=int, help="ID du contrat")
@click.option("--total-amount", type=float, default=None, help="Nouveau montant total (€)")
@click.option("--amount-due", type=float, default=None, help="Nouveau reste à payer (€)")
@click.option("--signed", is_flag=True, default=None, help="Marquer comme signé")
@click.option("--commercial-id", type=int, default=None, help="Changer le commercial rattaché (Gestion)")
@require_role("GESTION", "COMMERCIAL")
def cli_update_contract(contract_id, total_amount, amount_due, signed, commercial_id):
    """Modifier un contrat (Équipe Gestion ou Commercial responsable)."""
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
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


# ==========================================
# 5. GESTION DES ÉVÉNEMENTS (COMMERCIAL, GESTION, SUPPORT)
# ==========================================

@cli.command(name="display-events")
@click.option("--no-support", is_flag=True, help="Filtrer les événements sans support attribué")
@click.option("--my-events", is_flag=True, help="Filtrer les événements à ma charge")
@require_login
def display_events(no_support, my_events):
    """Afficher la liste des événements (avec filtres optionnels)."""
    user, _ = get_current_user()
    events = get_all_events(filter_no_support=no_support, filter_my_events=my_events, current_user=user)

    filter_title = ""
    if no_support:
        filter_title = "(Sans support associé)"
    elif my_events:
        filter_title = "(Attribués à ma charge)"

    display_events_view(events, filter_title=filter_title)


@cli.command(name="create-event")
@click.option("--title", prompt="Titre de l'événement", help="Titre de l'événement")
@click.option("--contract-id", prompt="ID du contrat associé", type=int, help="ID du contrat signé")
@click.option("--start", prompt="Date début (YYYY-MM-DD HH:MM)", help="Date et heure de début")
@click.option("--end", prompt="Date fin (YYYY-MM-DD HH:MM)", help="Date et heure de fin")
@click.option("--location", prompt="Lieu de l'événement", help="Lieu de l'événement")
@click.option("--attendees", default=0, type=int, help="Nombre de participants")
@click.option("--notes", default=None, help="Notes d'organisation")
@require_role("COMMERCIAL")
def cli_create_event(title, contract_id, start, end, location, attendees, notes):
    """Créer un événement pour un contrat signé (Équipe Commerciale)."""
    user, _ = get_current_user()
    try:
        dt_start = datetime.strptime(start, "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(end, "%Y-%m-%d %H:%M")
    except ValueError:
        click.echo(click.style("❌ Format de date invalide. Utilisez le format 'YYYY-MM-DD HH:MM'.", fg="red"))
        return

    success, message = create_event(
        title, contract_id, dt_start, dt_end, location, attendees=attendees, notes=notes, current_user=user
    )
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


@cli.command(name="update-event")
@click.option("--event-id", prompt="ID de l'événement à modifier", type=int, help="ID de l'événement")
@click.option("--title", default=None, help="Nouveau titre")
@click.option("--start", default=None, help="Nouvelle date début (YYYY-MM-DD HH:MM)")
@click.option("--end", default=None, help="Nouvelle date fin (YYYY-MM-DD HH:MM)")
@click.option("--location", default=None, help="Nouveau lieu")
@click.option("--attendees", type=int, default=None, help="Nouveau nombre de participants")
@click.option("--notes", default=None, help="Nouvelles notes")
@click.option("--support-id", type=int, default=None, help="Attribuer un contact Support (Gestion)")
@require_role("GESTION", "SUPPORT")
def cli_update_event(event_id, title, start, end, location, attendees, notes, support_id):
    """Modifier un événement (Support responsable ou Gestion pour désigner le support)."""
    user, _ = get_current_user()
    dt_start = None
    dt_end = None
    if start:
        try:
            dt_start = datetime.strptime(start, "%Y-%m-%d %H:%M")
        except ValueError:
            click.echo(click.style("❌ Format de date début invalide (YYYY-MM-DD HH:MM).", fg="red"))
            return
    if end:
        try:
            dt_end = datetime.strptime(end, "%Y-%m-%d %H:%M")
        except ValueError:
            click.echo(click.style("❌ Format de date fin invalide (YYYY-MM-DD HH:MM).", fg="red"))
            return

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
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


if __name__ == "__main__":
    cli()
