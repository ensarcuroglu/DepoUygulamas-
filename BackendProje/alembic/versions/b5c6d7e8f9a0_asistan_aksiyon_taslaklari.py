"""asistan_aksiyon_taslaklari

Revision ID: b5c6d7e8f9a0
Revises: a1b2c3d4e5f6
Create Date: 2026-05-18 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asistan_aksiyon_taslaklari",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "kullanici_id",
            sa.Integer(),
            sa.ForeignKey("kullanicilar.id"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(length=32), nullable=False),
        sa.Column("tool_id", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column(
            "durum",
            sa.String(length=30),
            server_default="BEKLEMEDE",
            nullable=False,
        ),
        sa.Column("ozet", sa.String(length=500), nullable=True),
        sa.Column(
            "idempotency_key",
            sa.String(length=128),
            nullable=False,
            unique=True,
        ),
        sa.Column("sonuc_json", sa.JSON(), nullable=True),
        sa.Column("hata_mesaji", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_asistan_aksiyon_taslaklari_kullanici_id",
        "asistan_aksiyon_taslaklari",
        ["kullanici_id"],
    )
    op.create_index(
        "ix_asistan_aksiyon_taslaklari_durum",
        "asistan_aksiyon_taslaklari",
        ["durum"],
    )
    op.create_index(
        "ix_asistan_aksiyon_taslaklari_tool_id",
        "asistan_aksiyon_taslaklari",
        ["tool_id"],
    )
    op.create_index(
        "ix_asistan_aksiyon_taslaklari_expires_at",
        "asistan_aksiyon_taslaklari",
        ["expires_at"],
    )
    op.create_index(
        "ix_asistan_aksiyon_taslaklari_created_at",
        "asistan_aksiyon_taslaklari",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_asistan_aksiyon_taslaklari_created_at",
        table_name="asistan_aksiyon_taslaklari",
    )
    op.drop_index(
        "ix_asistan_aksiyon_taslaklari_expires_at",
        table_name="asistan_aksiyon_taslaklari",
    )
    op.drop_index(
        "ix_asistan_aksiyon_taslaklari_tool_id",
        table_name="asistan_aksiyon_taslaklari",
    )
    op.drop_index(
        "ix_asistan_aksiyon_taslaklari_durum",
        table_name="asistan_aksiyon_taslaklari",
    )
    op.drop_index(
        "ix_asistan_aksiyon_taslaklari_kullanici_id",
        table_name="asistan_aksiyon_taslaklari",
    )
    op.drop_table("asistan_aksiyon_taslaklari")
