from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AdminUser
from app.security import get_current_admin


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """FastAPI dependency wrapper around security.get_current_admin."""
    return get_current_admin(request, db)
