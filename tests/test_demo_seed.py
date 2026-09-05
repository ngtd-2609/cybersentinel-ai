import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from cybersentinel_ai.auth.service import authenticate_user
from cybersentinel_ai.core.config import Settings
from cybersentinel_ai.db.database import Base, build_engine
from cybersentinel_ai.db.models import DetectionEvent, Incident, IncidentTimeline, User
from cybersentinel_ai.demo.seed import seed_demo_data


@pytest.fixture
def database_factory(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'portfolio-demo.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield factory
    engine.dispose()


def demo_settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="portfolio",
        demo_seed_enabled=True,
        demo_user_password="PortfolioDemo123!",
    )


def test_demo_seed_is_idempotent_and_uses_restricted_account(database_factory):
    settings = demo_settings()
    with database_factory() as database:
        first = seed_demo_data(database, settings)
        second = seed_demo_data(database, settings)

        user = database.scalar(select(User).where(User.email == settings.demo_user_email))
        assert user is not None
        assert user.role == "ANALYST"
        assert first.events == second.events == 8
        assert database.scalar(select(func.count()).select_from(DetectionEvent)) == 8
        assert database.scalar(select(func.count()).select_from(Incident)) == 3
        assert database.scalar(select(func.count()).select_from(IncidentTimeline)) == 6


def test_demo_reset_restores_incident_and_password(database_factory):
    settings = demo_settings()
    with database_factory() as database:
        seed_demo_data(database, settings)
        incident = database.scalar(
            select(Incident).where(Incident.title == "[DEMO] Ransomware containment")
        )
        assert incident is not None
        incident.status = "RESOLVED"
        database.commit()

        result = seed_demo_data(database, settings, reset=True)
        database.refresh(incident)

        assert result.reset is True
        assert incident.status == "IN_PROGRESS"
        assert authenticate_user(
            database,
            settings.demo_user_email,
            "PortfolioDemo123!",
        ) is not None


def test_demo_seed_refuses_to_replace_admin(database_factory):
    settings = demo_settings()
    with database_factory() as database:
        database.add(
            User(
                email=settings.demo_user_email,
                username=settings.demo_user_username,
                hashed_password="not-used",
                role="ADMIN",
            )
        )
        database.commit()

        with pytest.raises(ValueError, match="administrator"):
            seed_demo_data(database, settings)
