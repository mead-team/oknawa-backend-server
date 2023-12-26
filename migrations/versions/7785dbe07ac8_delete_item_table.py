"""delete item table

Revision ID: 7785dbe07ac8
Revises: f96f41032ef0
Create Date: 2023-12-09 07:09:21.873236

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7785dbe07ac8"
down_revision: Union[str, None] = "f96f41032ef0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_item_description", table_name="item")
    op.drop_index("ix_item_id", table_name="item")
    op.drop_index("ix_item_title", table_name="item")
    op.drop_table("item")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "item",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("title", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
            comment="생성일시",
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
            comment="수정일시",
        ),
        sa.Column(
            "deleted_at",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
            comment="삭제일시",
        ),
        sa.PrimaryKeyConstraint("id", name="item_pkey"),
        comment="아이템",
    )
    op.create_index("ix_item_title", "item", ["title"], unique=False)
    op.create_index("ix_item_id", "item", ["id"], unique=False)
    op.create_index("ix_item_description", "item", ["description"], unique=False)
    # ### end Alembic commands ###
