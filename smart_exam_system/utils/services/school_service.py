from smart_exam_system.models.school import SchoolModel
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