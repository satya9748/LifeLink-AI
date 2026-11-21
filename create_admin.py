
from getpass import getpass

from app.db.database import SessionLocal
from app.models import User
from app.core.security import hash_password

db = SessionLocal()

try:
    email = input("Enter Admin email: ").strip().lower()

    existing = db.query(User).filter(User.email == email).first()

    if existing:
        print("This email is already registered.")
    else:
        full_name = input("Enter Admin name: ").strip()
        password = getpass("Enter Admin password: ")
        confirm = getpass("Confirm Admin password: ")

        if password != confirm:
            print("Passwords do not match.")
        elif len(password) < 8:
            print("Password must contain at least 8 characters.")
        else:
            admin = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role="admin",
                is_active=True,
                is_verified=True
            )

            db.add(admin)
            db.commit()

            print("Admin account created successfully!")

finally:
    db.close()