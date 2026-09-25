from datetime import datetime

from extensions import db


class InterviewRecording(db.Model):
    __tablename__ = "interview_recordings"

    id = db.Column(db.Integer, primary_key=True)

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

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_type = db.Column(
        db.String(50),
        nullable=False
    )

    duration = db.Column(
        db.Float,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    interview = db.relationship(
        "Interview",
        backref=db.backref(
            "recordings",
            lazy=True
        )
    )

    question = db.relationship(
        "InterviewQuestion",
        backref=db.backref(
            "recordings",
            lazy=True
        )
    )