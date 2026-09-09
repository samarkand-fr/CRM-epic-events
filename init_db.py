from db import engine, Base
import models  # Ensure all models are registered

def init_db(reset: bool = True):
    print("Re-creating all database tables in PostgreSQL...")
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables recreated successfully!")

if __name__ == "__main__":
    init_db(reset=True)
