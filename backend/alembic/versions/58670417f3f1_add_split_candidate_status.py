"""add split candidate status

Revision ID: 58670417f3f1
Revises: 235074550aec
Create Date: 2026-08-16 20:59:05.240369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58670417f3f1'
down_revision: Union[str, None] = '235074550aec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE candidate_status ADD VALUE IF NOT EXISTS 'split'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; downgrading would require
    # recreating the type. Not needed for an additive status value.
    pass
