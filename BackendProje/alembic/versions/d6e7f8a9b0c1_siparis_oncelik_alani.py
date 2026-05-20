"""siparis_oncelik_alani

Revision ID: d6e7f8a9b0c1
Revises: b5c6d7e8f9a0
Create Date: 2026-05-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, Sequence[str], None] = "b5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "siparisler",
        sa.Column(
            "oncelik",
            sa.Integer(),
            server_default="5",
            nullable=False,
        ),
    )
    op.create_index("ix_siparisler_oncelik", "siparisler", ["oncelik"])


def downgrade() -> None:
    op.drop_index("ix_siparisler_oncelik", table_name="siparisler")
    op.drop_column("siparisler", "oncelik")
