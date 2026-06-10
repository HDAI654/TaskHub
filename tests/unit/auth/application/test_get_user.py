import pytest
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.auth.application.get_user import GetUserByIDService
from src.modules.core.database import Base
from src.modules.core.database import get_async_session, engine
from src.modules.auth.domain.factories.user_factory import UserFactory


class TestGetUserByIDService:
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture
    async def db_session(self):
        async for session in get_async_session():
            yield session
            await session.rollback()
            break

    @pytest.fixture
    async def uow(self, db_session) -> IUnitOfWork:
        return SQLAL_UnitOfWork(db_session)

    @pytest.fixture
    async def user(self, uow):
        user = UserFactory.create(
            email="mynewexampleemail@me.he",
            hashed_password="user_hashed_password",
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def service(self, uow):
        return GetUserByIDService(
            uow=uow,
        )

    async def test_get_user_success(self, user, service):
        found_user = await service.execute(user.id.value)

        assert found_user.id == user.id
        assert found_user.email == user.email
        assert found_user.hashed_password == user.hashed_password
