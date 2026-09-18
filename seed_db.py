from datetime import datetime, timedelta, timezone
from db import SessionLocal, engine, Base
from init_db import init_db
from models import Role, User, Client, Contract, Event
from security import hash_password


def seed_database():
    print("Initialising database tables and seeding roles, default users, clients, contracts, and events...")
    init_db(reset=True)
    db = SessionLocal()
    try:
        # 1. Create Default Roles
        roles_data = [
            ("COMMERCIAL", "Département commercial - Démarchage clients et création événements"),
            ("SUPPORT", "Département support - Organisation et déroulé des événements"),
            ("GESTION", "Département gestion - Gestion collaborateurs, contrats et attribution support"),
        ]

        role_map = {}
        for role_name, description in roles_data:
            role = Role(name=role_name, description=description)
            db.add(role)
            db.commit()
            db.refresh(role)
            role_map[role_name] = role

        # 2. Create Default Test Users
        users_data = [
            {
                "employee_number": "EMP001",
                "full_name": "Bill Boquet",
                "email": "bill.boquet@epicevents.io",
                "password": "Password123!",
                "role": role_map["COMMERCIAL"],
            },
            {
                "employee_number": "EMP002",
                "full_name": "Kate Hastroff",
                "email": "kate.hastroff@epicevents.io",
                "password": "Password123!",
                "role": role_map["SUPPORT"],
            },
            {
                "employee_number": "EMP003",
                "full_name": "Admin Gestion",
                "email": "gestion@epicevents.io",
                "password": "Password123!",
                "role": role_map["GESTION"],
            },
        ]

        user_map = {}
        for u in users_data:
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

        bill = user_map["EMP001"]
        kate = user_map["EMP002"]

        # 3. Create Sample Clients
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

        # 4. Create Sample Contracts
        k1 = Contract(
            client_id=c1.id,
            commercial_contact_id=bill.id,
            total_amount=5000.0,
            amount_due=2500.0,
            is_signed=True,
        )
        k2 = Contract(
            client_id=c2.id,
            commercial_contact_id=bill.id,
            total_amount=10000.0,
            amount_due=5000.0,
            is_signed=True,
        )
        k3 = Contract(
            client_id=c3.id,
            commercial_contact_id=bill.id,
            total_amount=15000.0,
            amount_due=15000.0,
            is_signed=False,
        )
        db.add_all([k1, k2, k3])
        db.commit()
        db.refresh(k1)
        db.refresh(k2)
        db.refresh(k3)

        # 5. Create Sample Events
        now = datetime.now(timezone.utc)
        e1 = Event(
            title="Kevin Casey Party",
            contract_id=k1.id,
            client_id=c1.id,
            event_date_start=now + timedelta(days=5),
            event_date_end=now + timedelta(days=6),
            support_contact_id=kate.id,
            location="10 Rue de Paris, Paris",
            attendees=50,
            notes="Cocktail & DJ",
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
            support_contact_id=None,  # No support contact assigned yet!
            location="Salle des fêtes de Mufflins",
            attendees=200,
            notes="Assemblée générale des actionnaires (~200 personnes).",
        )
        db.add_all([e1, e2, e3])
        db.commit()

        print("✅ Database seeding completed with Roles, Users, Clients, Contracts, and Events!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during database seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
