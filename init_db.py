from db import engine, Base
import models  # Ensure all models are imported so Base metadata knows about them

def init_db():
    print("Creating all tables in PostgreSQL database...")
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created successfully!")

if __name__ == "__main__":
    init_db()
