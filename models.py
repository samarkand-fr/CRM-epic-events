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
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    # Relationship to User
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_number = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships with eager loading for role to prevent DetachedInstanceError
    role = relationship("Role", back_populates="users", foreign_keys=[role_id], lazy="joined")
    clients = relationship("Client", back_populates="commercial_contact", foreign_keys="Client.commercial_contact_id")
    contracts = relationship("Contract", back_populates="commercial_contact", foreign_keys="Contract.commercial_contact_id")
    events = relationship("Event", back_populates="support_contact", foreign_keys="Event.support_contact_id")

    def __repr__(self):
        return f"<User(id={self.id}, emp_num='{self.employee_number}', name='{self.full_name}')>"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    company_name = Column(String(150), nullable=True)
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_update = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    commercial_contact = relationship("User", back_populates="clients", foreign_keys=[commercial_contact_id])
    contracts = relationship("Contract", back_populates="client", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, full_name='{self.full_name}', company='{self.company_name}')>"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    amount_due = Column(Float, nullable=False, default=0.0)
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_signed = Column(Boolean, nullable=False, default=False)

    # Relationships
    client = relationship("Client", back_populates="contracts", foreign_keys=[client_id])
    commercial_contact = relationship("User", back_populates="contracts", foreign_keys=[commercial_contact_id])
    event = relationship("Event", back_populates="contract", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contract(id={self.id}, client_id={self.client_id}, is_signed={self.is_signed}, total_amount={self.total_amount})>"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    event_date_start = Column(DateTime, nullable=False)
    event_date_end = Column(DateTime, nullable=False)

    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    location = Column(String(255), nullable=False)
    attendees = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    # Relationships
    contract = relationship("Contract", back_populates="event", foreign_keys=[contract_id])
    client = relationship("Client", back_populates="events", foreign_keys=[client_id])
    support_contact = relationship("User", back_populates="events", foreign_keys=[support_contact_id])

    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', support_contact_id={self.support_contact_id})>"
