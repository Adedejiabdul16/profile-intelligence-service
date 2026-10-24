import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase



DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    hostname = os.getenv("DATABASE_HOSTNAME")
    port = os.getenv("DATABASE_PORT", "5432")
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    database_name = os.getenv("DATABASE_NAME", "neondb")

    if hostname and username and password:
        from sqlalchemy.engine import URL

        DATABASE_URL = URL.create(
            drivername="postgresql+asyncpg",
            username=username,
            password=password,
            host=hostname,
            port=int(port),
            database=database_name,
        )

    else:
        DATABASE_URL = "sqlite+aiosqlite:///./profiles.db"

if isinstance(DATABASE_URL, str):
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

connect_args = (
    {"ssl": "require"}
    if str(DATABASE_URL).startswith("postgresql+asyncpg://")
    else {}
)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
