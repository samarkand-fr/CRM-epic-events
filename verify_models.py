import sys
from datetime import datetime, timedelta, timezone
from db import SessionLocal
from models import User, DepartmentEnum, Client, Contract, Event


def test_models():
    print("Testing ORM models creation and relationships...")
    db = SessionLocal()
    try:
        # Clean up existing test data
        db.query(Event).delete()
        db.query(Contract).delete()
        db.query(Client).delete()
        db.query(User).delete()
        db.commit()

        # 1. Create Users for each department
        commercial_user = User(
            full_name="Bill Boquet",
            email="bill.boquet@epicevents.io",
            password_hash="hashed_password_commercial",
            department=DepartmentEnum.COMMERCIAL,
        )
        support_user = User(
            full_name="Kate Hastroff",
            email="kate.hastroff@epicevents.io",
            password_hash="hashed_password_support",
            department=DepartmentEnum.SUPPORT,
        )
        gestion_user = User(
            full_name="Admin Gestion",
            email="gestion@epicevents.io",
            password_hash="hashed_password_gestion",
            department=DepartmentEnum.GESTION,
        )
        db.add_all([commercial_user, support_user, gestion_user])
        db.commit()
        db.refresh(commercial_user)
        db.refresh(support_user)
        db.refresh(gestion_user)
        print(f"  Created Users: {commercial_user}, {support_user}, {gestion_user}")

        # 2. Create Client associated with commercial
        client = Client(
            full_name="John Ouick",
            email="john.ouick@gmail.com",
            phone="+1 234 567 8901",
            company_name="Ouick Inc.",
            commercial_contact_id=commercial_user.id,
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        print(f"  Created Client: {client}")
        assert client.commercial_contact.full_name == "Bill Boquet"

        # 3. Create Contract for Client
        contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=5000.0,
            amount_due=2500.0,
            is_signed=True,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        print(f"  Created Contract: {contract}")
        assert contract.client.full_name == "John Ouick"
        assert contract.commercial_contact.full_name == "Bill Boquet"

        # 4. Create Event for signed Contract
        now = datetime.now(timezone.utc)
        event = Event(
            title="John Ouick Wedding",
            contract_id=contract.id,
            client_id=client.id,
            event_date_start=now + timedelta(days=10),
            event_date_end=now + timedelta(days=11),
            support_contact_id=support_user.id,
            location="53 Rue du Château, 41120 Candé-sur-Beuvron, France",
            attendees=75,
            notes="Wedding starts at 3PM, by the river.",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        print(f"  Created Event: {event}")
        assert event.contract.id == contract.id
        assert event.client.email == "john.ouick@gmail.com"
        assert event.support_contact.full_name == "Kate Hastroff"

        print("✅ Models verification succeeded! All entities and relationships are valid.")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error during models verification: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_models()
    sys.exit(0 if success else 1)
