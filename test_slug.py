from run import app
from smart_exam_system.extensions import db
from smart_exam_system.models.school import SchoolModel
from smart_exam_system.utils.helpers import generate_slug

with app.app_context():

    schools = SchoolModel.query.all()

    for school in schools:
        if not school.slug:
            school.slug = generate_slug(school.name)
            print(f"Updated: {school.name} -> {school.slug}")

    db.session.commit()

    print("✅ All school slugs updated")