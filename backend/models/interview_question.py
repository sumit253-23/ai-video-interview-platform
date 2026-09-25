from datetime import datetime

from extensions import db


class InterviewQuestion(db.Model):
    __tablename__ = "interview_questions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    interview_id = db.Column(
        db.Integer,
        db.ForeignKey("interviews.id"),
        nullable=False
    )

    question = db.Column(
        db.Text,
        nullable=False
    )

    topic = db.Column(
        db.String(255),
        nullable=True
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    difficulty = db.Column(
        db.String(50),
        nullable=True
    )

    question_order = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    interview = db.relationship(
        "Interview",
        foreign_keys=[interview_id],
        backref=db.backref(
            "questions",
            lazy=True
        )
    )

    answers = db.relationship(
        "InterviewAnswer",
        foreign_keys="InterviewAnswer.question_id",
        back_populates="question_reference",
        lazy=True
    )