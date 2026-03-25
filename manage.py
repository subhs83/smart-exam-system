# manage.py
import click
from smart_exam_system.app import create_app
from smart_exam_system.extensions import db
from smart_exam_system.utils.init_data import create_default_super_admin
# Optional: seed_test_data for demo/test data
# from smart_exam_system.utils.seed_data import seed_test_data

app = create_app()

# -------------------------------
# CLI Commands
# -------------------------------

@app.cli.command("runserver")
def runserver():
    """Run the Flask development server."""
    app.run(debug=True)


@app.cli.command("create-admin")
def create_admin():
    """Create default super admin if not exists."""
    with app.app_context():
        create_default_super_admin()
        click.echo("✅ Super admin ensured.")


# Optional: seed demo/test data
# @app.cli.command("seed-data")
# def seed_data():
#     """Seed test/demo data."""
#     with app.app_context():
#         seed_test_data()
#         click.echo("✅ Test data seeded!")