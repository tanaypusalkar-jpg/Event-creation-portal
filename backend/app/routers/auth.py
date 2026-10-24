from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.deps import require_admin
from app.limiter import limiter
from app.models import AdminUser
from app.schemas import LoginRequest
from app.security import COOKIE_NAME, create_access_token, hash_password, verify_password

router = APIRouter()

# Used to keep response time similar when the email does not exist.
_DUMMY_HASH = hash_password("not-a-real-password")


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    admin = db.scalar(select(AdminUser).where(AdminUser.email == email))
    ok = verify_password(payload.password, admin.password_hash if admin else _DUMMY_HASH)
    if not admin or not ok or not admin.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(admin.id))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    return {"email": admin.email}


@router.post("/logout", status_code=204)
def logout():
    response = Response(status_code=204)
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
    return response


@router.get("/me")
def me(admin: AdminUser = Depends(require_admin)):
    return {"email": admin.email}
