"""add_prefix_to_uretim_seri_sayac

Revision ID: daa71d83850f
Revises: 94f3a07ddcd5
Create Date: 2026-04-29 12:05:38.556500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daa71d83850f'
down_revision: Union[str, Sequence[str], None] = '94f3a07ddcd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add prefix column
    op.add_column('uretim_seri_sayac', sa.Column('prefix', sa.String(length=10), server_default='PRD', nullable=False))
    
    # Change primary key from (tarih) to (prefix, tarih)
    # Using raw SQL for MySQL PK drop/add to ensure compatibility
    op.execute("ALTER TABLE uretim_seri_sayac DROP PRIMARY KEY")
    op.execute("ALTER TABLE uretim_seri_sayac ADD PRIMARY KEY (prefix, tarih)")

def downgrade() -> None:
    """Downgrade schema."""
    # Revert primary key back to (tarih)
    op.execute("ALTER TABLE uretim_seri_sayac DROP PRIMARY KEY")
    op.execute("ALTER TABLE uretim_seri_sayac ADD PRIMARY KEY (tarih)")
    
    # Drop prefix column
    op.drop_column('uretim_seri_sayac', 'prefix')
