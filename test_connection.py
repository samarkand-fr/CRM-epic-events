import sys
from sqlalchemy import text
from db import SessionLocal

def test_db_connection():
    print("Testing connection to PostgreSQL database...")
    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1;"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Connexion à la base de données PostgreSQL réussie avec succès !")
                return True
            else:
                print("⚠️ Connexion établie mais la requête a retourné un résultat inattendu.")
                return False
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la base de données : {e}")
        return False

if __name__ == "__main__":
    success = test_db_connection()
    sys.exit(0 if success else 1)
