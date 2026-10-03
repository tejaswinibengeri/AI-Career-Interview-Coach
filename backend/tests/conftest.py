"""
Shared test fixtures for backend tests.
"""

from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.main import app
from app.models.user import Profile, User

# Test async SQLite in-memory database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create fresh database tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated test session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with database override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Create and return a sample registered user."""
    user = User(
        email="testuser@example.com",
        name="Alex Mercer",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(
        user_id=user.id,
        education="MIT",
        degree="B.S. Computer Science",
        graduation_year=2024,
        experience="2 years",
        current_role="Junior Software Engineer",
        target_role="Senior Full Stack Engineer",
        skills=["Python", "FastAPI", "React", "TypeScript"],
        preferred_location="San Francisco, CA",
        work_preference="Remote",
        career_goal="Lead high-impact full stack architecture projects",
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(sample_user: User) -> dict[str, str]:
    """Generate auth headers containing a valid JWT for sample_user."""
    token = create_access_token({"sub": str(sample_user.id), "email": sample_user.email})
    return {"Authorization": f"Bearer {token}"}
