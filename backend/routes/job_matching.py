from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.resume import Resume
from models.resume_analysis import ResumeAnalysis
from models.job_match import JobMatch
from services.job_matching_service import match_resume_with_job


job_matching_bp = Blueprint(
    "job_matching",
    __name__,
    url_prefix="/api/job-matching"
)


@job_matching_bp.route("/", methods=["POST"])
@jwt_required()
def create_job_match():
    user_id = int(get_jwt_identity())

    data = request.get_json(silent=True) or {}

    resume_id = data.get("resume_id")
    job_description = data.get("job_description")

    if not resume_id:
        return {
            "status": "error",
            "message": "resume_id is required"
        }, 400

    if not job_description or not job_description.strip():
        return {
            "status": "error",
            "message": "Job description is required"
        }, 400

    try:
        resume_id = int(resume_id)
    except (TypeError, ValueError):
        return {
            "status": "error",
            "message": "Invalid resume_id"
        }, 400

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=user_id
    ).first()

    if not resume:
        return {
            "status": "error",
            "message": "Resume not found"
        }, 404

    resume_analysis = ResumeAnalysis.query.filter_by(
        resume_id=resume.id
    ).first()

    if not resume_analysis:
        return {
            "status": "error",
            "message": "Please analyze your resume before matching it with a job"
        }, 400

    try:
        match_result = match_resume_with_job(
            resume_analysis,
            job_description.strip()
        )

        job_match = JobMatch(
            user_id=user_id,
            resume_id=resume.id,
            job_description=job_description.strip(),
            match_score=match_result["match_score"],
            matched_skills=match_result["matched_skills"],
            missing_skills=match_result["missing_skills"],
            strengths=match_result["strengths"],
            recommendations=match_result["recommendations"]
        )

        db.session.add(job_match)
        db.session.commit()

        return {
            "status": "success",
            "message": "Job matching completed successfully",
            "job_match": {
                "id": job_match.id,
                "resume_id": job_match.resume_id,
                "match_score": job_match.match_score,
                "matched_skills": job_match.matched_skills,
                "missing_skills": job_match.missing_skills,
                "strengths": job_match.strengths,
                "recommendations": job_match.recommendations
            }
        }, 201

    except Exception as error:
        db.session.rollback()
        print("JOB MATCHING ERROR:", repr(error))
        raise

      