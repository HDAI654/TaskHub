import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.exceptions import InvalidToken, UserNotFoundError
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.domain.value_objects.role import Role
from src.modules.org.exceptions import OrgDuplicateError, PermissionDenied

logger = logging.getLogger(__name__)


class CreateOrgService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, name: str) -> OrgEntity:
        logger.info("Creating organization: name=%s", name)

        # Decode and validate access token
        try:
            payload = self.jwt_decoder.decode_and_validate(access_token, "access")
        except InvalidToken as e:
            logger.warning("access_token was invalid: %s", str(e))
            raise

        # Check user exists
        try:
            user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning("User not found: user_id=%s", payload["sub"])
            raise

        # Check token version
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        if payload["ver"] != current_version:
            raise InvalidToken("Access token is expired")

        # Check if organization name already exists
        org_name = Name(name)
        if await self.uow.orgs.exists_by_name(org_name):
            logger.warning("Organization already exists: name=%s", name)
            raise OrgDuplicateError(f"Organization with name '{name}' already exists")

        # Create organization
        org = OrgFactory.create(name=name)
        await self.uow.orgs.add(org)
        await self.uow.commit()

        # Add creator as owner
        await self.uow.orgs.add_member(org.id, user.id, Role("owner"))
        await self.uow.commit()

        logger.info("Organization created successfully: org_id=%s, owner=%s", org.id.value, user.id.value)
        return org