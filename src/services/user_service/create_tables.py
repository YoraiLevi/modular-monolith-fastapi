from .database import engine
from .models import UserTableObject


def create_tables():
    UserTableObject.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
