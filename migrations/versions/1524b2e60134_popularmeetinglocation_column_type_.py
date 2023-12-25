"""popularmeetinglocation column type modify

Revision ID: 1524b2e60134
Revises: 7785dbe07ac8
Create Date: 2023-12-22 07:42:12.452404

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1524b2e60134"
down_revision: Union[str, None] = "7785dbe07ac8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "popular_meeting_location",
        "location_x",
        existing_type=sa.VARCHAR(),
        type_=sa.Float(),
        existing_comment="x좌표",
        existing_nullable=False,
        postgresql_using="location_x::double precision",
    )
    op.alter_column(
        "popular_meeting_location",
        "location_y",
        existing_type=sa.VARCHAR(),
        type_=sa.Float(),
        existing_comment="y좌표",
        existing_nullable=False,
        postgresql_using="location_x::double precision",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "popular_meeting_location",
        "location_y",
        existing_type=sa.Float(),
        type_=sa.VARCHAR(),
        existing_comment="y좌표",
        existing_nullable=False,
    )
    op.alter_column(
        "popular_meeting_location",
        "location_x",
        existing_type=sa.Float(),
        type_=sa.VARCHAR(),
        existing_comment="x좌표",
        existing_nullable=False,
    )
    # ### end Alembic commands ###