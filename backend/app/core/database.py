from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    connect_args = {"check_same_thread": False}
    pool_kwargs = {}
else:
    connect_args = {
        "ssl": "require",
        # ── PgBouncer (Neon pooler) fix ──
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        "server_settings": {"application_name": "jobpilot"},
    }
    pool_kwargs = {
        "pool_size": 5,          # Neon ফ্রি টিয়ারে বেশি দরকার নেই
        "max_overflow": 5,
        "pool_recycle": 300,     # ৫ মিনিট — Neon autosuspend-এর আগেই রিসাইকেল
        "pool_timeout": 30,
    }

engine = create_async_engine(
    DATABASE_URL,
    echo=(settings.APP_ENV == "development"),
    future=True,
    pool_pre_ping=True,          # ← মৃত কানেকশন ধরার জন্য, অপরিহার্য
    connect_args=connect_args,
    **pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise