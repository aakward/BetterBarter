from data.db import Base, engine
import data.models  # ensure all models are registered with Base

def init():
    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

if __name__ == "__main__":
    init()
