import click
from smart_exam_system import create_app
from smart_exam_system.extensions import db
from smart_exam_system.utils.init_data import create_default_super_admin

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