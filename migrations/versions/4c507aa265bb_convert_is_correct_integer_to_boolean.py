"""convert is_correct integer to boolean

Revision ID: 4c507aa265bb
Revises: a8bbd28b31f3
Create Date: 2026-05-20 11:29:03.309597

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c507aa265bb'
down_revision = 'a8bbd28b31f3'
branch_labels = None
depends_on = None


def upgrade():

    op.execute("""
        ALTER TABLE student_answers
        ALTER COLUMN is_correct
        TYPE BOOLEAN
        USING CASE
            WHEN is_correct = 1 THEN TRUE
            ELSE FALSE
        END
    """)

    # ### end Alembic commands ###


def downgrade():

    op.execute("""
        ALTER TABLE student_answers
        ALTER COLUMN is_correct
        TYPE INTEGER
        USING CASE
            WHEN is_correct = TRUE THEN 1
            ELSE 0
        END
    """)

    # ### end Alembic commands ###
