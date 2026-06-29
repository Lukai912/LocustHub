import hashlib
import hmac

from fastapi import Header, HTTPException, status


def hash_password(username: str, password: str) -> str:
    # Stage 8 keeps password verification local and dependency-free for the
    # MVP. The helper boundary lets production replace this with bcrypt or an
    # external IdP without changing route code.
    raw = f"locusthub:v1:{username}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_password(username: str, password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return hmac.compare_digest(hash_password(username, password), password_hash)


def require_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return token
