"""Add gemini_access_until to user table

Revision ID: a2b3c4d5e6f7
Revises: 42e2978c7933
Create Date: 2026-07-21 00:00:00.000000
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '42e2978c7933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = {c['name'] for c in inspector.get_columns('user')}
    if 'gemini_access_until' not in user_columns:
        op.add_column('user', sa.Column('gemini_access_until', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('gemini_access_until')
