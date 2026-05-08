"""add school logo

Revision ID: cb813556cb29
Revises: 0fe70b9224f5
Create Date: 2026-05-08 13:03:48.856123

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb813556cb29'
down_revision = '0fe70b9224f5'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('schools', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logo', sa.String(length=255), nullable=True))


def downgrade():

    with op.batch_alter_table('schools', schema=None) as batch_op:
        batch_op.drop_column('logo')

    # ### end Alembic commands ###
