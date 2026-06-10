import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.entities.user import UserEntity
from src.modules.auth.domain.value_objects.id import ID

logger = logging.getLogger(__name__)


class GetUserByIDService:
    def __init__(
        self,
        uow: IUnitOfWork,
    ):
        self.uow = uow

    async def execute(self, user_id: str) -> UserEntity:
        logger.info("GetUserByIDService started: user_id=%s", user_id)

        # Retrieve user by id
        user = await self.uow.users.get_by_id(id=ID(user_id))

        logger.info("GetUserByIDService finished successfully: user_id=%s", user_id)

        return user
