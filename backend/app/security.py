from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import AdminUser

password_hash = PasswordHash.recommended()
COOKIE_NAME = "event_portal_access"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hash.verify(password, hashed)
    except Exception:
        return False

def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": subject, "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "iss": "event-workshop-portal", "aud": "event-workshop-admin"
    }, settings.jwt_secret, algorithm="HS256")

def get_current_admin(request: Request, db: Session) -> AdminUser:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"],
            issuer="event-workshop-portal", audience="event-workshop-admin",
            options={"require": ["sub", "exp", "iat"]})
        admin_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired session") from None
    admin = db.get(AdminUser, admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive admin")
    return admin
