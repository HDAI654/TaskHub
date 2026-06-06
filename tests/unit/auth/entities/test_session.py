from src.modules.auth.domain.entities.session import SessionEntity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.date import Date


class TestSessionEntity:
    def test_eq_id(self):
        session = SessionEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDD"),
            user_id=ID("MyUserIDDDDDDDDDDDDDDD"),
            created_at=Date(),
        )
        session2 = SessionEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDD"),
            user_id=ID("MyUserIDDDDDDDDDDDDDDD"),
            created_at=Date("1999-05-08"),
        )
        session3 = SessionEntity(
            id=ID("MyDifferentIDDDDDDDDDD"),
            user_id=ID("MyUserIDDDDDDDDDDDDDDD"),
            created_at=Date("2025-12-09"),
        )

        assert session == session2
        assert session != session3 and session2 != session3
