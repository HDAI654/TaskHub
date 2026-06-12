import logging
from typing import Dict, Any, Optional, Tuple, Callable
from src.modules.card.application.create_card import CreateCardService
from src.modules.card.application.edit_card import EditCardService
from src.modules.card.application.delete_card import DeleteCardService
from src.modules.card.application.get_card_by_id import GetCardByIdService
from src.modules.card.application.get_column_cards import GetColumnCardsService
from src.modules.card.application.add_assignee import AddAssigneeService
from src.modules.card.application.remove_assignee import RemoveAssigneeService
from src.modules.card.application.get_card_assignees import GetCardAssigneesService
from src.modules.card.application.add_label_to_card import AddLabelToCardService
from src.modules.card.application.remove_label_from_card import (
    RemoveLabelFromCardService,
)
from src.modules.card.application.get_card_labels import GetCardLabelsService
from src.modules.card.application.add_checklist import AddChecklistService
from src.modules.card.application.update_checklist import UpdateChecklistService
from src.modules.card.application.delete_checklist import DeleteChecklistService
from src.modules.card.application.get_checklist_by_id import GetChecklistByIdService
from src.modules.card.application.get_card_checklists import GetCardChecklistsService

logger = logging.getLogger(__name__)

ActionResult = Dict[str, Any]


def require_fields(message: Dict, required: list) -> None:
    """check required fields in the message."""
    missing = [f for f in required if f not in message]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


# ---------- Action Handlers ----------


