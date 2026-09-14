import click
from controllers.auth_controller import login_user, logout_user
from permissions import get_current_user


@click.group()
def cli():
    """Epic Events CRM - Application en Ligne de Commande (CLI)"""
    pass


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


if __name__ == "__main__":
    cli()
