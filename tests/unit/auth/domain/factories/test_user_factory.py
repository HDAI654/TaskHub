from src.modules.auth.domain.factories.user_factory import UserFactory


class TestUserFactory:
    def test_create_success(self):
        user = UserFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDD",
            email="marshall@eminem.com",
            hashed_password="example_hashed_password",
        )

        assert user.id.value == "MyIDDDDDDDDDDDDDDDDDDD"
        assert user.email.value == "marshall@eminem.com"
        assert user.hashed_password.value == "example_hashed_password"
