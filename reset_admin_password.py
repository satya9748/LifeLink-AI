
from getpass import getpass
from app.db.database import SessionLocal
from app.models import User
from app.core.security import hash_password

db = SessionLocal()

try:
    email = input("Enter Admin email: ").strip().lower()
    admin = db.query(User).filter(
        User.email == email,
        User.role == "admin"
    ).first()

    if not admin:
        print("Admin account not found.")
    else:
        password = getpass("Enter new Admin password: ")
        confirm = getpass("Confirm new password: ")

        if password != confirm:
            print("Passwords do not match.")
        elif len(password) < 8:
            print("Password must be at least 8 characters.")
        else:
            admin.password_hash = hash_password(password)
            db.commit()
            print("Admin password reset successfully!")

finally:
    db.close()
