from sqlmodel import SQLModel


def create_tables(engine):
    SQLModel.metadata.create_all(engine)
