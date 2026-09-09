import click
from controllers.auth_controller import login_user, logout_user
from permissions import get_current_user


@click.group()
def cli():
    """Epic Events CRM - Application en Ligne de Commande (CLI)"""
    pass


@cli.command()
@click.option("--identifier", prompt="Email ou numéro d'employé", help="Adresse email ou numéro d'employé")
@click.option("--password", prompt="Mot de passe", hide_input=True, help="Mot de passe")
def login(identifier, password):
    """Se connecter à la plateforme CRM Epic Events."""
    success, message = login_user(identifier, password)
    if success:
        click.echo(click.style(f"✅ {message}", fg="green"))
    else:
        click.echo(click.style(f"❌ {message}", fg="red"))


@cli.command()
def logout():
    """Se déconnecter de la plateforme CRM."""
    logout_user()
    click.echo(click.style("👋 Déconnexion réussie.", fg="blue"))


@cli.command()
def whoami():
    """Afficher le collaborateur actuellement connecté."""
    user = get_current_user()
    if user:
        click.echo(click.style("🔑 Session active :", fg="green"))
        click.echo(f"  Employé N° : {user.employee_number}")
        click.echo(f"  Nom        : {user.full_name}")
        click.echo(f"  Email      : {user.email}")
        click.echo(f"  Département: {user.role.name} ({user.role.description})")
    else:
        click.echo(click.style("ℹ️ Aucun collaborateur actuellement connecté.", fg="yellow"))


if __name__ == "__main__":
    cli()
