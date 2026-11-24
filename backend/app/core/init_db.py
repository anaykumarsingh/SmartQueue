from app.core.database import Base, engine
from app.models.queue import Service, Counter, QueueToken, ServiceRecord
from app.models.staff import Staff


def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")
    print("Tables:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    initialize_database()
