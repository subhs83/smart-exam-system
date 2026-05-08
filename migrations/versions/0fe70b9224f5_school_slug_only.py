"""school slug only

Revision ID: 0fe70b9224f5
Revises: 08619c7307e7
Create Date: 2026-05-08 10:47:09.616153
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0fe70b9224f5'
down_revision = '08619c7307e7'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('schools', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_schools_slug', ['slug'])

    with op.batch_alter_table('student_attempts', schema=None) as batch_op:
        batch_op.create_index(
            'idx_exam_submitted_percentage',
            ['exam_id', 'is_submitted', 'percentage'],
            unique=False
        )


def downgrade():

    with op.batch_alter_table('schools', schema=None) as batch_op:
        batch_op.drop_constraint('uq_schools_slug', type_='unique')
        batch_op.drop_column('slug')