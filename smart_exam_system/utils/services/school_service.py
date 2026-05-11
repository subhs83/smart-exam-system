from smart_exam_system.models.school import SchoolModel
from smart_exam_system.models.user import UserModel
from smart_exam_system.models.exam import ExamModel

from smart_exam_system.models.attempt import AttemptModel
from datetime import datetime
from smart_exam_system.utils.helpers import generate_slug



def generate_unique_school_slug(name, school_id=None):

    slug = generate_slug(name)

    existing_slug = SchoolModel.query.filter(
        SchoolModel.slug == slug
    )

    if school_id:
        existing_slug = existing_slug.filter(
            SchoolModel.id != school_id
        )

    existing_slug = existing_slug.first()

    if existing_slug:

        if school_id:
            slug = f"{slug}-{school_id}"
        else:
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    return slug

    

def get_school_or_404(school_slug):

    return SchoolModel.query.filter_by(
        slug=school_slug
    ).first_or_404()



def build_school_dashboard_data(school_id):
    return {
        "total_teachers": UserModel.count_teachers_by_school(school_id),
        "total_exams": ExamModel.count_by_school(school_id),
        "total_attempts": AttemptModel.count_by_school(school_id),
        "exams": ExamModel.get_exams_by_school(school_id),
    }




def build_teacher_exam_list(teacher_id):

    exams = ExamModel.get_exams_by_teacher(teacher_id)

    exam_list = []

    for exam in exams:
        exam_list.append({
            "id": exam.id,
            "title": exam.title,
            "student_attempts": AttemptModel.get_attempt_count(exam.id)
        })

    return exam_list