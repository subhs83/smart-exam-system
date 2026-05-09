"""Add school_id foreign key to ExamModel

Revision ID: 08f218a1f116
Revises: cb813556cb29
Create Date: 2026-05-09 00:22:15.749898

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '926fc660d202'
down_revision = 'cb813556cb29'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_exams_school_id',   # name of the constraint
            'schools',              # referent table
            ['school_id'],          # local column
            ['id']                  # remote column
        )

def downgrade():
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.drop_constraint('fk_exams_school_id', type_='foreignkey')

