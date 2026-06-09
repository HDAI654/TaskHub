import pytest
from sqlalchemy import select, exists, text
from src.modules.core.database import get_async_session, engine
from src.modules.org.infrastructure.persistence.models import OrgModel, OrgMemberModel
from src.modules.core.database import Base
from src.modules.auth.infrastructure.persistence.models import UserModel
from src.modules.org.infrastructure.persistence.sqlal_org_repo import (
    SQLAL_OrgRepository,
)
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.role import Role
from src.modules.org.exceptions import (
    OrgNotFoundError,
    NoChangesError,
    MemberDuplicateError,
    MemberNotFoundError,
)
from src.modules.auth.exceptions import UserNotFoundError


class TestOrgRepo:
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
    async def repo(self, db_session):
        return SQLAL_OrgRepository(db_session)

    @pytest.fixture
    async def org_seed(self, db_session):
        org = OrgModel(
            public_id=ID().value,
            name="Test Organization",
        )
        db_session.add(org)
        await db_session.flush()
        return org

    @pytest.fixture
    async def second_org_seed(self, db_session):
        org = OrgModel(
            public_id=ID().value,
            name="Another Organization",
        )
        db_session.add(org)
        await db_session.flush()
        return org

    @pytest.fixture
    async def user_seed(self, db_session):
        user = UserModel(
            public_id=ID().value,
            email="testuser@example.com",
            password="hashedpassword",
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.fixture
    async def second_user_seed(self, db_session):
        user = UserModel(
            public_id=ID().value,
            email="seconduser@example.com",
            password="hashedpassword2",
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.fixture
    async def org_member_seed(self, db_session, org_seed, user_seed):
        member = OrgMemberModel(
            user_id=user_seed.id,
            organization_id=org_seed.id,
            role="owner",
        )
        db_session.add(member)
        await db_session.flush()
        return member

    @pytest.fixture
    async def org_entity(self, org_seed):
        return OrgFactory.create(
            id=org_seed.public_id,
            name=org_seed.name,
            created_at=org_seed.created_at.isoformat(),
        )

    @pytest.fixture
    async def non_existent_org_id(self):
        return ID()

    async def test_add_successfully(self, repo, db_session):
        org_id = ID()
        org = OrgFactory.create(
            id=org_id.value,
            name="New Org",
        )

        await repo.add(org)

        result = await db_session.execute(
            select(OrgModel).where(OrgModel.public_id == org_id.value)
        )
        saved_org = result.scalar_one()

        assert saved_org.public_id == org_id.value
        assert saved_org.name == "New Org"

    async def test_get_by_id_successfully(self, repo, org_entity, org_seed):
        result = await repo.get_by_id(org_entity.id)

        assert result.id.value == org_seed.public_id
        assert result.name.value == org_seed.name

    async def test_get_by_id_not_found(self, repo, non_existent_org_id):
        with pytest.raises(OrgNotFoundError):
            await repo.get_by_id(non_existent_org_id)

    async def test_get_by_name_successfully(self, repo, org_entity, org_seed):
        result = await repo.get_by_name(org_entity.name)

        assert result.id.value == org_seed.public_id
        assert result.name.value == org_seed.name

    async def test_get_by_name_not_found(self, repo):
        with pytest.raises(OrgNotFoundError):
            await repo.get_by_name(Name("Nonexistent Org"))

    async def test_exists_by_id(self, repo, org_entity):
        assert await repo.exists_by_id(org_entity.id) is True
        assert await repo.exists_by_id(ID()) is False

    async def test_exists_by_name(self, repo, org_entity):
        assert await repo.exists_by_name(org_entity.name) is True
        assert await repo.exists_by_name(Name("Fake Name")) is False

    async def test_update_name_successfully(self, repo, db_session, org_entity):
        await repo.update(org_entity.id, new_name=Name("Updated Org Name"))

        result = await db_session.execute(
            select(OrgModel).where(OrgModel.public_id == org_entity.id.value)
        )
        updated_org = result.scalar_one()

        assert updated_org.name == "Updated Org Name"

    async def test_update_raises_when_no_fields_provided(self, repo, org_entity):
        with pytest.raises(NoChangesError):
            await repo.update(org_entity.id)

    async def test_update_raises_when_org_not_found(self, repo, non_existent_org_id):
        with pytest.raises(OrgNotFoundError):
            await repo.update(non_existent_org_id, new_name=Name("New Name"))

    async def test_delete_successfully(self, repo, db_session, org_entity):
        await repo.delete(org_entity.id)

        result = await db_session.execute(
            select(exists().where(OrgModel.public_id == org_entity.id.value))
        )
        assert result.scalar() is False

    async def test_delete_raises_when_org_not_found(self, repo, non_existent_org_id):
        with pytest.raises(OrgNotFoundError):
            await repo.delete(non_existent_org_id)

    async def test_get_members_no_filter(
        self, repo, org_entity, org_seed, user_seed, second_user_seed, db_session
    ):
        member1 = OrgMemberModel(
            user_id=user_seed.public_id,
            organization_id=org_seed.public_id,
            role="owner",
        )
        member2 = OrgMemberModel(
            user_id=second_user_seed.public_id,
            organization_id=org_seed.public_id,
            role="member",
        )
        db_session.add_all([member1, member2])
        await db_session.flush()

        members = await repo.get_members(org_entity.id)

        assert len(members) == 2
        assert members[0]["user_id"] == user_seed.public_id
        assert members[1]["user_id"] == second_user_seed.public_id

    async def test_get_members_with_role_filter(
        self, repo, org_entity, org_seed, user_seed, second_user_seed, db_session
    ):
        member1 = OrgMemberModel(
            user_id=user_seed.public_id,
            organization_id=org_seed.public_id,
            role="owner",
        )
        member2 = OrgMemberModel(
            user_id=second_user_seed.public_id,
            organization_id=org_seed.public_id,
            role="member",
        )
        db_session.add_all([member1, member2])
        await db_session.flush()

        owners = await repo.get_members(org_entity.id, role=Role("owner"))
        members = await repo.get_members(org_entity.id, role=Role("member"))

        assert len(owners) == 1
        assert owners[0]["user_id"] == user_seed.public_id
        assert owners[0]["role"] == "owner"

        assert len(members) == 1
        assert members[0]["user_id"] == second_user_seed.public_id
        assert members[0]["role"] == "member"

    async def test_get_members_returns_empty_list_for_no_members(
        self, repo, org_entity
    ):
        members = await repo.get_members(org_entity.id)

        assert members == []

    async def test_add_member_successfully(self, repo, org_entity, user_seed):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("member"))

        role = await repo.get_user_role(org_entity.id, ID(user_seed.public_id))
        assert role is not None
        assert role.value == "member"

        # Verify member appears in get_members
        members = await repo.get_members(org_entity.id)
        assert len(members) == 1
        assert members[0]["user_id"] == user_seed.public_id
        assert members[0]["role"] == "member"

    async def test_add_member_already_exists(self, repo, org_entity, user_seed):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("member"))
        with pytest.raises(MemberDuplicateError):
            await repo.add_member(
                org_entity.id, ID(user_seed.public_id), Role("member")
            )

    async def test_add_member_org_not_found(self, repo, non_existent_org_id, user_seed):
        with pytest.raises(OrgNotFoundError):
            await repo.add_member(
                non_existent_org_id, ID(user_seed.public_id), Role("member")
            )

    async def test_add_member_user_not_found(self, repo, org_entity):
        with pytest.raises(UserNotFoundError):
            await repo.add_member(org_entity.id, ID(), Role("member"))

    async def test_remove_member_successfully(self, repo, org_entity, user_seed):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("member"))

        await repo.remove_member(org_entity.id, ID(user_seed.public_id))

        role = await repo.get_user_role(org_entity.id, ID(user_seed.public_id))
        assert role is None

        # Verify member is removed from get_members
        members = await repo.get_members(org_entity.id)
        assert len(members) == 0

    async def test_remove_member_not_found(self, repo, org_entity, user_seed):
        with pytest.raises(MemberNotFoundError):
            await repo.remove_member(org_entity.id, ID(user_seed.public_id))

    async def test_remove_member_org_not_found(self, repo, user_seed):
        with pytest.raises(MemberNotFoundError):
            await repo.remove_member(ID(), ID(user_seed.public_id))

    async def test_get_user_role_returns_none_for_non_member(
        self, repo, org_entity, user_seed
    ):
        role = await repo.get_user_role(org_entity.id, ID(user_seed.public_id))
        assert role is None

    async def test_get_user_role_returns_role_for_member(
        self, repo, org_entity, user_seed
    ):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("member"))
        role = await repo.get_user_role(org_entity.id, ID(user_seed.public_id))
        assert role is not None
        assert role.value == "member"

    async def test_change_user_role_successfully(self, repo, org_entity, user_seed):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("member"))

        await repo.change_user_role(
            org_entity.id, ID(user_seed.public_id), Role("admin")
        )

        role = await repo.get_user_role(org_entity.id, ID(user_seed.public_id))
        assert role.value == "admin"

        # Verify role is updated in get_members
        members = await repo.get_members(org_entity.id)
        assert members[0]["role"] == "admin"

    async def test_change_user_role_member_not_found(self, repo, org_entity, user_seed):
        with pytest.raises(MemberNotFoundError):
            await repo.change_user_role(
                org_entity.id, ID(user_seed.public_id), Role("admin")
            )

    async def test_change_user_role_org_not_found(
        self, repo, non_existent_org_id, user_seed
    ):
        with pytest.raises(MemberNotFoundError):
            await repo.change_user_role(
                non_existent_org_id, ID(user_seed.public_id), Role("admin")
            )

    async def test_add_multiple_members_to_org(
        self, repo, org_entity, user_seed, second_user_seed
    ):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("owner"))
        await repo.add_member(
            org_entity.id, ID(second_user_seed.public_id), Role("member")
        )

        members = await repo.get_members(org_entity.id)
        assert len(members) == 2

        roles = {m["user_id"]: m["role"] for m in members}
        assert roles[user_seed.public_id] == "owner"
        assert roles[second_user_seed.public_id] == "member"

    async def test_same_user_in_different_orgs(
        self, repo, org_entity, second_org_seed, user_seed
    ):
        await repo.add_member(org_entity.id, ID(user_seed.public_id), Role("owner"))
        await repo.add_member(
            ID(second_org_seed.public_id), ID(user_seed.public_id), Role("member")
        )

        role1 = await repo.get_user_role(org_entity.id, ID(user_seed.public_id))
        role2 = await repo.get_user_role(
            ID(second_org_seed.public_id), ID(user_seed.public_id)
        )

        assert role1.value == "owner"
        assert role2.value == "member"
