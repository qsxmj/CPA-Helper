"""Remove theme preference from app settings.

Revision ID: 20260513_0001
Revises: 20260511_0005
Create Date: 2026-05-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260513_0001"
down_revision: str | None = "20260511_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return any(
        column["name"] == column_name
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    )


def upgrade() -> None:
    if not _column_exists("app_settings", "theme_preference"):
        return
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("theme_preference")


def downgrade() -> None:
    if _column_exists("app_settings", "theme_preference"):
        return
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "theme_preference",
                sa.String(length=16),
                nullable=False,
                server_default="system",
            )
        )
