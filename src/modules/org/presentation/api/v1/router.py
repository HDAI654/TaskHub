from fastapi import APIRouter
from .create_org import router as create_org_router
from .get_org import router as get_org_router
from .update_org import router as update_org_router
from .delete_org import router as delete_org_router
from .add_member import router as add_member_router
from .remove_member import router as remove_member_router
from .change_user_role import router as change_user_role_router
from .get_user_orgs import router as get_user_orgs_router
from .get_org_members import router as get_org_members_router

router = APIRouter(prefix="/api/v1", tags=["Organizations"])

router.include_router(create_org_router)
router.include_router(get_org_router)
router.include_router(update_org_router)
router.include_router(delete_org_router)
router.include_router(add_member_router)
router.include_router(remove_member_router)
router.include_router(change_user_role_router)
router.include_router(get_user_orgs_router)
router.include_router(get_org_members_router)
