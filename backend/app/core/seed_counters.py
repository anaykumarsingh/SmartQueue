from app.core.database import SessionLocal
from app.models.queue import Service, Counter


INITIAL_COUNTERS = {
    "ACC": [
        {"counter_number": 1, "label": "Accounts Counter 1"},
        {"counter_number": 2, "label": "Accounts Counter 2"},
    ],
    "EXM": [
        {"counter_number": 1, "label": "Examination Counter 1"},
    ],
    "LIB": [
        {"counter_number": 1, "label": "Library Counter 1"},
    ],
}


def seed_counters():
    db = SessionLocal()

    try:
        for service_code, counters in INITIAL_COUNTERS.items():
            service = (
                db.query(Service)
                .filter_by(code=service_code)
                .first()
            )

            if service is None:
                print(f"Service not found: {service_code}")
                continue

            for counter_data in counters:
                existing = (
                    db.query(Counter)
                    .filter_by(
                        service_id=service.id,
                        counter_number=counter_data["counter_number"],
                    )
                    .first()
                )

                if existing is None:
                    db.add(
                        Counter(
                            service_id=service.id,
                            status="open",
                            **counter_data,
                        )
                    )
                    print(f"Added: {counter_data['label']}")
                else:
                    print(f"Already exists: {counter_data['label']}")

        db.commit()
        print("Initial counters are ready.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_counters()
