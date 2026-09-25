from datetime import datetime

from extensions import db


class JobMatch(db.Model):
    __tablename__ = "job_matches"

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
        nullable=False
    )

    match_score = db.Column(
        db.Float,
        nullable=True
    )

    matched_skills = db.Column(
        db.JSON,
        nullable=True
    )

    missing_skills = db.Column(
        db.JSON,
        nullable=True
    )

    strengths = db.Column(
        db.JSON,
        nullable=True
    )

    recommendations = db.Column(
        db.JSON,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "job_matches",
            lazy=True
        )
    )

    resume = db.relationship(
        "Resume",
        backref=db.backref(
            "job_matches",
            lazy=True
        )
    )