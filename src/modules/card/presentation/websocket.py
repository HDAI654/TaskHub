import logging
import json
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter, Query
from src.modules.card.presentation.connection_manager import ConnectionManager
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.core.id_vo import ID
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    CardNotFoundError,
    ColumnNotFoundError,
    CheckListNotFoundError,
    InvalidIDError,
    PermissionDenied,
    LabelNotFoundError,
    NoChangesError,
    DatabaseError,
    CacheError,
)
from src.modules.card.presentation.dependencies import (
    get_uow,
    get_token_repo,
    get_jwt_decoder,
    get_create_card_service,
    get_edit_card_service,
    get_delete_card_service,
    get_get_card_service,
    get_get_column_cards_service,
    get_add_assignee_service,
    get_remove_assignee_service,
    get_get_assignees_service,
    get_add_label_service,
    get_remove_label_service,
    get_get_labels_service,
    get_add_checklist_service,
    get_update_checklist_service,
    get_delete_checklist_service,
    get_get_checklist_service,
    get_get_card_checklists_service,
)

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

from src.modules.card.presentation.actions import ACTION_MAP

logger = logging.getLogger(__name__)

router = APIRouter()

manager = ConnectionManager()


# ---------- WebSocket Endpoint ----------
@router.websocket("/boards/{board_id}")
async def board_websocket(
    websocket: WebSocket,
    board_id: str,
    access_token: str = Query(...),
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
    create_card_service: CreateCardService = Depends(get_create_card_service),
    edit_card_service: EditCardService = Depends(get_edit_card_service),
    delete_card_service: DeleteCardService = Depends(get_delete_card_service),
    get_card_service: GetCardByIdService = Depends(get_get_card_service),
    get_column_cards_service: GetColumnCardsService = Depends(
        get_get_column_cards_service
    ),
    add_assignee_service: AddAssigneeService = Depends(get_add_assignee_service),
    remove_assignee_service: RemoveAssigneeService = Depends(
        get_remove_assignee_service
    ),
    get_assignees_service: GetCardAssigneesService = Depends(get_get_assignees_service),
    add_label_service: AddLabelToCardService = Depends(get_add_label_service),
    remove_label_service: RemoveLabelFromCardService = Depends(
        get_remove_label_service
    ),
    get_labels_service: GetCardLabelsService = Depends(get_get_labels_service),
    add_checklist_service: AddChecklistService = Depends(get_add_checklist_service),
    update_checklist_service: UpdateChecklistService = Depends(
        get_update_checklist_service
    ),
    delete_checklist_service: DeleteChecklistService = Depends(
        get_delete_checklist_service
    ),
    get_checklist_service: GetChecklistByIdService = Depends(get_get_checklist_service),
    get_card_checklists_service: GetCardChecklistsService = Depends(
        get_get_card_checklists_service
    ),
):
    """
    WebSocket endpoint for real‑time board operations.
    All users with the same board_id are in the same room.
    """
    logger.info("WebSocket connection attempt for board %s", board_id)

    # 1. Authenticate the user and validate membership
    try:
        payload = jwt_decoder.decode_and_validate(access_token, "access")

        try:
            user_id = ID(payload["sub"])
            current_version = await token_repo.get_user_version(user_id)
            is_token_blocked = await token_repo.is_token_blocked(
                token_id=ID(payload["jti"])
            )
            if payload["ver"] != current_version or is_token_blocked:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except InvalidIDError:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Check that the user belongs to the organization that owns the board
        # First, get the board to find its project and organization
        try:
            board = await uow.boards.get_by_id(ID(board_id))
        except Exception:
            await websocket.close(code=4004, reason="Board not found")
            return

        # Get organization id via project
        try:
            project = await uow.projects.get_by_id(board.prj_id)
        except Exception:
            await websocket.close(code=4004, reason="Project not found")
            return
        org_id = project.org_id
        role = await uow.orgs.get_user_role(org_id, user_id)
        if role is None:
            await websocket.close(code=4003, reason="Not a member of this organization")
            return

        # Store user info in connection state
        websocket.state.user_id = user_id
        websocket.state.org_id = org_id
        websocket.state.board_id = board_id

    except (InvalidToken, UserNotFoundError):
        await websocket.close(code=4001, reason="Invalid token")
        return

    except Exception as e:
        logger.exception("Authentication error")
        await websocket.close(code=4000, reason="Authentication failed")
        return

    # 2. Accept connection and add to room
    await manager.connect(websocket, board_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
                continue

            action = message.get("action")
            if not action:
                await websocket.send_text(
                    json.dumps({"error": "Missing 'action' field"})
                )
                continue

            if action not in ACTION_MAP:
                await websocket.send_text(
                    json.dumps({"error": f"Unknown action: {action}"})
                )
                continue

            # Process action
            try:
                handler, service_names = ACTION_MAP[action]

                # Collect required services dynamically
                services = {}
                for name in service_names:
                    if name == "create_card_service":
                        services["create_card_service"] = create_card_service
                    elif name == "edit_card_service":
                        services["edit_card_service"] = edit_card_service
                    elif name == "delete_card_service":
                        services["delete_card_service"] = delete_card_service
                    elif name == "get_card_service":
                        services["get_card_service"] = get_card_service
                    elif name == "get_column_cards_service":
                        services["get_column_cards_service"] = get_column_cards_service
                    elif name == "add_assignee_service":
                        services["add_assignee_service"] = add_assignee_service
                    elif name == "remove_assignee_service":
                        services["remove_assignee_service"] = remove_assignee_service
                    elif name == "get_assignees_service":
                        services["get_assignees_service"] = get_assignees_service
                    elif name == "add_label_service":
                        services["add_label_service"] = add_label_service
                    elif name == "remove_label_service":
                        services["remove_label_service"] = remove_label_service
                    elif name == "get_labels_service":
                        services["get_labels_service"] = get_labels_service
                    elif name == "add_checklist_service":
                        services["add_checklist_service"] = add_checklist_service
                    elif name == "update_checklist_service":
                        services["update_checklist_service"] = update_checklist_service
                    elif name == "delete_checklist_service":
                        services["delete_checklist_service"] = delete_checklist_service
                    elif name == "get_checklist_service":
                        services["get_checklist_service"] = get_checklist_service
                    elif name == "get_card_checklists_service":
                        services["get_card_checklists_service"] = (
                            get_card_checklists_service
                        )

                result, event = await handler(
                    **services, message=message, access_token=access_token
                )
                if result is not None:
                    await websocket.send_text(
                        json.dumps(
                            {"action": action, "result": result, "status": "success"}
                        )
                    )
                if event is not None:
                    await manager.broadcast(board_id, event)

            except (InvalidToken, UserNotFoundError) as e:
                await websocket.send_text(
                    json.dumps({"error": "Authentication error", "details": str(e)})
                )
            except PermissionDenied as e:
                await websocket.send_text(
                    json.dumps({"error": "Permission denied", "details": str(e)})
                )
            except (
                OrgNotFoundError,
                ColumnNotFoundError,
                CardNotFoundError,
                CheckListNotFoundError,
                LabelNotFoundError,
            ) as e:
                await websocket.send_text(
                    json.dumps({"error": "Not found", "details": str(e)})
                )
            except NoChangesError as e:
                await websocket.send_text(
                    json.dumps({"error": "No changes provided", "details": str(e)})
                )
            except ValueError as e:
                await websocket.send_text(
                    json.dumps({"error": "Invalid request", "details": str(e)})
                )
            except (DatabaseError, CacheError) as e:
                logger.exception("Database/Cache error during WebSocket action")
                await websocket.send_text(
                    json.dumps(
                        {
                            "error": "Internal server error",
                            "details": "Please try again later",
                        }
                    )
                )
            except Exception as e:
                logger.exception("Unexpected error in WebSocket handler")
                await websocket.send_text(
                    json.dumps({"error": "Internal error", "details": str(e)})
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, board_id)
        logger.info(f"WebSocket disconnected from board {board_id}")
    except Exception as e:
        logger.exception(f"Unexpected WebSocket error: {e}")
        manager.disconnect(websocket, board_id)
