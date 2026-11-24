from getpass import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.staff import Staff
from app.services.auth_service import create_staff_account


def main():
    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(Staff).where(Staff.is_admin.is_(True))
        )

        if existing_admin:
            print("An administrator account already exists.")
            return

        print("\n=== SmartQueue First Administrator Setup ===")

        username = input("Choose admin username: ").strip().lower()
        full_name = input("Enter your full name: ").strip()

        if len(username) < 3 or len(username) > 80:
            print("Username must be between 3 and 80 characters.")
            return

        if len(full_name) < 2 or len(full_name) > 120:
            print("Full name must be between 2 and 120 characters.")
            return

        password = getpass("Create password (minimum 12 characters): ")
        confirm_password = getpass("Confirm password: ")

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        try:
            admin = create_staff_account(
                db=db,
                username=username,
                full_name=full_name,
                password=password,
                is_admin=True,
            )
        except ValueError as error:
            print(f"Could not create administrator: {error}")
            return

        print("\nAdministrator account created successfully.")
        print(f"Username: {admin.username}")
        print("Your password is securely hashed.")


if __name__ == "__main__":
    main()
