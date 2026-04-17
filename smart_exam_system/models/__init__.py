# smart_exam_system/models/__init__.py

from smart_exam_system.models.user import UserModel
from smart_exam_system.models.school import School
from smart_exam_system.models.exam import Exam
from smart_exam_system.models.question import QuestionModel
from smart_exam_system.models.attempt import Attempt
from smart_exam_system.models.result import Result
from smart_exam_system.models.answer import StudentAnswerModel
from smart_exam_system.models.democontact import DemoRequest, ContactMessage


__all__ = [
    "UserModel",
    "School",
    "Exam",
    "QuestionModel",
    "Attempt",
    "Result",
    "StudentAnswerModel",
    "DemoRequest",
    "ContactMessage"
    
]