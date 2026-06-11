from fastapi import APIRouter
from src.modules.org.presentation.api.v1.create_org import router as create_org_router
from src.modules.org.presentation.api.v1.get_org import router as get_org_router
from src.modules.org.presentation.api.v1.update_org import router as update_org_router
from src.modules.org.presentation.api.v1.delete_org import router as delete_org_router
from src.modules.org.presentation.api.v1.add_member import router as add_member_router
from src.modules.org.presentation.api.v1.remove_member import (
    router as remove_member_router,
)
from src.modules.org.presentation.api.v1.change_user_role import (
    router as change_user_role_router,
)
from src.modules.org.presentation.api.v1.get_user_orgs import (
    router as get_user_orgs_router,
)
from src.modules.org.presentation.api.v1.get_org_members import (
    router as get_org_members_router,
)

from src.modules.org.presentation.api.v1.create_project import (
    router as create_project_router,
)
from src.modules.org.presentation.api.v1.update_project import (
    router as update_project_router,
)
from src.modules.org.presentation.api.v1.delete_project import (
    router as delete_project_router,
)
from src.modules.org.presentation.api.v1.get_project import router as get_project_router
from src.modules.org.presentation.api.v1.get_org_projects import (
    router as get_org_projects_router,
)

from src.modules.org.presentation.api.v1.create_board import (
    router as create_board_router,
)
from src.modules.org.presentation.api.v1.update_board import (
    router as update_board_router,
)
from src.modules.org.presentation.api.v1.delete_board import (
    router as delete_board_router,
)
from src.modules.org.presentation.api.v1.get_board import router as get_board_router
from src.modules.org.presentation.api.v1.get_project_boards import (
    router as get_project_boards_router,
)

from src.modules.org.presentation.api.v1.create_column import (
    router as create_column_router,
)
from src.modules.org.presentation.api.v1.update_column import (
    router as update_column_router,
)
from src.modules.org.presentation.api.v1.delete_column import (
    router as delete_column_router,
)
from src.modules.org.presentation.api.v1.get_column import router as get_column_router
from src.modules.org.presentation.api.v1.get_board_columns import (
    router as get_board_columns_router,
)

router = APIRouter(prefix="/api/v1/mng", tags=["Organizations"])

router.include_router(create_org_router)
router.include_router(get_org_router)
router.include_router(update_org_router)
router.include_router(delete_org_router)
router.include_router(add_member_router)
router.include_router(remove_member_router)
router.include_router(change_user_role_router)
router.include_router(get_user_orgs_router)
router.include_router(get_org_members_router)

router.include_router(create_project_router)
router.include_router(update_project_router)
router.include_router(delete_project_router)
router.include_router(get_project_router)
router.include_router(get_org_projects_router)

router.include_router(create_board_router)
router.include_router(update_board_router)
router.include_router(delete_board_router)
router.include_router(get_board_router)
router.include_router(get_project_boards_router)

router.include_router(create_column_router)
router.include_router(update_column_router)
router.include_router(delete_column_router)
router.include_router(get_column_router)
router.include_router(get_board_columns_router)
