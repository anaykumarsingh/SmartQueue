from app.core.database import SessionLocal
from app.models.queue import Service


INITIAL_SERVICES = [
    {
        "code": "ACC",
        "name": "Accounts Office",
        "description": "Fee and accounts-related enquiries",
        "avg_service_minutes": 5.0,
    },
    {
        "code": "EXM",
        "name": "Examination Cell",
        "description": "Examination and academic record enquiries",
        "avg_service_minutes": 4.0,
    },
    {
        "code": "LIB",
        "name": "Library Help Desk",
        "description": "Library assistance and enquiries",
        "avg_service_minutes": 3.0,
    },
]


def seed_services():
    db = SessionLocal()

    try:
        for service_data in INITIAL_SERVICES:
            existing = (
                db.query(Service)
                .filter_by(code=service_data["code"])
                .first()
            )

            if existing is None:
                db.add(Service(**service_data))
                print(f"Added: {service_data['name']}")
            else:
                print(f"Already exists: {service_data['name']}")

        db.commit()
        print("Initial services are ready.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_services()
