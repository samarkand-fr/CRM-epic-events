import sys
from sqlalchemy import text
from db import SessionLocal

def test_db_connection():
    print("Testing connection to PostgreSQL database...")
    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1;"))
            row = result.fetchone()
            assert row is not None and row[0] == 1
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la base de données : {e}")
        assert False, f"Database connection failed: {e}"

if __name__ == "__main__":
    test_db_connection()
    sys.exit(0)

