"""operator_performans_modulu

LMS Faz 1 — Görev performans olay log'u (transactional outbox) ve
operatör vardiya KPI özeti tabloları.

Revision ID: e2f3a4b5c6d7
Revises: c1d4e5f6a7b8
Create Date: 2026-05-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'c1d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """LMS Faz 1 tablolarını oluşturur."""

    # ── gorev_performans_eventleri (transactional outbox event log) ──
    op.create_table(
        'gorev_performans_eventleri',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('event_tipi', sa.String(length=30), nullable=False),
        sa.Column('gorev_tipi', sa.String(length=20), nullable=False),
        sa.Column('gorev_id', sa.Integer(), nullable=False),
        sa.Column(
            'kullanici_id',
            sa.Integer(),
            sa.ForeignKey('kullanicilar.id'),
            nullable=False,
        ),
        sa.Column(
            'depo_id',
            sa.Integer(),
            sa.ForeignKey('depolar.id'),
            nullable=True,
        ),
        sa.Column('sure_saniye', sa.Integer(), nullable=True),
        sa.Column('iptal_nedeni', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column(
            'aggregate_edildi',
            sa.Boolean(),
            server_default=sa.text('0'),
            nullable=False,
        ),
        sa.Column(
            'olusturma_tarihi',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        'ix_gorev_performans_eventleri_event_tipi',
        'gorev_performans_eventleri',
        ['event_tipi'],
    )
    op.create_index(
        'ix_gorev_performans_eventleri_gorev_tipi',
        'gorev_performans_eventleri',
        ['gorev_tipi'],
    )
    op.create_index(
        'ix_gorev_performans_eventleri_gorev_id',
        'gorev_performans_eventleri',
        ['gorev_id'],
    )
    op.create_index(
        'ix_gorev_performans_eventleri_kullanici_id',
        'gorev_performans_eventleri',
        ['kullanici_id'],
    )
    op.create_index(
        'ix_gorev_performans_eventleri_depo_id',
        'gorev_performans_eventleri',
        ['depo_id'],
    )
    op.create_index(
        'ix_gorev_performans_eventleri_aggregate_edildi',
        'gorev_performans_eventleri',
        ['aggregate_edildi'],
    )
    op.create_index(
        'ix_gorev_performans_eventleri_olusturma_tarihi',
        'gorev_performans_eventleri',
        ['olusturma_tarihi'],
    )
    op.create_index(
        'ix_gorev_performans_event_outbox',
        'gorev_performans_eventleri',
        ['aggregate_edildi', 'olusturma_tarihi'],
    )
    op.create_index(
        'ix_gorev_performans_event_kullanici_tarih',
        'gorev_performans_eventleri',
        ['kullanici_id', 'olusturma_tarihi'],
    )

    # ── operator_vardiya_metrikleri (vardiya bazlı KPI özeti) ──
    op.create_table(
        'operator_vardiya_metrikleri',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'kullanici_id',
            sa.Integer(),
            sa.ForeignKey('kullanicilar.id'),
            nullable=False,
        ),
        sa.Column(
            'depo_id',
            sa.Integer(),
            sa.ForeignKey('depolar.id'),
            nullable=True,
        ),
        sa.Column('vardiya_tarihi', sa.Date(), nullable=False),
        sa.Column(
            'tamamlanan_yerlestirme',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'tamamlanan_toplama',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'iptal_sayisi',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'toplam_aktif_saniye',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'ortalama_gorev_suresi_sn',
            sa.Float(),
            server_default='0',
            nullable=False,
        ),
        sa.Column(
            'son_guncelleme',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            'kullanici_id',
            'vardiya_tarihi',
            name='uq_operator_vardiya_metrikleri_kullanici_tarih',
        ),
    )
    op.create_index(
        'ix_operator_vardiya_metrikleri_kullanici_id',
        'operator_vardiya_metrikleri',
        ['kullanici_id'],
    )
    op.create_index(
        'ix_operator_vardiya_metrikleri_depo_id',
        'operator_vardiya_metrikleri',
        ['depo_id'],
    )
    op.create_index(
        'ix_operator_vardiya_metrikleri_vardiya_tarihi',
        'operator_vardiya_metrikleri',
        ['vardiya_tarihi'],
    )
    op.create_index(
        'ix_operator_vardiya_metrikleri_depo_tarih',
        'operator_vardiya_metrikleri',
        ['depo_id', 'vardiya_tarihi'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_operator_vardiya_metrikleri_depo_tarih',
        table_name='operator_vardiya_metrikleri',
    )
    op.drop_index(
        'ix_operator_vardiya_metrikleri_vardiya_tarihi',
        table_name='operator_vardiya_metrikleri',
    )
    op.drop_index(
        'ix_operator_vardiya_metrikleri_depo_id',
        table_name='operator_vardiya_metrikleri',
    )
    op.drop_index(
        'ix_operator_vardiya_metrikleri_kullanici_id',
        table_name='operator_vardiya_metrikleri',
    )
    op.drop_table('operator_vardiya_metrikleri')

    op.drop_index(
        'ix_gorev_performans_event_kullanici_tarih',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_event_outbox',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_olusturma_tarihi',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_aggregate_edildi',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_depo_id',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_kullanici_id',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_gorev_id',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_gorev_tipi',
        table_name='gorev_performans_eventleri',
    )
    op.drop_index(
        'ix_gorev_performans_eventleri_event_tipi',
        table_name='gorev_performans_eventleri',
    )
    op.drop_table('gorev_performans_eventleri')
