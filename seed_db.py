"""
Database Seeding Script (seed_db.py).

This script populates the PostgreSQL database with realistic sample data
for development and demonstration purposes. It performs a full reset before seeding.

Seeding Steps:
    1. Drop and recreate all database tables (via init_db.init_db).
    2. Create the three department roles: COMMERCIAL, SUPPORT, GESTION.
    3. Create three default test users (one per department).
    4. Create three sample clients assigned to the COMMERCIAL user.
    5. Create three contracts (two signed, one unsigned).
    6. Create four events for signed contracts (demonstrating 1-to-N Contract→Events).

Usage:
    python seed_db.py

Security:
    Default user password is loaded from DEFAULT_SEED_PASSWORD environment variable.
    Falls back to 'Password123!' if not set (for local dev only).
    Never hardcode production passwords in source code.
"""

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from db import SessionLocal, engine, Base
from init_db import init_db
from models import Role, User, Client, Contract, Event
from security import hash_password

# Load environment variables from .env file
load_dotenv()

# Step 0: Load seed password from environment (never hardcode credentials)
DEFAULT_PASSWORD = os.getenv("DEFAULT_SEED_PASSWORD", "Password123!")


def seed_database():
    """
    Seeds the PostgreSQL database with demo data.

    Drops and recreates all tables, then populates with:
    - 3 Roles (COMMERCIAL, SUPPORT, GESTION)
    - 3 Users (one per department)
    - 3 Clients (assigned to the commercial user)
    - 3 Contracts (k1=signed, k2=signed, k3=unsigned)
    - 4 Events (demonstrating 1-to-N contract→events relationship)
    """
    print("Initializing database and seeding roles, users, clients, contracts, and events...")

    # Step 1: Reset database (drop + recreate all tables)
    init_db(reset=True)
    db = SessionLocal()
    try:
        # Step 2: Create the three department roles
        roles_data = [
            ("COMMERCIAL", "Sales department - Client acquisition and event creation"),
            ("SUPPORT", "Support department - Event logistics and execution"),
            ("GESTION", "Management department - Employees, contracts, and support assignment"),
        ]

        role_map = {}
        for role_name, description in roles_data:
            role = Role(name=role_name, description=description)
            db.add(role)
            db.commit()
            db.refresh(role)
            role_map[role_name] = role
        print(f"  ✓ {len(role_map)} department roles created.")

        # Step 3: Create three default test users (one per department)
        users_data = [
            {
                "employee_number": "EMP001",
                "full_name": "Bill Boquet",
                "email": "bill.boquet@epicevents.io",
                "password": DEFAULT_PASSWORD,
                "role": role_map["COMMERCIAL"],
            },
            {
                "employee_number": "EMP002",
                "full_name": "Kate Hastroff",
                "email": "kate.hastroff@epicevents.io",
                "password": DEFAULT_PASSWORD,
                "role": role_map["SUPPORT"],
            },
            {
                "employee_number": "EMP003",
                "full_name": "Admin Gestion",
                "email": "gestion@epicevents.io",
                "password": DEFAULT_PASSWORD,
                "role": role_map["GESTION"],
            },
        ]

        user_map = {}
        for u in users_data:
            # Hash password with Argon2 before storing (never store plaintext)
            user = User(
                employee_number=u["employee_number"],
                full_name=u["full_name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role_id=u["role"].id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_map[u["employee_number"]] = user
        print(f"  ✓ {len(user_map)} users created.")

        # Shortcut references to commercial and support users
        bill = user_map["EMP001"]  # COMMERCIAL
        kate = user_map["EMP002"]  # SUPPORT

        # Step 4: Create three sample clients assigned to the commercial user
        c1 = Client(
            full_name="Kevin Casey",
            email="kevin@startup.io",
            phone="+678 123 456 78",
            company_name="Cool Startup LLC",
            commercial_contact_id=bill.id,
        )
        c2 = Client(
            full_name="John Ouick",
            email="john.ouick@gmail.com",
            phone="+1 234 567 8901",
            company_name="Ouick Events",
            commercial_contact_id=bill.id,
        )
        c3 = Client(
            full_name="Lou Bouzin",
            email="jacky@loubouzin.grd",
            phone="+666 12345",
            company_name="Lou Bouzin Corp",
            commercial_contact_id=bill.id,
        )
        db.add_all([c1, c2, c3])
        db.commit()
        db.refresh(c1)
        db.refresh(c2)
        db.refresh(c3)
        print("  ✓ 3 sample clients created.")

        # Step 5: Create three contracts (two signed, one unsigned)
        # k1 & k2 are signed → eligible for event creation
        # k3 is unsigned → events cannot be created until signed
        k1 = Contract(
            client_id=c1.id,
            commercial_contact_id=bill.id,
            total_amount=5000.0,
            amount_due=2500.0,
            is_signed=True,  # Signed: eligible for events
        )
        k2 = Contract(
            client_id=c2.id,
            commercial_contact_id=bill.id,
            total_amount=10000.0,
            amount_due=5000.0,
            is_signed=True,  # Signed: eligible for events
        )
        k3 = Contract(
            client_id=c3.id,
            commercial_contact_id=bill.id,
            total_amount=15000.0,
            amount_due=15000.0,
            is_signed=False,  # Not signed yet: events cannot be created
        )
        db.add_all([k1, k2, k3])
        db.commit()
        db.refresh(k1)
        db.refresh(k2)
        db.refresh(k3)
        print("  ✓ 3 contracts created (2 signed, 1 unsigned).")

        # Step 6: Create four sample events (demonstrates 1-to-N: Contract → Events)
        # k1 has 2 events (Main Party + After-Party)
        # k2 has 1 event (Wedding)
        # k3 has 1 event with NO support assigned (contract unsigned in reality, added for demo)
        now = datetime.now(timezone.utc)

        e1 = Event(
            title="Kevin Casey Main Party",
            contract_id=k1.id,
            client_id=c1.id,
            event_date_start=now + timedelta(days=5),
            event_date_end=now + timedelta(days=6),
            support_contact_id=kate.id,  # Kate assigned as support
            location="10 Rue de Paris, Paris",
            attendees=50,
            notes="Cocktail & DJ",
        )
        e4 = Event(
            title="Kevin Casey After-Party",
            contract_id=k1.id,  # Same contract (demonstrates 1-to-N: one contract, multiple events)
            client_id=c1.id,
            event_date_start=now + timedelta(days=6, hours=2),
            event_date_end=now + timedelta(days=6, hours=8),
            support_contact_id=kate.id,
            location="Le Club Secret, Paris",
            attendees=30,
            notes="Late night lounge after-party",
        )
        e2 = Event(
            title="John Ouick Wedding",
            contract_id=k2.id,
            client_id=c2.id,
            event_date_start=now + timedelta(days=15),
            event_date_end=now + timedelta(days=16),
            support_contact_id=kate.id,
            location="53 Rue du Château, 41120 Candé-sur-Beuvron, France",
            attendees=75,
            notes="Wedding starts at 3PM by the river.",
        )
        e3 = Event(
            title="Lou Bouzin General Assembly",
            contract_id=k3.id,
            client_id=c3.id,
            event_date_start=now + timedelta(days=30),
            event_date_end=now + timedelta(days=30, hours=5),
            support_contact_id=None,  # No support assigned yet - GESTION must assign
            location="Salle des fêtes de Mufflins",
            attendees=200,
            notes="General shareholders assembly (~200 attendees).",
        )
        db.add_all([e1, e4, e2, e3])
        db.commit()
        print("  ✓ 4 sample events created.")

        print("\n✅ Database seeding completed successfully!")
        print("   Login: bill.boquet@epicevents.io / kate.hastroff@epicevents.io / gestion@epicevents.io")
        print(f"   Password for all accounts: {DEFAULT_PASSWORD}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

