import base64
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import jwt
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ensure valid 32-byte urlsafe base64 key for Fernet encryption
def _get_fernet() -> Fernet:
    raw_key = settings.ENCRYPTION_KEY.encode("utf-8")
    if len(raw_key) != 44:
        # Generate deterministic 32-byte base64 encoded key from setting string
        hashed = base64.urlsafe_b64encode(raw_key.ljust(32)[:32])
        return Fernet(hashed)
    return Fernet(raw_key)

fernet = _get_fernet()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
        return encrypted_secret  # Fallback if unencrypted

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
