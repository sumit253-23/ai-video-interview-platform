from datetime import datetime

from extensions import db


class ResumeAnalysis(db.Model):
    __tablename__ = "resume_analysis"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    resume_id = db.Column(
        db.Integer,
        db.ForeignKey("resumes.id"),
        nullable=False,
        unique=True
    )

    summary = db.Column(
        db.Text,
        nullable=True
    )

    skills = db.Column(
        db.JSON,
        nullable=True
    )

    programming_languages = db.Column(
        db.JSON,
        nullable=True
    )

    frameworks = db.Column(
        db.JSON,
        nullable=True
    )

    projects = db.Column(
        db.JSON,
        nullable=True
    )

    cs_fundamentals = db.Column(
        db.JSON,
        nullable=True
    )

    dsa_topics = db.Column(
        db.JSON,
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

    resume = db.relationship(
        "Resume",
        backref=db.backref(
            "analysis",
            uselist=False
        )
    )