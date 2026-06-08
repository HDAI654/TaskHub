from fastapi import APIRouter
from src.modules.auth.presentation.api.v1.delete_account import (
    router as delete_account_router,
)
from src.modules.auth.presentation.api.v1.forget_password import (
    router as forget_password_router,
)
from src.modules.auth.presentation.api.v1.login import router as login_router
from src.modules.auth.presentation.api.v1.logout import router as logout_router
from src.modules.auth.presentation.api.v1.refresh import router as refresh_router
from src.modules.auth.presentation.api.v1.reset_password import (
    router as reset_password_router,
)
from src.modules.auth.presentation.api.v1.set_password import (
    router as set_password_router,
)
from src.modules.auth.presentation.api.v1.signup import router as signup_router

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

router.include_router(delete_account_router)
router.include_router(forget_password_router)
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(refresh_router)
router.include_router(reset_password_router)
router.include_router(set_password_router)
router.include_router(signup_router)
