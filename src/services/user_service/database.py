from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, Session
from .consants import service_name
from common.config_loader import load_config, config_path

config = load_config(config_path)
DATABASE_URL = config["sub_routes"][service_name]["database_url"]
# Create SQLModel engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed only for SQLite
)


# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
