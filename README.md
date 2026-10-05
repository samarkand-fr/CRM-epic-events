# 🏢 Epic Events CRM - Application en Ligne de Commande (CLI)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0+-green.svg)](https://www.sqlalchemy.org/)
[![Security Argon2](https://img.shields.io/badge/Security-Argon2-red.svg)](https://passlib.readthedocs.io/)
[![Sentry.io](https://img.shields.io/badge/Logging-Sentry.io-purple.svg)](https://sentry.io/)

**Epic Events CRM** est une application sécurisée en ligne de commande (CLI) développée en Python pour la gestion de la relation client, des contrats et de l'organisation d'événements.

L'application découpe les opérations entre les trois départements de l'entreprise : **Commercial**, **Support** et **Gestion**, en appliquant strictement le **principe du moindre privilège (RBAC)**.

---

## 📐 Architecture & Modèle de Données (ERD)

L'application repose sur un schéma PostgreSQL normalisé avec 5 entités :

```mermaid
erdiagram
    ROLE {
        int id PK
        string name UK "COMMERCIAL | SUPPORT | GESTION"
        string description
    }

    USER {
        int id PK
        string employee_number UK "ex: EMP001"
        string full_name
        string email UK
        string password_hash "Argon2"
        int role_id FK "References ROLE(id)"
        datetime created_at
    }

    CLIENT {
        int id PK
        string full_name
        string email UK
        string phone
        string company_name
        datetime creation_date
        datetime last_update
        int commercial_contact_id FK "References USER(id)"
    }

    CONTRACT {
        int id PK
        int client_id FK "References CLIENT(id)"
        int commercial_contact_id FK "References USER(id)"
        float total_amount
        float amount_due
        datetime creation_date
        boolean is_signed
    }

    EVENT {
        int id PK
        string title
        int contract_id FK "References CONTRACT(id) (1-to-N)"
        int client_id FK "References CLIENT(id)"
        datetime event_date_start
        datetime event_date_end
        int support_contact_id FK "References USER(id) NULLABLE"
        string location
        int attendees
        text notes
    }

    ROLE ||--o{ USER : "possède des utilisateurs"
    USER ||--o{ CLIENT : "est commercial de"
    USER ||--o{ CONTRACT : "gère contrat"
    USER ||--o{ EVENT : "supporte événement"
    CLIENT ||--o{ CONTRACT : "possède"
    CLIENT ||--o{ EVENT : "organise"
    CONTRACT ||--o{ EVENT : "donne lieu à (1-à-N)"
```

---

## 🛠️ Stack Technique

- **Langage** : Python 3.9+
- **SGBD** : PostgreSQL 16
- **ORM** : SQLAlchemy 2.0+
- **Interface CLI** : Click 8.x + Rich (tableaux et panneaux colorés)
- **Authentification & Sécurité** : PyJWT (Tokens de session persistants) + Argon2 (`passlib[argon2]`)
- **Journalisation & Monitoring** : Sentry.io SDK
- **Tests & Validation** : Pytest

---

## ⚙️ Procédure d'Installation & Déploiement

### 1. Prérequis

- Python 3.9 ou supérieur
- PostgreSQL (démarré localement)
- Git

### 2. Cloner le Dépôt

```bash
git clone https://github.com/samarkand-fr/CRM-epic-events
cd epic_events
```

### 3. Créer et Activer l'Environnement Virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 5. Configurer la Base de Données PostgreSQL

Connectez-vous à PostgreSQL et exécutez la création de l'utilisateur et de la base :

```sql

CREATE ROLE epic_crm_user WITH LOGIN PASSWORD 'StrongPassword123!' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE epic_crm_db OWNER epic_crm_user;
GRANT CONNECT ON DATABASE epic_crm_db TO epic_crm_user;
GRANT ALL ON SCHEMA public TO epic_crm_user;
```

### 6. Configurer les Variables d'Environnement

Copiez le modèle exemple et renseignez vos informations réelles dans `.env` :

```bash
cp .env.example .env
```

Éditez le fichier `.env` :

```env

DATABASE_URL=postgresql+psycopg2://epic_crm_user:StrongPassword123!@localhost:5432/epic_crm_db
SECRET_KEY=votre_cle_secrete_jwt_longue_et_aleatoire
SENTRY_DSN=https://votre_dsn_sentry@sentry.io/project
```

### 7. Initialiser la Base & Insérer les Données de Démonstration

Exécutez le script d'initialisation pour générer le schéma et insérer les comptes de démo :

```bash
python seed_db.py
```

*(Ou exécutez le fichier SQL `psql -U epic_crm_user -d epic_crm_db -f schema.sql`)*.

---

## 🔑 Comptes de Démonstration Générés

| Numéro Employé | Nom Complet | Email | Département / Rôle | Mot de passe |
| :--- | :--- | :--- | :--- | :--- |
| `EMP001` | Bill Boquet | `bill.boquet@epicevents.io` | `COMMERCIAL` | `Password123!` |
| `EMP002` | Kate Hastroff | `kate.hastroff@epicevents.io` | `SUPPORT` | `Password123!` |
| `EMP003` | Admin Gestion | `gestion@epicevents.io` | `GESTION` | `Password123!` |

---

## 💻 Guide d'Utilisation des Commandes CLI (`epicevents.py`)

### 1. Authentification & Session

```bash
# Se connecter (par email ou par N° d'employé)
python epicevents.py login --identifier EMP001 --password Password123!

# Consulter le profil et la session active
python epicevents.py whoami

# Se déconnecter
python epicevents.py logout
```

### 2. Lecture des Données (Accessible à tous les collaborateurs authentifiés)

```bash
# Liste de tous les collaborateurs
python epicevents.py display-users

# Liste de tous les clients
python epicevents.py display-clients

# Liste des contrats (avec filtres optionnels)
python epicevents.py display-contracts
python epicevents.py display-contracts --unsigned
python epicevents.py display-contracts --unpaid

# Liste des événements (avec filtres optionnels)
python epicevents.py display-events
python epicevents.py display-events --no-support
python epicevents.py display-events --my-events
```

### 3. Opérations Équipe Gestion (`GESTION`)

```bash
# Créer un collaborateur
python epicevents.py create-user --emp-num EMP004 --full-name "Marc Dupont" --email marc@epicevents.io --password Pass123! --role SUPPORT

# Modifier un collaborateur
python epicevents.py update-user --user-id 4 --role GESTION

# Créer un contrat pour un client
python epicevents.py create-contract --client-id 1 --total-amount 8000.0 --amount-due 4000.0 --unsigned

# Modifier un contrat
python epicevents.py update-contract --contract-id 3 --signed

# Attribuer un collaborateur Support à un événement
python epicevents.py update-event --event-id 4 --support-id 2
```

### 4. Opérations Équipe Commerciale (`COMMERCIAL`)

```bash
# Créer un client (attribué automatiquement au commercial connecté)
python epicevents.py create-client --full-name "Alice Martin" --email alice@corp.com --company "Corp SA"

# Modifier ses propres clients
python epicevents.py update-client --client-id 4 --phone "+33600000000"

# Créer un événement (Uniquement si le contrat est SIGNÉ)
python epicevents.py create-event --title "Lancement Produit Alice" --contract-id 1 --start "2026-10-15 10:00" --end "2026-10-15 18:00" --location "Paris Center" --attendees 100
```

### 5. Opérations Équipe Support (`SUPPORT`)

```bash
# Modifier les détails d'un événement sous sa responsabilité
python epicevents.py update-event --event-id 1 --location "Le Palais des Congrès" --notes "Installation sono à 8h."
```

---

## 🔒 Sécurité et Bonnes Pratiques

1. **Prévention des Injections SQL** : Utilisation exclusive des requêtes paramétrées via l'ORM SQLAlchemy 2.0.
2. **Hachage des Mots de Passe** : Mots de passe salés et hachés avec **Argon2** (`passlib[argon2]`). Aucun mot de passe en clair.
3. **Protection des Jetons de Session** : Le jeton JWT est enregistré sous `~/.epic_events_token` avec des autorisations système `chmod 0600`.
4. **Contrôle d'Accès Basé sur les Rôles (RBAC)** : Décorateurs d'autorisation `@require_role(...)` et vérification de propriété des entités.
5. **Gestion des Secrets** : Exclusion de `.env` dans [.gitignore](.gitignore). Seul un modèle non-sensible [.env.example](.env.example) est versionné.
6. **Journalisation Sentry.io** : Log d'audit émis pour la création/modification d'utilisateurs, la signature de contrats et la capture automatique des exceptions inattendues.

---

## 📄 Licence

Projet développé pour Epic Events CRM. Tous droits réservés.
