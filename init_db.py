"""
Database Initialization Module (init_db.py).

This module provides a utility function to create (or reset) all database
tables based on the SQLAlchemy ORM model definitions.

It uses SQLAlchemy's metadata API to:
- Drop all existing tables (when reset=True) to ensure a clean state.
- Recreate all tables reflecting the current ORM model definitions.

Usage:
    python init_db.py          # Reset and recreate all tables
    from init_db import init_db; init_db(reset=False)  # Create only missing tables
"""

from db import engine, Base
import models  # Import all ORM model classes so they register with Base.metadata


def init_db(reset: bool = True):
    """
    Initialize the PostgreSQL database schema.

    Step 1 (optional): Drop all existing tables if reset=True to ensure a clean schema.
    Step 2: Create all tables based on SQLAlchemy ORM model definitions.

    Args:
        reset (bool): If True (default), drop existing tables before recreating.
                      Set to False to only create tables that do not exist yet.
    """
    print("Initializing PostgreSQL database tables...")

    # Step 1: Optionally drop all existing tables for a clean start
    if reset:
        print("  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)

    # Step 2: Recreate all tables from ORM model definitions
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables initialized successfully!")


if __name__ == "__main__":
    # Direct execution: perform a full reset (drop + recreate)
    init_db(reset=True)

