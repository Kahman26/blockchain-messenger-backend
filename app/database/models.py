from sqlalchemy import (
    Table, Column, Integer, BigInteger, String, Text, DateTime, ForeignKey,
    MetaData, CheckConstraint, Numeric, UniqueConstraint, CHAR, Date, Boolean
)
from sqlalchemy.sql import func

metadata = MetaData()

Notifications = Table(
    "Notifications", metadata,
    Column("notification_id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("Users.user_id"), nullable=False),
    Column("notification_content", Text, nullable=False),
    Column("sent_at", DateTime, nullable=False, server_default=func.now()),
    Column("read_at", DateTime),
)

Contacts = Table(
    "Contacts", metadata,
    Column("contact_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("Users.user_id"), nullable=False),
    Column("contact_user_id", Integer, nullable=False),
    Column("added_at", DateTime, nullable=False, server_default=func.now()),
)

Chats = Table(
    "Chats", metadata,
    Column("chat_id", BigInteger, primary_key=True, autoincrement=True),
    Column("chat_name", String(100)),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
    Column("chat_type", String(20), nullable=False),
    Column("creator_user_id", Integer, nullable=False),
    Column("description", Text),
    CheckConstraint("chat_type IN ('private', 'group', 'channel')")
)

UserSettings = Table(
    "UserSettings", metadata,
    Column("setting_id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("Users.user_id"), nullable=False),
    Column("setting_key", String(50), nullable=False),
    Column("setting_value", String(255), nullable=False),
    Column("edited_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

BannedUsers = Table(
    "BannedUsers", metadata,
    Column("ban_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("Users.user_id"), nullable=False),
    Column("banned_at", DateTime, nullable=False, server_default=func.now()),
    Column("unban_at", DateTime),
    Column("reason", Text),
)

Roles = Table(
    "Roles", metadata,
    Column("role_id", Integer, primary_key=True, autoincrement=True),
    Column("role_name", String(50), nullable=False),
    Column("role_description", Text),
    CheckConstraint("role_name IN ('owner', 'admin', 'moderator', 'muted')")
)


Users = Table(
    "Users", metadata,
    Column("user_id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(50), nullable=False),
    Column("first_name", String(50)),
    Column("last_name", String(100)),
    Column("phone_number", String(30)),
    Column("email", String(100), nullable=False),
    Column("password_hash", String(128), nullable=False),
    Column("birth_date", Date, nullable=False),
    Column("last_seen", DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
    Column("is_activated_acc", Boolean, default=False),
)

Email_verifications = Table(
    "Email_verifications",
    metadata,
    Column("user_id", Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("verification_code", String, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

Admins = Table(
    "Admins", metadata,
    Column("user_id", Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime, nullable=False, server_default=func.now()),
    Column("active", Boolean, nullable=False, server_default="true"),
    Column("notes", Text),
)


ChatMembers = Table(
    "ChatMembers", metadata,
    Column("chat_id", BigInteger, ForeignKey("Chats.chat_id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("Users.user_id"), primary_key=True),
    Column("joined_at", DateTime, nullable=False, server_default=func.now()),
)

ChatUserRoles = Table(
    "ChatUserRoles", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("chat_id", BigInteger, ForeignKey("Chats.chat_id", ondelete="CASCADE"), nullable=False),
    Column("user_id", Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False),
    Column("role_id", Integer, ForeignKey("Roles.role_id"), nullable=False),
    Column("assigned_at", DateTime, nullable=False, server_default=func.now()),
)

PaymentMethods = Table(
    "PaymentMethods", metadata,
    Column("payment_method_id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(50), nullable=False, unique=True),
    Column("description", Text),
    Column("icon_url", String(255)),
)

Payments = Table(
    "Payments", metadata,
    Column("payment_id", BigInteger, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False),
    Column("amount", Numeric(10, 4), nullable=False),
    Column("payment_method_id", Integer, ForeignKey("PaymentMethods.payment_method_id"), nullable=False),
    Column("payment_date", DateTime, nullable=False, server_default=func.now()),
)

BlockchainBlocks = Table(
    "BlockchainBlocks", metadata,
    Column("block_id", BigInteger, primary_key=True, autoincrement=True),
    Column("previous_hash", CHAR(64), nullable=False),
    Column("block_hash", CHAR(64), nullable=False, unique=True),
    Column("timestamp", DateTime, nullable=False, server_default=func.now()),
    Column("nonce", BigInteger, nullable=False),
    Column("creator_user_id", Integer, ForeignKey("Users.user_id")),
)

BlockchainTransactions = Table(
    "BlockchainTransactions", metadata,
    Column("transaction_id", BigInteger, primary_key=True, autoincrement=True),
    Column("block_id", Integer, ForeignKey("BlockchainBlocks.block_id", ondelete="CASCADE"), nullable=False),
    Column("sender_id", Integer, ForeignKey("Users.user_id"), nullable=False),
    Column("receiver_id", Integer, ForeignKey("Users.user_id"), nullable=False),
    Column("chat_id", BigInteger, ForeignKey("Chats.chat_id"), nullable=True),  # <--- НОВОЕ
    Column("payload_hash", CHAR(64), nullable=False),
    Column("signature", Text, nullable=False),
    Column("timestamp", DateTime, nullable=False, server_default=func.now()),
)

BlockchainPayloads = Table(
    "BlockchainPayloads", metadata,
    Column("payload_id", BigInteger, primary_key=True, autoincrement=True),
    Column("transaction_id", Integer, ForeignKey("BlockchainTransactions.transaction_id", ondelete="CASCADE"), nullable=False),
    Column("encrypted_data", Text, nullable=False),
)

UserKeys = Table(
    "UserKeys", metadata,
    Column("user_id", Integer, ForeignKey("Users.user_id"), primary_key=True),
    Column("public_key", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)

BlockchainFiles = Table(
    "BlockchainFiles", metadata,
    Column("file_id", BigInteger, primary_key=True, autoincrement=True),
    Column("transaction_id", BigInteger, ForeignKey("BlockchainTransactions.transaction_id", ondelete="CASCADE"), nullable=False),
    Column("file_name", String(255), nullable=False),
    Column("mime_type", String(100), nullable=False),
    Column("file_url", Text, nullable=False),  # ссылка на зашифрованный файл в хранилище
    Column("file_size", BigInteger, nullable=False),  # размер в байтах
    Column("encrypted_key", Text, nullable=False),  # AES-ключ, зашифрованный публичным ключом получателя
    Column("file_hash", String(64), nullable=False),  # SHA256 хеш исходного файла
    Column("thumbnail_base64", Text),  # превью (опционально, например, для изображений)
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)
