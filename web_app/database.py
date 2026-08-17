from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker, Session

engine: Engine | None = None
db_session: scoped_session[Session] | None = None
Base = declarative_base()


def init_engine(database_uri: str) -> tuple[Engine, scoped_session[Session]]:
    global engine, db_session
    engine = create_engine(database_uri, future=True)
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    )
    Base.query = db_session.query_property()
    return engine, db_session


def create_all_tables() -> None:
    from . import models  # noqa: F401

    assert engine is not None, "init_engine() must be called before create_all_tables()"
    # Use if_not_exists=True to allow idempotent table creation
    Base.metadata.create_all(bind=engine, checkfirst=True)


def get_session() -> scoped_session[Session]:
    assert db_session is not None, "init_engine() must be called before get_session()"
    return db_session
