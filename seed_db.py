from db import SessionLocal, engine, Base
from init_db import init_db
from models import Role, User
from security import hash_password


def seed_database():
    print("Initialising database tables and seeding roles and default users...")
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
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=description)
                db.add(role)
                db.commit()
                db.refresh(role)
                print(f"  Role created: {role.name}")
            role_map[role_name] = role

        # 2. Create Default Test Users with Argon2 salted/hashed passwords
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

        for u in users_data:
            user = db.query(User).filter(User.email == u["email"]).first()
            if not user:
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
                print(f"  User created: {user.full_name} ({user.employee_number}) - Role: {u['role'].name}")

        print("✅ Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during database seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
