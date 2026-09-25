from datetime import datetime

from extensions import db


class InterviewAnswer(db.Model):
    __tablename__ = "interview_answers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    interview_id = db.Column(
        db.Integer,
        db.ForeignKey("interviews.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("interview_questions.id"),
        nullable=True
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

    answer = db.Column(
        db.Text,
        nullable=True
    )

    score = db.Column(
        db.Float,
        nullable=True
    )

    technical_accuracy = db.Column(
        db.Text,
        nullable=True
    )

    relevance = db.Column(
        db.Text,
        nullable=True
    )

    completeness = db.Column(
        db.Text,
        nullable=True
    )

    feedback = db.Column(
        db.Text,
        nullable=True
    )

    strengths = db.Column(
        db.JSON,
        nullable=True
    )

    improvements = db.Column(
        db.JSON,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    answered_at = db.Column(
        db.DateTime,
        nullable=True
    )

    interview = db.relationship(
        "Interview",
        foreign_keys=[interview_id],
        back_populates="answers"
    )

    question_reference = db.relationship(
        "InterviewQuestion",
        foreign_keys=[question_id],
        back_populates="answers"
    )