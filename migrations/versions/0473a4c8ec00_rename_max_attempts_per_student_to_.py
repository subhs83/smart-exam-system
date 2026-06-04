"""Rename max_attempts_per_student to ExamModel

Revision ID: 0473a4c8ec00
Revises: 0f6407f4c760
Create Date: 2026-06-04 12:53:09.495667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0473a4c8ec00'
down_revision = '0f6407f4c760'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.alter_column('max_attempts_per_mobile',
                              new_column_name='max_attempts_per_student')

    # ✅ Backfill student_id before enforcing NOT NULL
    op.execute("UPDATE student_attempts SET student_id = hex(randomblob(16)) WHERE student_id IS NULL")

    with op.batch_alter_table('student_attempts', schema=None) as batch_op:
        batch_op.alter_column('student_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=False)



    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('student_attempts', schema=None) as batch_op:
        batch_op.alter_column('student_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=True)

    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_attempts_per_mobile', sa.INTEGER(), nullable=True))
        batch_op.drop_column('max_attempts_per_student')


    # ### end Alembic commands ###
