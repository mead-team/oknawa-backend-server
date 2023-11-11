"""init migrations

Revision ID: c7d7af19a559
Revises: 
Create Date: 2023-11-11 06:54:52.727834

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d7af19a559"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="생성일시",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="수정일시",
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="삭제일시"),
        sa.PrimaryKeyConstraint("id"),
        comment="아이템",
    )
    op.create_index(op.f("ix_item_description"), "item", ["description"], unique=False)
    op.create_index(op.f("ix_item_id"), "item", ["id"], unique=False)
    op.create_index(op.f("ix_item_title"), "item", ["title"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_item_title"), table_name="item")
    op.drop_index(op.f("ix_item_id"), table_name="item")
    op.drop_index(op.f("ix_item_description"), table_name="item")
    op.drop_table("item")
    # ### end Alembic commands ###
