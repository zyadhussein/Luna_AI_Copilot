from database import Base, engine
import db_models


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Tables created.")