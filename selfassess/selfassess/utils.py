import os


def get_database_url(db=None, envvar="DATABASE_URL"):
    if db is None:
        db = os.getenv(envvar)
        if db is None:
            raise RuntimeError(envvar + " not set")
    return db


def get_session(db=None):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    engine = create_engine(get_database_url(db), future=True)
    session = sessionmaker(bind=engine, future=True)
    return scoped_session(session)


def get_async_session(db=None):
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker

    url = get_database_url(db, "ASYNC_DATABASE_URL")
    engine = create_async_engine(url, future=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )
    return async_session
