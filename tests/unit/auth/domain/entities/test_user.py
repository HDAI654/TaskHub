from src.modules.auth.domain.entities.user import UserEntity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password import HashedPassword


class TestUserEntity:
    def test_eq_id(self):
        user = UserEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            email=Email("MyExampleEmail@gmail.com"),
            hashed_password=HashedPassword("example_hashed_password"),
        )
        user2 = UserEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            email=Email("MyEmail@gmail.com"),
            hashed_password=HashedPassword("example_hashed_password"),
        )
        user3 = UserEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            email=Email("ExampleEmail@gmail.com"),
            hashed_password=HashedPassword("example_hashed_password"),
        )

        assert user == user2
        assert user != user3 and user2 != user3
