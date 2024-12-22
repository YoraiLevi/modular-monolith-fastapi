from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy import Engine
from sqlmodel import Session, create_engine


def init_engine(DATABASE_URL: str):
    return create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # needed only for SQLite
    )


async def get_engine_instance() -> Engine:
    raise NotImplementedError("Engine is not implemented")


EngineDep = Annotated[Engine, Depends(get_engine_instance)]


async def get_session(engine: EngineDep) -> AsyncGenerator[Session, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
