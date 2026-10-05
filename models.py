"""
SQLAlchemy ORM Data Models Module (models.py).

This module defines the core domain entities for the Epic Events CRM application:
- Role: Department roles for employees (COMMERCIAL, SUPPORT, GESTION).
- User: Employee user accounts (employee_number, email, Argon2 password hash).
- Client: Clients managed by commercial representatives.
- Contract: Commercial contracts linked to clients and commercials.
- Event: Events associated with signed contracts (1-to-N relationship).
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from db import Base


class Role(Base):
    """
    ORM Model representing an employee Department / Role in Epic Events.

    Avoids hardcoding roles into user rows by providing normalized role tables.
    Valid role names: 'COMMERCIAL', 'SUPPORT', 'GESTION'.
    """
    __tablename__ = "roles"

    # Primary key column
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Unique role identifier name (e.g. COMMERCIAL)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    # 1-to-N relationship with User model
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base):
    """
    ORM Model representing an Epic Events Employee / User account.

    Stores unique employee numbers, credentials hashed with Argon2,
    and foreign key reference to assigned Role.
    """
    __tablename__ = "users"

    # Primary key column
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Unique business identifier (e.g. EMP001)
    employee_number = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Foreign key to roles table
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Eager loading (lazy="joined") prevents DetachedInstanceError outside active DB sessions
    role = relationship("Role", back_populates="users", foreign_keys=[role_id], lazy="joined")
    clients = relationship("Client", back_populates="commercial_contact", foreign_keys="Client.commercial_contact_id")
    contracts = relationship("Contract", back_populates="commercial_contact", foreign_keys="Contract.commercial_contact_id")
    events = relationship("Event", back_populates="support_contact", foreign_keys="Event.support_contact_id")

    def __repr__(self):
        return f"<User(id={self.id}, emp_num='{self.employee_number}', name='{self.full_name}')>"


class Client(Base):
    """
    ORM Model representing a Client account in Epic Events CRM.

    Each client is assigned to a Commercial representative (User).
    """
    __tablename__ = "clients"

    # Primary key column
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    company_name = Column(String(150), nullable=True)
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_update = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Foreign key link to assigned commercial user
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships with eager join loading
    commercial_contact = relationship("User", back_populates="clients", foreign_keys=[commercial_contact_id], lazy="joined")
    contracts = relationship("Contract", back_populates="client", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, full_name='{self.full_name}', company='{self.company_name}')>"


class Contract(Base):
    """
    ORM Model representing a Commercial Contract.

    Stores total financial amount, balance due, signature status, and client/commercial links.
    1-to-N relationship with Events (a signed contract can spawn multiple events).
    """
    __tablename__ = "contracts"

    # Primary key column
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    amount_due = Column(Float, nullable=False, default=0.0)
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_signed = Column(Boolean, nullable=False, default=False)

    # ORM Navigation Relationships
    client = relationship("Client", back_populates="contracts", foreign_keys=[client_id], lazy="joined")
    commercial_contact = relationship("User", back_populates="contracts", foreign_keys=[commercial_contact_id], lazy="joined")
    events = relationship("Event", back_populates="contract", cascade="all, delete-orphan", lazy="joined")

    def __repr__(self):
        return f"<Contract(id={self.id}, client_id={self.client_id}, is_signed={self.is_signed}, total_amount={self.total_amount})>"


class Event(Base):
    """
    ORM Model representing an Event hosted by Epic Events.

    Linked to a signed contract, a client, and optionally an assigned Support employee.
    """
    __tablename__ = "events"

    # Primary key column
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    event_date_start = Column(DateTime, nullable=False)
    event_date_end = Column(DateTime, nullable=False)

    # Optional Support contact assigned by GESTION department
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    location = Column(String(255), nullable=False)
    attendees = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    # Eager joined relationship objects
    contract = relationship("Contract", back_populates="events", foreign_keys=[contract_id], lazy="joined")
    client = relationship("Client", back_populates="events", foreign_keys=[client_id], lazy="joined")
    support_contact = relationship("User", back_populates="events", foreign_keys=[support_contact_id], lazy="joined")

    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', contract_id={self.contract_id}, support_contact_id={self.support_contact_id})>"

