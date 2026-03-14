"""add_filename_to_asset

Revision ID: a3f9c12e4b01
Revises: 1bf23ef769e2
Create Date: 2026-03-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f9c12e4b01'
down_revision = '1bf23ef769e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('asset', schema=None) as batch_op:
        batch_op.add_column(sa.Column('filename', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('asset', schema=None) as batch_op:
        batch_op.drop_column('filename')
