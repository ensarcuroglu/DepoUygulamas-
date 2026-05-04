"""talep_tahmin_cache_tablosu

Revision ID: c1d4e5f6a7b8
Revises: daa71d83850f
Create Date: 2026-05-04 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'daa71d83850f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Talep tahmini cache tablosu — nightly job tarafindan upsert edilir."""
    op.create_table(
        'talep_tahmin_cache',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column(
            'urun_id',
            sa.Integer(),
            sa.ForeignKey('urunler.id'),
            nullable=False,
        ),
        sa.Column('tahmin_gun', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('stok_riski', sa.String(length=20), nullable=False),
        sa.Column('tahmini_talep', sa.Float(), server_default='0', nullable=False),
        sa.Column('onerilen_ikmal', sa.Float(), server_default='0', nullable=False),
        sa.Column('veri_guven_skoru', sa.Float(), server_default='0', nullable=False),
        sa.Column('model_versiyonu', sa.String(length=80), nullable=False),
        sa.Column(
            'hesaplanma_tarihi',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            'urun_id', 'tahmin_gun', name='uq_talep_tahmin_cache_urun_ufuk'
        ),
    )
    op.create_index(
        'ix_talep_tahmin_cache_urun_id', 'talep_tahmin_cache', ['urun_id']
    )
    op.create_index(
        'ix_talep_tahmin_cache_tahmin_gun', 'talep_tahmin_cache', ['tahmin_gun']
    )
    op.create_index(
        'ix_talep_tahmin_cache_stok_riski', 'talep_tahmin_cache', ['stok_riski']
    )
    op.create_index(
        'ix_talep_tahmin_cache_hesaplanma_tarihi',
        'talep_tahmin_cache',
        ['hesaplanma_tarihi'],
    )


def downgrade() -> None:
    op.drop_index('ix_talep_tahmin_cache_hesaplanma_tarihi', table_name='talep_tahmin_cache')
    op.drop_index('ix_talep_tahmin_cache_stok_riski', table_name='talep_tahmin_cache')
    op.drop_index('ix_talep_tahmin_cache_tahmin_gun', table_name='talep_tahmin_cache')
    op.drop_index('ix_talep_tahmin_cache_urun_id', table_name='talep_tahmin_cache')
    op.drop_table('talep_tahmin_cache')
