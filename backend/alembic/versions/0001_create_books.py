"""create books table"""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_books"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False),
        sa.Column("genre", sa.String(length=60), nullable=False, server_default="General"),
        sa.Column("pages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shelf", sa.String(length=20), nullable=False, server_default="WANT"),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("added_on", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_books_shelf", "books", ["shelf"])


def downgrade():
    op.drop_index("ix_books_shelf", table_name="books")
    op.drop_table("books")
