"""make_metadata_fields_optional

Revision ID: 94f3a07ddcd5
Revises: 7f50efcab8fd
Create Date: 2026-04-21 17:13:12.355181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '94f3a07ddcd5'
down_revision: Union[str, Sequence[str], None] = '7f50efcab8fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('depolar', 'adres', existing_type=mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True)
    op.alter_column('depolar', 'aciklama', existing_type=mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True)
    op.alter_column('kategoriler', 'aciklama', existing_type=mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True)
    op.alter_column('kategoriler', 'ikon', existing_type=mysql.VARCHAR(charset='utf8mb4', collation='utf8mb4_unicode_ci', length=50), nullable=True, existing_server_default=sa.text("'FolderOpen'"))
    op.alter_column('lotlar', 'aciklama', existing_type=mysql.TEXT(charset='utf8mb4', collation='utf8mb4_unicode_ci'), nullable=True)
    op.alter_column('urunler', 'aciklama', existing_type=mysql.TEXT(charset='utf8mb4', collation='utf8mb4_unicode_ci'), nullable=True)
    op.alter_column('urunler', 'depolama_tipi', existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=20), nullable=True, existing_server_default=sa.text("'Kuru'"))
    op.alter_column('raflar', 'bolge', existing_type=mysql.VARCHAR(length=50), nullable=True)
    op.alter_column('raflar', 'koridor', existing_type=mysql.VARCHAR(length=10), nullable=True)

def downgrade() -> None:
    """Downgrade schema."""
    pass