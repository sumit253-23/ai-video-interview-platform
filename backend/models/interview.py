from datetime import datetime

from extensions import db


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    resume_id = db.Column(
        db.Integer,
        db.ForeignKey("resumes.id"),
        nullable=False
    )

    job_description = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active"
    )

    current_stage = db.Column(
        db.String(50),
        nullable=False,
        default="candidate_introduction"
    )

    current_question_id = db.Column(
        db.Integer,
        db.ForeignKey("interview_questions.id"),
        nullable=True
    )

    candidate_introduction = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "interviews",
            lazy=True
        )
    )

    resume = db.relationship(
        "Resume",
        backref=db.backref(
            "interviews",
            lazy=True
        )
    )

    current_question = db.relationship(
        "InterviewQuestion",
        foreign_keys=[current_question_id]
    )

    answers = db.relationship(
        "InterviewAnswer",
        foreign_keys="InterviewAnswer.interview_id",
        back_populates="interview",
        lazy=True
    )