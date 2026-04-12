# run_server.py
from smart_exam_system.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()