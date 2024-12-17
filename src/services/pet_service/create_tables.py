from .database import engine
from .models import PetTableObject


def create_tables():
    PetTableObject.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
