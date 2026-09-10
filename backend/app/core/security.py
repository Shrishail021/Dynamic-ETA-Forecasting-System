"""
Authentication and security dependencies.
Implements signed JWT generation/decoding, role verification (admin, staff, public),
and password hashing backed by the SQLite users table.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.db.database import get_db_connection, verify_password

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_admin_token: Optional[str] = Header(default=None, alias="x-admin-token"),
) -> Dict[str, Any]:
    # 1. Backwards-compatible demo token check
    if x_admin_token and x_admin_token == settings.DEMO_ADMIN_TOKEN:
        return {"username": "admin_demo", "role": "admin"}

    # 2. Extract Bearer Token
    token = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif x_admin_token:
        token = x_admin_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode JWT
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload["sub"]
    role = payload.get("role", "public")

    # Verify user exists in SQLite
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            # If payload is valid token signed by us, allow role from token
            return {"username": username, "role": role}
        return {"username": user_row["username"], "role": user_row["role"]}


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )
    return current_user


def require_staff(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") not in ("admin", "staff"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or Admin privileges required for this operation",
        )
    return current_user
