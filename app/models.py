from sqlalchemy import (Table, Column, Integer, String, Date, Boolean, MetaData,
DateTime, ForeignKey)
from datetime import datetime

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("first_name", String, nullable=False),
    Column("last_name", String, nullable=False),
    Column("login", String, unique=True, nullable=False),
    Column("password", String, nullable=False),
    Column("birth_date", Date, nullable=False),
    Column("is_admin", Boolean, nullable=False),
    Column("is_blocked", Boolean, nullable=False, default=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

email_verifications = Table(
    "email_verifications",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    Column("email", String, unique=True, nullable=False),
    Column("verification_code", String, nullable=True),
    Column("code_created_at", DateTime, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)