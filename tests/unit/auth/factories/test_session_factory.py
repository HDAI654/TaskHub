from src.modules.auth.domain.factories.session_factory import SessionFactory
from datetime import date


class TestUserFactory:
    def test_create_success(self):
        user = SessionFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDD",
            user_id="UserIDDDDDDDDDDDDDDDDD",
            created_at="1998-06-08",
        )

        assert user.id.value == "MyIDDDDDDDDDDDDDDDDDDD"
        assert user.user_id.value == "UserIDDDDDDDDDDDDDDDDD"
        assert user.created_at.value == date(1998, 6, 8)
