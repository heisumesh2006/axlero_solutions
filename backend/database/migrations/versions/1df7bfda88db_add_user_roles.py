from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "1df7bfda88db"
down_revision: Union[str, Sequence[str], None] = "db3a7dcf40b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="USER"
        )
    )


def downgrade() -> None:
    op.drop_column("users", "role")