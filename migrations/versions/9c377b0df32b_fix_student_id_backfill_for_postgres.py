"""fix student_id backfill for Postgres

Revision ID: 9c377b0df32b
Revises: 0473a4c8ec00
Create Date: 2026-06-05 01:07:30.699791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c377b0df32b'
down_revision = '0473a4c8ec00'
branch_labels = None
depends_on = None

def upgrade():
    # Backfill any NULL student_id values with UUIDs
    op.execute("UPDATE student_attempts SET student_id = gen_random_uuid() WHERE student_id IS NULL;")

    # Ensure future inserts auto-generate UUIDs
    op.execute("ALTER TABLE student_attempts ALTER COLUMN student_id SET DEFAULT gen_random_uuid();")

def downgrade():
    # Remove default if downgrading
    op.execute("ALTER TABLE student_attempts ALTER COLUMN student_id DROP DEFAULT;")