import logging
from src.modules.org.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.domain.value_objects.id import ID
from src.modules.auth.exceptions import InvalidToken, UserNotFoundError
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.exceptions import OrgDuplicateError
from src.modules.org.infrastructure.persistence.models import OrgMemberModel

logger = logging.getLogger(__name__)


class AddOrgService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, name: str):
        logger.info("Creating new organization: name=%s", name)

        payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        user = await self.uow.users.get_by_id(ID(payload["sub"]))

        current_version = await self.token_repo.get_user_version(user_id=user.id)
        if payload["ver"] != current_version:
            raise InvalidToken("Access token is expired")

        is_blocked = await self.token_repo.is_token_blocked(ID(payload["jti"]))
        if is_blocked:
            raise InvalidToken("Access token is revoked")

        org_name = Name(name)
        if await self.uow.orgs.exists_by_name(org_name):
            raise OrgDuplicateError(f"Organization with name '{name}' already exists")

        org = OrgFactory.create(name=name)
        await self.uow.orgs.add(org)
        await self.uow.commit()

        org_db = await self.uow.orgs.get_by_name(org_name)
        org_member = OrgMemberModel(
            user_id=user.id.value,
            organization_id=org_db.id.value,
            role="owner",
        )
        self.uow._session.add(org_member)
        await self.uow.commit()

        logger.info("Organization created successfully: org_id=%s", org.id.value)
        return org
