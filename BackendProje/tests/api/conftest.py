"""API test conftest — factory session binding (DB gerektiren testler için)."""

import pytest
from tests.factories import ALL_FACTORIES


@pytest.fixture(autouse=True)
def _bind_factories(db_session):
    """Tüm factory'lere aktif session'ı bağla."""
    for factory_cls in ALL_FACTORIES:
        factory_cls._meta.sqlalchemy_session = db_session
