import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

DATABASE_URL = getattr(settings, "DATABASE_URL", "sqlite+aiosqlite:///./test.db")

connect_args = {}

if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False
elif "postgresql+asyncpg" in DATABASE_URL:
    # URL-এ যদি sslmode চলে আসে, সেটা ক্লিন রাখা
    if "?sslmode=" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "?ssl=require")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()