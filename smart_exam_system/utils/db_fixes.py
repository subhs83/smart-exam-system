from sqlalchemy import inspect, text
from smart_exam_system.extensions import db


def ensure_column(table_name, column_name, sql_definition):

    inspector = inspect(db.engine)

    columns = [c["name"] for c in inspector.get_columns(table_name)]

    if column_name not in columns:

        db.session.execute(
            text(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {sql_definition}"
            )
        )

        db.session.commit()

        print(f"Added column: {table_name}.{column_name}")

    else:
        print(f"Column exists: {table_name}.{column_name}")