"""rabbitmq_outbox_alanlari

LMS Faz 2 — `gorev_performans_eventleri` tablosuna RabbitMQ outbox relay
durum alanlarını ekler. Mevcut event'ler için `event_uuid` MySQL UUID()
ile backfill edilir.

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d8e9
Create Date: 2026-05-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3a4b5c6d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'gorev_performans_eventleri',
        sa.Column('event_uuid', sa.String(length=36), nullable=True),
    )
    op.add_column(
        'gorev_performans_eventleri',
        sa.Column(
            'rabbitmq_yayinlandi',
            sa.Boolean(),
            server_default=sa.text('0'),
            nullable=False,
        ),
    )
    op.add_column(
        'gorev_performans_eventleri',
        sa.Column('rabbitmq_yayin_tarihi', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'gorev_performans_eventleri',
        sa.Column(
            'rabbitmq_deneme_sayisi',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
    )
    op.add_column(
        'gorev_performans_eventleri',
        sa.Column('rabbitmq_son_hata', sa.Text(), nullable=True),
    )

    # Backfill mevcut event'lere benzersiz UUID — MySQL UUID() string döner.
    op.execute(
        "UPDATE gorev_performans_eventleri "
        "SET event_uuid = UUID() WHERE event_uuid IS NULL"
    )

    op.alter_column(
        'gorev_performans_eventleri',
        'event_uuid',
        existing_type=sa.String(length=36),
        nullable=False,
    )

    op.create_index(
        'ix_gorev_performans_eventleri_rabbitmq_yayinlandi',
        'gorev_performans_eventleri',
        ['rabbitmq_yayinlandi'],
    )
    op.create_index(
        'ix_gorev_performans_event_relay_outbox',
        'gorev_performans_eventleri',
        ['rabbitmq_yayinlandi', 'olusturma_tarihi'],
    )
    op.create_unique_constraint(
        'uq_gorev_performans_eventleri_event_uuid',
        'gorev_performans_eventleri',
        ['event_uuid'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_gorev_performans_eventleri_event_uuid',
        'gorev_performans_eventleri',
        type_='unique',
    )
    op.drop_index(
        'ix_gorev_performans_event_relay_outbox',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_rabbitmq_yayinlandi',
        table_name='gorev_performans_eventleri',
    )
    op.drop_column('gorev_performans_eventleri', 'rabbitmq_son_hata')
    op.drop_column('gorev_performans_eventleri', 'rabbitmq_deneme_sayisi')
    op.drop_column('gorev_performans_eventleri', 'rabbitmq_yayin_tarihi')
    op.drop_column('gorev_performans_eventleri', 'rabbitmq_yayinlandi')
    op.drop_column('gorev_performans_eventleri', 'event_uuid')
