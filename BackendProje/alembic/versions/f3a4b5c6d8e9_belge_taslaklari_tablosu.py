"""belge_taslaklari_tablosu

Revision ID: f3a4b5c6d8e9
Revises: e2f3a4b5c6d7
Create Date: 2026-05-11 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a4b5c6d8e9"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "belge_taslaklari",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("kaynak_dosya_yolu", sa.String(length=500), nullable=True),
        sa.Column(
            "belge_tipi",
            sa.String(length=50),
            server_default="IRSALIYE",
            nullable=False,
        ),
        sa.Column("ham_json", sa.JSON(), nullable=False),
        sa.Column(
            "durum",
            sa.String(length=30),
            server_default="KABUL_BEKLIYOR",
            nullable=False,
        ),
        sa.Column("confidence_skoru", sa.Float(), server_default="0", nullable=False),
        sa.Column(
            "olusturan_kullanici_id",
            sa.Integer(),
            sa.ForeignKey("kullanicilar.id"),
            nullable=True,
        ),
        sa.Column(
            "depo_id",
            sa.Integer(),
            sa.ForeignKey("depolar.id"),
            nullable=False,
        ),
        sa.Column(
            "mal_kabul_irsaliye_id",
            sa.Integer(),
            sa.ForeignKey("mal_kabul_irsaliyeleri.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_belge_taslaklari_belge_tipi", "belge_taslaklari", ["belge_tipi"])
    op.create_index("ix_belge_taslaklari_durum", "belge_taslaklari", ["durum"])
    op.create_index(
        "ix_belge_taslaklari_olusturan_kullanici_id",
        "belge_taslaklari",
        ["olusturan_kullanici_id"],
    )
    op.create_index("ix_belge_taslaklari_depo_id", "belge_taslaklari", ["depo_id"])
    op.create_index(
        "ix_belge_taslaklari_mal_kabul_irsaliye_id",
        "belge_taslaklari",
        ["mal_kabul_irsaliye_id"],
    )
    op.create_index(
        "ix_belge_taslaklari_created_at",
        "belge_taslaklari",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_belge_taslaklari_created_at", table_name="belge_taslaklari")
    op.drop_index(
        "ix_belge_taslaklari_mal_kabul_irsaliye_id",
        table_name="belge_taslaklari",
    )
    op.drop_index("ix_belge_taslaklari_depo_id", table_name="belge_taslaklari")
    op.drop_index(
        "ix_belge_taslaklari_olusturan_kullanici_id",
        table_name="belge_taslaklari",
    )
    op.drop_index("ix_belge_taslaklari_durum", table_name="belge_taslaklari")
    op.drop_index("ix_belge_taslaklari_belge_tipi", table_name="belge_taslaklari")
    op.drop_table("belge_taslaklari")
