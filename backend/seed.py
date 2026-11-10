from sqlalchemy import select

from database import SessionLocal
from db_models import ApartmentDB


def seed_apartments():
    db = SessionLocal()

    try:
        existing = db.execute(
            select(ApartmentDB)
        ).scalars().first()

        if existing:
            print("Apartments already seeded.")
            return

        apartments = [
            ApartmentDB(
                id=1204,
                name="Sea View 1204",
                capacity=3,
                base_price=350,
            ),
            ApartmentDB(
                id=804,
                name="Lagoon View 804",
                capacity=2,
                base_price=250,
            ),
        ]

        db.add_all(apartments)
        db.commit()

        print("Apartments seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_apartments()