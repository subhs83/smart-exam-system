from app import create_app
from extensions import db
from models.user import UserModel, User

# ✅ create app FIRST
app = create_app()

# ✅ then use it
with app.app_context():
    # test SQLAlchemy
    users = UserModel.query.all()
    print(users)

    # test new function
    teachers = User.get_teachers_by_school_sa(1)
    print(teachers)