# app/utils/blockchain.py

import json
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, b64decode
from datetime import datetime

# ------------------------------
# Хеширование блока
# ------------------------------

def calculate_hash(block_data: dict) -> str:
    block_string = json.dumps(block_data, sort_keys=True, default=str).encode()
    return hashlib.sha256(block_string).hexdigest()

# ------------------------------
# Генерация ключей (только для теста)
# ------------------------------

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return priv_pem.decode(), pub_pem.decode()

# ------------------------------
# Шифрование сообщения (E2E)
# ------------------------------

def encrypt_message(message: str, recipient_public_pem: str) -> str:
    public_key = serialization.load_pem_public_key(recipient_public_pem.encode(), backend=default_backend())
    encrypted = public_key.encrypt(
        message.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return b64encode(encrypted).decode()

# ------------------------------
# Расшифровка сообщения (на клиенте, не на сервере)
# ------------------------------

def decrypt_message(encrypted_b64: str, recipient_private_pem: str) -> str:
    private_key = serialization.load_pem_private_key(recipient_private_pem.encode(), password=None, backend=default_backend())
    decrypted = private_key.decrypt(
        b64decode(encrypted_b64),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return decrypted.decode()

# ------------------------------
# Подпись сообщения
# ------------------------------

def sign_message(message: str, sender_private_pem: str) -> str:
    private_key = serialization.load_pem_private_key(sender_private_pem.encode(), password=None, backend=default_backend())
    signature = private_key.sign(
        message.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return b64encode(signature).decode()

# ------------------------------
# Проверка подписи
# ------------------------------

def verify_signature(message: str, signature_b64: str, sender_public_pem: str) -> bool:
    public_key = serialization.load_pem_public_key(sender_public_pem.encode(), backend=default_backend())
    try:
        public_key.verify(
            b64decode(signature_b64),
            message.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# ------------------------------
# Сборка данных блока
# ------------------------------

def generate_block_data(previous_hash: str, transactions: list, nonce: int) -> dict:
    return {
        "previous_hash": previous_hash,
        "transactions": transactions,
        "timestamp": datetime.utcnow().isoformat(),
        "nonce": nonce,
    }
