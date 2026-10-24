from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import AdminUser
from app.security import hash_password

def main():
    if settings.app_env == "production" and settings.admin_password == "change-me":
        raise SystemExit("Refusing to seed default admin credentials in production.")
    with SessionLocal() as db:
        email = settings.admin_email.strip().lower()
        if db.scalar(select(AdminUser).where(AdminUser.email == email)):
            print(f"Admin {email} already exists.")
            return
        db.add(AdminUser(email=email, password_hash=hash_password(settings.admin_password)))
        db.commit()
        print(f"Created admin {email}. Keep credentials secret.")

if __name__ == "__main__":
    main()
