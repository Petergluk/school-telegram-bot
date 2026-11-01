from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Lesson, Homework, Grade

router = APIRouter(prefix="/school", tags=["school"])


@router.get("/schedule")
async def get_schedule(db: Session = Depends(get_db)):
    lessons = db.query(Lesson).all()
    return [
        {
            "id": lesson.id,
            "class_name": lesson.class_name,
            "day": lesson.day,
            "time": lesson.time,
            "subject": lesson.subject,
        }
        for lesson in lessons
    ]


@router.get("/homework")
async def get_homework(db: Session = Depends(get_db)):
    items = db.query(Homework).all()
    return [
        {
            "id": item.id,
            "class_name": item.class_name,
            "subject": item.subject,
            "title": item.title,
            "description": item.description,
            "due_date": item.due_date,
        }
        for item in items
    ]


@router.get("/grades")
async def get_grades(db: Session = Depends(get_db)):
    items = db.query(Grade).all()
    return [
        {
            "id": item.id,
            "student_id": item.student_id,
            "teacher_id": item.teacher_id,
            "subject": item.subject,
            "value": item.value,
        }
        for item in items
    ]
