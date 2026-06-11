import logging
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, delete
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    TimeoutError,
    SQLAlchemyError,
)

from src.modules.card.domain.ports.card_repo_interface import ICardRepository
from src.modules.card.domain.entities.card import CardEntity
from src.modules.card.domain.entities.label import LabelEntity
from src.modules.card.domain.entities.checklist import CheckListEntity
from src.modules.auth.domain.entities.user import UserEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.description import Description
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.card.domain.value_objects.datetime import DateTime
from src.modules.card.domain.value_objects.is_checked import IsChecked

from src.modules.card.infrastructure.persistence.models import (
    CardModel,
    CardAssigneesModel,
    LabelsModel,
    CardLabels,
    CheckListsModel,
)
from src.modules.card.domain.factories.card_factory import CardFactory
from src.modules.card.domain.factories.label_factory import LabelFactory
from src.modules.card.domain.factories.checklist_factory import CheckListFactory
from src.modules.auth.infrastructure.persistence.models import UserModel

from src.modules.core.exceptions import (
    CardNotFoundError,
    LabelNotFoundError,
    CheckListNotFoundError,
    NoChangesError,
    DatabaseOperationError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
)

logger = logging.getLogger(__name__)


class SQLAL_CardRepository(ICardRepository):
    """SQLAlchemy Repository for Card entities and related sub-entities."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ==============================
    # Card operations
    # ==============================

    async def add(self, card: CardEntity) -> None:
        logger.info(
            "Adding card: public_id=%s, title=%s, column_id=%s",
            card.id.value,
            card.title.value,
            card.column_id.value,
        )

        due_date_obj = datetime.fromisoformat(card.due_date.value)

        card_model = CardModel(
            public_id=card.id.value,
            column_id=card.column_id.value,
            title=card.title.value,
            description=card.description.value,
            priority=card.priority.value,
            due_date=due_date_obj,
            created_by_user_id=card.created_by_user_id.value,
        )

        self._session.add(card_model)
        await self._execute_db_operation("add_card", self._session.flush)

        logger.info("Card added successfully: public_id=%s", card.id.value)

    async def update(
        self,
        card_id: ID,
        new_column_id: ID | None = None,
        new_title: Title | None = None,
        new_description: Description | None = None,
        new_priority: Priority | None = None,
        new_due_date: DateTime | None = None,
    ) -> None:
        logger.info(
            "Updating card: public_id=%s, new_column_id=%s, new_title=%s, new_description=%s, new_priority=%s, new_due_date=%s",
            card_id.value,
            new_column_id.value if new_column_id else None,
            new_title.value if new_title else None,
            new_description.value if new_description else None,
            new_priority.value if new_priority else None,
            new_due_date.value if new_due_date else None,
        )

        update_data = {}
        if new_column_id is not None:
            update_data["column_id"] = new_column_id.value
        if new_title is not None:
            update_data["title"] = new_title.value
        if new_description is not None:
            update_data["description"] = new_description.value
        if new_priority is not None:
            update_data["priority"] = new_priority.value
        if new_due_date is not None:
            update_data["due_date"] = datetime.fromisoformat(new_due_date.value)

        if not update_data:
            logger.debug("No changes provided")
            raise NoChangesError("No non-null changes provided.")

        result = await self._execute_db_operation(
            "update_card",
            self._session.execute,
            update(CardModel)
            .where(CardModel.public_id == card_id.value)
            .values(**update_data)
            .returning(CardModel.public_id),
        )

        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            logger.debug("Card not found: public_id=%s", card_id.value)
            raise CardNotFoundError(f"Card with id {card_id.value!r} not found")

        await self._execute_db_operation("update_card", self._session.flush)

        logger.info("Card updated successfully: public_id=%s", card_id.value)

    async def delete(self, card_id: ID) -> None:
        logger.info("Deleting card: public_id=%s", card_id.value)

        result = await self._execute_db_operation(
            "delete_card",
            self._session.execute,
            delete(CardModel).where(CardModel.public_id == card_id.value),
        )

        if result.rowcount == 0:
            logger.debug("Card not found: public_id=%s", card_id.value)
            raise CardNotFoundError(f"Card with id {card_id.value!r} not found")

        await self._execute_db_operation("delete_card", self._session.flush)

        logger.info("Card deleted successfully: public_id=%s", card_id.value)

    async def get_by_id(self, card_id: ID) -> CardEntity:
        logger.info("Getting card by id: public_id=%s", card_id.value)

        result = await self._execute_db_operation(
            "get_card_by_id",
            self._session.execute,
            select(CardModel).where(CardModel.public_id == card_id.value),
        )
        card_row = result.scalar_one_or_none()

        if card_row:
            logger.info("Card found: public_id=%s", card_id.value)
            return self._to_card_entity(card_row)

        logger.debug("Card not found: public_id=%s", card_id.value)
        raise CardNotFoundError(f"Card with id {card_id.value!r} not found")

    async def get_by_column_id(self, column_id: ID) -> List[CardEntity]:
        logger.info("Getting cards for column: column_id=%s", column_id.value)

        result = await self._execute_db_operation(
            "get_cards_by_column_id",
            self._session.execute,
            select(CardModel).where(CardModel.column_id == column_id.value),
        )

        cards = []
        for row in result.scalars():
            cards.append(self._to_card_entity(row))

        logger.info(
            "Found %d cards for column: column_id=%s", len(cards), column_id.value
        )
        return cards

    # ==============================
    # Assignee operations
    # ==============================

    async def add_assignee(self, card_id: ID, assignee: UserEntity) -> None:
        logger.info(
            "Adding assignee to card: card_id=%s, user_id=%s",
            card_id.value,
            assignee.id.value,
        )

        card_exists = await self._card_exists(card_id)
        if not card_exists:
            raise CardNotFoundError(f"Card with id {card_id.value!r} not found")

        # Check if already assigned
        existing = await self._session.execute(
            select(CardAssigneesModel).where(
                CardAssigneesModel.card_id == card_id.value,
                CardAssigneesModel.user_id == assignee.id.value,
            )
        )
        if existing.first():
            logger.debug("Assignee already added to card")
            return

        assignee_model = CardAssigneesModel(
            user_id=assignee.id.value,
            card_id=card_id.value,
        )
        self._session.add(assignee_model)
        await self._execute_db_operation("add_assignee", self._session.flush)

        logger.info(
            "Assignee added successfully: card_id=%s, user_id=%s",
            card_id.value,
            assignee.id.value,
        )

    async def del_assignee(self, card_id: ID, assignee_id: ID) -> None:
        logger.info(
            "Removing assignee from card: card_id=%s, user_id=%s",
            card_id.value,
            assignee_id.value,
        )

        result = await self._execute_db_operation(
            "remove_assignee",
            self._session.execute,
            delete(CardAssigneesModel).where(
                CardAssigneesModel.card_id == card_id.value,
                CardAssigneesModel.user_id == assignee_id.value,
            ),
        )

        if result.rowcount == 0:
            logger.debug(
                "Assignee not found on card: card_id=%s, user_id=%s",
                card_id.value,
                assignee_id.value,
            )
        else:
            await self._execute_db_operation("remove_assignee", self._session.flush)
            logger.info(
                "Assignee removed successfully: card_id=%s, user_id=%s",
                card_id.value,
                assignee_id.value,
            )

    async def get_card_assignee_IDs(self, card_id: ID) -> List[ID]:
        logger.info("Getting assignee IDs for card: card_id=%s", card_id.value)

        result = await self._execute_db_operation(
            "get_card_assignee_ids",
            self._session.execute,
            select(CardAssigneesModel.user_id).where(
                CardAssigneesModel.card_id == card_id.value
            ),
        )

        ids = [ID(row) for row in result.scalars()]
        logger.info("Found %d assignees for card: card_id=%s", len(ids), card_id.value)
        return ids

    # ==============================
    # Label operations
    # ==============================

    async def add_label(self, card_id: ID, label: LabelEntity) -> None:
        logger.info(
            "Adding label to card: card_id=%s, label_name=%s",
            card_id.value,
            label.name.value,
        )

        card_exists = await self._card_exists(card_id)
        if not card_exists:
            raise CardNotFoundError(f"Card with id {card_id.value!r} not found")

        # Find or create label by name
        label_row = await self._get_label_by_name(label.name.value)
        if label_row is None:
            # Create new label with generated public_id
            label_public_id = ID().value
            label_model = LabelsModel(
                public_id=label_public_id,
                name=label.name.value,
            )
            self._session.add(label_model)
            await self._execute_db_operation("add_label", self._session.flush)
            label_row = label_model

        # Check if association already exists
        existing = await self._session.execute(
            select(CardLabels).where(
                CardLabels.label_id == label_row.public_id,
                CardLabels.card_id == card_id.value,
            )
        )
        if existing.first():
            logger.debug("Label already associated with card")
            return

        card_label = CardLabels(
            label_id=label_row.public_id,
            card_id=card_id.value,
        )
        self._session.add(card_label)
        await self._execute_db_operation("add_card_label", self._session.flush)

        logger.info(
            "Label added to card successfully: card_id=%s, label_name=%s",
            card_id.value,
            label.name.value,
        )

    async def del_label(self, card_id: ID, label: LabelEntity) -> None:
        logger.info(
            "Removing label from card: card_id=%s, label_name=%s",
            card_id.value,
            label.name.value,
        )

        label_row = await self._get_label_by_name(label.name.value)
        if label_row is None:
            raise LabelNotFoundError(f"Label with name {label.name.value!r} not found")

        result = await self._execute_db_operation(
            "remove_card_label",
            self._session.execute,
            delete(CardLabels).where(
                CardLabels.label_id == label_row.public_id,
                CardLabels.card_id == card_id.value,
            ),
        )

        if result.rowcount == 0:
            logger.debug(
                "Label not associated with card: card_id=%s, label_name=%s",
                card_id.value,
                label.name.value,
            )
            raise LabelNotFoundError(
                f"Label {label.name.value!r} not attached to card {card_id.value}"
            )

        await self._execute_db_operation("remove_card_label", self._session.flush)

        logger.info(
            "Label removed from card successfully: card_id=%s, label_name=%s",
            card_id.value,
            label.name.value,
        )

    async def get_card_labels(self, card_id: ID) -> List[LabelEntity]:
        logger.info("Getting labels for card: card_id=%s", card_id.value)

        result = await self._execute_db_operation(
            "get_card_labels",
            self._session.execute,
            select(LabelsModel)
            .join(CardLabels, LabelsModel.public_id == CardLabels.label_id)
            .where(CardLabels.card_id == card_id.value),
        )

        labels = []
        for row in result.scalars():
            labels.append(LabelFactory.create(id=row.public_id, name=row.name))

        logger.info("Found %d labels for card: card_id=%s", len(labels), card_id.value)
        return labels

    # ==============================
    # Checklist operations
    # ==============================

    async def add_checklist(self, card_id: ID, checklist: CheckListEntity) -> None:
        logger.info(
            "Adding checklist to card: card_id=%s, title=%s",
            card_id.value,
            checklist.title.value,
        )

        card_exists = await self._card_exists(card_id)
        if not card_exists:
            raise CardNotFoundError(f"Card with id {card_id.value!r} not found")

        checklist_model = CheckListsModel(
            public_id=checklist.id.value,
            title=checklist.title.value,
            card_id=card_id.value,
            is_checked=checklist.is_checked.value,
        )

        self._session.add(checklist_model)
        await self._execute_db_operation("add_checklist", self._session.flush)

        logger.info("Checklist added successfully: public_id=%s", checklist.id.value)

    async def update_checklist(
        self,
        checklist_id: ID,
        new_title: Title | None = None,
        new_is_checked: IsChecked | None = None,
    ) -> None:
        logger.info(
            "Updating checklist: public_id=%s, new_title=%s, new_is_checked=%s",
            checklist_id.value,
            new_title.value if new_title else None,
            new_is_checked.value if new_is_checked else None,
        )

        update_data = {}
        if new_title is not None:
            update_data["title"] = new_title.value
        if new_is_checked is not None:
            update_data["is_checked"] = new_is_checked.value

        if not update_data:
            logger.debug("No changes provided")
            raise NoChangesError("No non-null changes provided.")

        result = await self._execute_db_operation(
            "update_checklist",
            self._session.execute,
            update(CheckListsModel)
            .where(CheckListsModel.public_id == checklist_id.value)
            .values(**update_data)
            .returning(CheckListsModel.public_id),
        )

        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            logger.debug("Checklist not found: public_id=%s", checklist_id.value)
            raise CheckListNotFoundError(
                f"Checklist with id {checklist_id.value!r} not found"
            )

        await self._execute_db_operation("update_checklist", self._session.flush)

        logger.info("Checklist updated successfully: public_id=%s", checklist_id.value)

    async def del_checklist(self, checklist_id: ID) -> None:
        logger.info("Deleting checklist: public_id=%s", checklist_id.value)

        result = await self._execute_db_operation(
            "delete_checklist",
            self._session.execute,
            delete(CheckListsModel).where(
                CheckListsModel.public_id == checklist_id.value
            ),
        )

        if result.rowcount == 0:
            logger.debug("Checklist not found: public_id=%s", checklist_id.value)
            raise CheckListNotFoundError(
                f"Checklist with id {checklist_id.value!r} not found"
            )

        await self._execute_db_operation("delete_checklist", self._session.flush)

        logger.info("Checklist deleted successfully: public_id=%s", checklist_id.value)

    async def get_checklist_by_id(self, checklist_id: ID) -> CheckListEntity:
        logger.info("Getting checklist by id: public_id=%s", checklist_id.value)

        result = await self._execute_db_operation(
            "get_checklist_by_id",
            self._session.execute,
            select(CheckListsModel).where(
                CheckListsModel.public_id == checklist_id.value
            ),
        )
        checklist_row = result.scalar_one_or_none()

        if checklist_row:
            logger.info("Checklist found: public_id=%s", checklist_id.value)
            return CheckListFactory.create(
                id=checklist_row.public_id,
                card_id=checklist_row.card_id,
                title=checklist_row.title,
                is_checked=checklist_row.is_checked,
            )

        logger.debug("Checklist not found: public_id=%s", checklist_id.value)
        raise CheckListNotFoundError(
            f"Checklist with id {checklist_id.value!r} not found"
        )

    async def get_card_checklists(self, card_id: ID) -> List[CheckListEntity]:
        logger.info("Getting checklists for card: card_id=%s", card_id.value)

        result = await self._execute_db_operation(
            "get_card_checklists",
            self._session.execute,
            select(CheckListsModel).where(CheckListsModel.card_id == card_id.value),
        )

        checklists = []
        for row in result.scalars():
            checklists.append(
                CheckListFactory.create(
                    id=row.public_id,
                    card_id=row.card_id,
                    title=row.title,
                    is_checked=row.is_checked,
                )
            )

        logger.info(
            "Found %d checklists for card: card_id=%s", len(checklists), card_id.value
        )
        return checklists

    # ==============================
    # Helper methods
    # ==============================

    async def _card_exists(self, card_id: ID) -> bool:
        result = await self._session.execute(
            select(CardModel).where(CardModel.public_id == card_id.value)
        )
        return result.first() is not None

    async def _get_label_by_name(self, name: str):
        result = await self._session.execute(
            select(LabelsModel).where(LabelsModel.name == name)
        )
        return result.scalar_one_or_none()

    def _to_card_entity(self, card_model: CardModel) -> CardEntity:
        return CardFactory.create(
            id=card_model.public_id,
            column_id=card_model.column_id,
            title=card_model.title,
            description=card_model.description,
            priority=card_model.priority,
            due_date=card_model.due_date.isoformat(),
            created_by_user_id=card_model.created_by_user_id,
            created_at=card_model.created_at.isoformat(),
        )

    async def _execute_db_operation(self, operation: str, coro, *args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except IntegrityError as e:
            logger.exception(f"Database integrity error during {operation}")
            raise DatabaseOperationError(f"Database integrity error: {e}") from e
        except OperationalError as e:
            logger.exception(f"Database connection error during {operation}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        except TimeoutError as e:
            logger.exception(f"Database timeout during {operation}")
            raise DatabaseTimeoutError(f"Database operation timed out: {e}") from e
        except SQLAlchemyError as e:
            logger.exception(f"Database error during {operation}")
            raise DatabaseOperationError(f"Database operation failed: {e}") from e
