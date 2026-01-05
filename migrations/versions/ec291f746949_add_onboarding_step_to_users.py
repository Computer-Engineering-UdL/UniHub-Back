"""add onboarding_step to users

Revision ID: ec291f746949
Revises: 3ef72cbe3fbf
Create Date: 2026-01-03 11:01:46.248969

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ec291f746949"
down_revision: Union[str, Sequence[str], None] = "3ef72cbe3fbf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user", sa.Column("onboarding_step", sa.String(length=20), server_default="not_started", nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user", "onboarding_step")
