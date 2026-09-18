import click
from controllers.auth_controller import login_user, logout_user
from controllers.client_controller import get_all_clients
from controllers.contract_controller import get_all_contracts
from controllers.event_controller import get_all_events
from permissions import get_current_user, require_login
from views import display_clients_view, display_contracts_view, display_events_view


@click.group()
def cli():
    """Epic Events CRM - Application en Ligne de Commande (CLI)"""
    pass


# --- COMMANDES D'AUTHENTIFICATION ---

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


# --- COMMANDES DE LECTURE DES DONNÉES MÉTIERS ---

@cli.command(name="display-clients")
@require_login
def display_clients():
    """Afficher la liste de tous les clients."""
    clients = get_all_clients()
    display_clients_view(clients)


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


@cli.command(name="display-events")
@click.option("--no-support", is_flag=True, help="Filtrer les événements qui n'ont pas encore de support associé")
@click.option("--my-events", is_flag=True, help="Filtrer uniquement les événements qui me sont attribués")
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


if __name__ == "__main__":
    cli()