async def create_card(
    create_card_service: CreateCardService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle create_card action."""
    require_fields(
        message, ["column_id", "title", "description", "priority", "due_date"]
    )
    card = await create_card_service.execute(
        access_token=access_token,
        column_id=message["column_id"],
        title=message["title"],
        description=message["description"],
        priority=message["priority"],
        due_date=message["due_date"],
    )
    result = {
        "card_id": card.id.value,
        "title": card.title.value,
        "column_id": card.column_id.value,
    }
    event = {"type": "card_created", "data": result}
    return result, event


async def edit_card(
    edit_card_service: EditCardService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle edit_card action."""
    require_fields(message, ["card_id"])
    await edit_card_service.execute(
        access_token=access_token,
        card_id=message["card_id"],
        new_column_id=message.get("new_column_id"),
        new_title=message.get("new_title"),
        new_description=message.get("new_description"),
        new_priority=message.get("new_priority"),
        new_due_date=message.get("new_due_date"),
    )
    updated_fields = [
        k
        for k in [
            "new_column_id",
            "new_title",
            "new_description",
            "new_priority",
            "new_due_date",
        ]
        if k in message
    ]
    result = {"card_id": message["card_id"], "updated_fields": updated_fields}
    event = {"type": "card_updated", "data": result}
    return result, event


async def delete_card(
    delete_card_service: DeleteCardService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle delete_card action."""
    require_fields(message, ["card_id"])
    await delete_card_service.execute(access_token, message["card_id"])
    result = {"card_id": message["card_id"]}
    event = {"type": "card_deleted", "data": result}
    return result, event


async def get_card_by_id(
    get_card_service: GetCardByIdService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle get_card_by_id action (no broadcast)."""
    require_fields(message, ["card_id"])
    card = await get_card_service.execute(access_token, message["card_id"])
    result = {
        "id": card.id.value,
        "column_id": card.column_id.value,
        "title": card.title.value,
        "description": card.description.value,
        "priority": card.priority.value,
        "due_date": card.due_date.value,
        "created_at": card.created_at.value,
        "created_by_user_id": card.created_by_user_id.value,
    }
    return result, None  # No event


async def get_column_cards(
    get_column_cards_service: GetColumnCardsService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle get_column_cards action (no broadcast)."""
    require_fields(message, ["column_id"])
    cards = await get_column_cards_service.execute(access_token, message["column_id"])
    result = [
        {
            "id": c.id.value,
            "title": c.title.value,
            "description": c.description.value,
            "priority": c.priority.value,
            "due_date": c.due_date.value,
        }
        for c in cards
    ]
    return result, None


async def add_assignee(
    add_assignee_service: AddAssigneeService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle add_assignee action."""
    require_fields(message, ["card_id", "assignee_id"])
    await add_assignee_service.execute(
        access_token, message["card_id"], message["assignee_id"]
    )
    result = {"card_id": message["card_id"], "assignee_id": message["assignee_id"]}
    event = {"type": "assignee_added", "data": result}
    return result, event


async def remove_assignee(
    remove_assignee_service: RemoveAssigneeService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle remove_assignee action."""
    require_fields(message, ["card_id", "assignee_id"])
    await remove_assignee_service.execute(
        access_token, message["card_id"], message["assignee_id"]
    )
    result = {"card_id": message["card_id"], "assignee_id": message["assignee_id"]}
    event = {"type": "assignee_removed", "data": result}
    return result, event


async def get_card_assignees(
    get_assignees_service: GetCardAssigneesService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle get_card_assignees action (no broadcast)."""
    require_fields(message, ["card_id"])
    assignees = await get_assignees_service.execute(access_token, message["card_id"])
    result = [{"user_id": u.id.value, "email": u.email.value} for u in assignees]
    return result, None


async def add_label(
    add_label_service: AddLabelToCardService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle add_label action."""
    require_fields(message, ["card_id", "label_name"])
    await add_label_service.execute(
        access_token, message["card_id"], message["label_name"]
    )
    result = {"card_id": message["card_id"], "label_name": message["label_name"]}
    event = {"type": "label_added", "data": result}
    return result, event


async def remove_label(
    remove_label_service: RemoveLabelFromCardService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle remove_label action."""
    require_fields(message, ["card_id", "label_name"])
    await remove_label_service.execute(
        access_token, message["card_id"], message["label_name"]
    )
    result = {"card_id": message["card_id"], "label_name": message["label_name"]}
    event = {"type": "label_removed", "data": result}
    return result, event


async def get_card_labels(
    get_labels_service: GetCardLabelsService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle get_card_labels action (no broadcast)."""
    require_fields(message, ["card_id"])
    labels = await get_labels_service.execute(access_token, message["card_id"])
    result = [{"id": l.id.value, "name": l.name.value} for l in labels]
    return result, None


async def add_checklist(
    add_checklist_service: AddChecklistService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle add_checklist action."""
    require_fields(message, ["card_id", "title"])
    await add_checklist_service.execute(
        access_token, message["card_id"], message["title"]
    )
    result = {"card_id": message["card_id"], "title": message["title"]}
    event = {"type": "checklist_added", "data": result}
    return result, event


async def update_checklist(
    update_checklist_service: UpdateChecklistService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle update_checklist action."""
    require_fields(message, ["checklist_id"])
    await update_checklist_service.execute(
        access_token,
        message["checklist_id"],
        new_title=message.get("new_title"),
        new_is_checked=message.get("new_is_checked"),
    )
    updated_fields = [k for k in ["new_title", "new_is_checked"] if k in message]
    result = {"checklist_id": message["checklist_id"], "updated_fields": updated_fields}
    event = {"type": "checklist_updated", "data": result}
    return result, event


async def delete_checklist(
    delete_checklist_service: DeleteChecklistService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle delete_checklist action."""
    require_fields(message, ["checklist_id"])
    await delete_checklist_service.execute(access_token, message["checklist_id"])
    result = {"checklist_id": message["checklist_id"]}
    event = {"type": "checklist_deleted", "data": result}
    return result, event


async def get_checklist_by_id(
    get_checklist_service: GetChecklistByIdService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle get_checklist_by_id action (no broadcast)."""
    require_fields(message, ["checklist_id"])
    cl = await get_checklist_service.execute(access_token, message["checklist_id"])
    result = {
        "id": cl.id.value,
        "card_id": cl.card_id.value,
        "title": cl.title.value,
        "is_checked": cl.is_checked.value,
    }
    return result, None


async def get_card_checklists(
    get_card_checklists_service: GetCardChecklistsService,
    message: Dict,
    access_token: str,
) -> Tuple[Optional[ActionResult], Optional[ActionResult]]:
    """Handle get_card_checklists action (no broadcast)."""
    require_fields(message, ["card_id"])
    cls = await get_card_checklists_service.execute(access_token, message["card_id"])
    result = [
        {
            "id": c.id.value,
            "title": c.title.value,
            "is_checked": c.is_checked.value,
        }
        for c in cls
    ]
    return result, None


# ---------- Mapping of action names to handler functions ----------
ACTION_MAP: dict[str, tuple[Callable, list[str]]] = {
    "create_card": (create_card, ["create_card_service"]),
    "edit_card": (edit_card, ["edit_card_service"]),
    "delete_card": (delete_card, ["delete_card_service"]),
    "get_card_by_id": (get_card_by_id, ["get_card_service"]),
    "get_column_cards": (get_column_cards, ["get_column_cards_service"]),
    "add_assignee": (add_assignee, ["add_assignee_service"]),
    "remove_assignee": (remove_assignee, ["remove_assignee_service"]),
    "get_card_assignees": (get_card_assignees, ["get_assignees_service"]),
    "add_label": (add_label, ["add_label_service"]),
    "remove_label": (remove_label, ["remove_label_service"]),
    "get_card_labels": (get_card_labels, ["get_labels_service"]),
    "add_checklist": (add_checklist, ["add_checklist_service"]),
    "update_checklist": (update_checklist, ["update_checklist_service"]),
    "delete_checklist": (delete_checklist, ["delete_checklist_service"]),
    "get_checklist_by_id": (get_checklist_by_id, ["get_checklist_service"]),
    "get_card_checklists": (get_card_checklists, ["get_card_checklists_service"]),
}
