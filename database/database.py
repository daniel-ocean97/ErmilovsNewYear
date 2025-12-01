from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config.config import Config, load_config
from models import Base

config: Config = load_config()

# Создаем асинхронный движок для PostgreSQL
engine = create_async_engine(
    f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.database}",
    echo=True,  # Включаем логирование SQL запросов (можно отключить в проде)
)

# Создаем фабрику сессий
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Инициализация базы данных, создание таблиц"""
    async with engine.begin() as conn:
        # Создаем все таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Получение сессии для работы с базой данных"""
    async with async_session() as session:
        yield session