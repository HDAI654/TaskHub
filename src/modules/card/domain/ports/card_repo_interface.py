from abc import ABC, abstractmethod
from typing import List
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


class ICardRepository(ABC):
    """Repository interface for card entities."""

    # ===== Card =====
    @abstractmethod
    async def add(self, card: CardEntity) -> None:
        """Create a new card in the database."""
        pass

    @abstractmethod
    async def update(
        self,
        card_id: ID,
        new_column_id: ID | None = None,
        new_title: Title | None = None,
        new_description: Description | None = None,
        new_priority: Priority | None = None,
        new_due_date: DateTime | None = None,
    ) -> None:
        """Update an existing card."""
        pass

    @abstractmethod
    async def delete(self, card_id: ID) -> None:
        """Delete a card by ID."""
        pass

    @abstractmethod
    async def get_by_id(self, card_id: ID) -> CardEntity:
        """Get a card by ID."""
        pass

    @abstractmethod
    async def get_by_column_id(self, column_id: ID) -> List[CardEntity]:
        """Get all cards belonging to a column."""
        pass

    # ===== Assignee =====
    @abstractmethod
    async def add_assignee(self, card_id: ID, assignee: UserEntity) -> None:
        """add an assignee a card."""
        pass

    @abstractmethod
    async def del_assignee(self, card_id: ID, assignee_id: ID) -> None:
        """remove an assignee from card."""
        pass

    @abstractmethod
    async def get_card_assignee_IDs(self, card_id: ID) -> List[ID]:
        """Get IDs of all assignees belonging to a card."""
        pass

    # ===== Label =====
    @abstractmethod
    async def add_label(self, card_id: ID, label: LabelEntity) -> None:
        """Add a label to card (create label if it did not exist)."""
        pass

    @abstractmethod
    async def del_label(self, card_id: ID, label: LabelEntity) -> None:
        """remove a label from card."""
        pass

    @abstractmethod
    async def get_card_labels(self, card_id: ID) -> List[LabelEntity]:
        """Get all labels belonging to a card."""
        pass

    # ===== CheckList =====
    @abstractmethod
    async def add_checklist(self, card_id: ID, checklist: CheckListEntity) -> None:
        """Add a checklist to card."""
        pass

    @abstractmethod
    async def update_checklist(
        self,
        checklist_id: ID,
        new_title: Title | None = None,
        new_is_checked: IsChecked | None = None,
    ) -> None:
        """Update an existing checklist."""
        pass

    @abstractmethod
    async def del_checklist(self, checklist_id: ID) -> None:
        """remove a checklist."""
        pass

    @abstractmethod
    async def get_checklist_by_id(self, checklist_id: ID) -> CheckListEntity:
        """Get a checklist by ID."""
        pass

    @abstractmethod
    async def get_card_checklists(self, card_id: ID) -> List[CheckListEntity]:
        """Get all checklists belonging to a card."""
        pass
