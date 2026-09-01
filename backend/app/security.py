import hashlib
import hmac
import os
import base64
from datetime import datetime, timedelta
from typing import Optional
from cryptography.fernet import Fernet
import jwt
from app.config import settings

# Ensure valid 32-byte urlsafe base64 key for Fernet encryption
def _get_fernet() -> Fernet:
    raw_key = settings.ENCRYPTION_KEY.encode("utf-8")
    if len(raw_key) != 44:
        hashed = base64.urlsafe_b64encode(raw_key.ljust(32)[:32])
        return Fernet(hashed)
    return Fernet(raw_key)

fernet = _get_fernet()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + pw_hash).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        decoded = base64.b64decode(hashed_password.encode('utf-8'))
        salt = decoded[:16]
        stored_hash = decoded[16:]
        new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(stored_hash, new_hash)
    except Exception:
        return False

def encrypt_credential(secret: str) -> str:
    if not secret:
        return ""
    return fernet.encrypt(secret.encode("utf-8")).decode("utf-8")

def decrypt_credential(encrypted_secret: str) -> str:
    if not encrypted_secret:
        return ""
    try:
        return fernet.decrypt(encrypted_secret.encode("utf-8")).decode("utf-8")
    except Exception:
        return encrypted_secret

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
