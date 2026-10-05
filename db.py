"""
Database Engine and Session Configuration Module (db.py).

This module manages the connection to the PostgreSQL database using SQLAlchemy.
It loads the database connection URL from the environment (.env)
and initializes the SQLAlchemy engine, session maker, and declarative Base class.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Step 1: Load environment variables from .env file
load_dotenv()

# Step 2: Retrieve PostgreSQL database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Security validation: Prevent app execution if DATABASE_URL is not configured
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is missing. "
        "Please create a .env file from .env.example with valid database credentials."
    )

# Step 3: Initialize SQLAlchemy Database Engine
# future=True enables SQLAlchemy 2.0+ execution standards
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries during development
    future=True,
)

# Step 4: Create SQLAlchemy Session Factory
# autocommit=False and autoflush=False ensure explicit transactional control
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Step 5: Declarative Base Class for ORM Data Models
Base = declarative_base()

