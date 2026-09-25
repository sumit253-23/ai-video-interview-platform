import os
from uuid import uuid4

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pypdf import PdfReader

from extensions import db
from models.resume import Resume
from models.resume_analysis import ResumeAnalysis
from services.resume_analysis_service import analyze_resume
resume_bp = Blueprint(
    "resume",
    __name__,
    url_prefix="/api/resume"
)


UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "uploads",
    "resumes"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)



    


@resume_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_resume():
    print("CONTENT TYPE:", request.content_type)
    print("FILES:", request.files)
    print("FORM:", request.form)

    user_id = int(get_jwt_identity())

    if "resume" not in request.files:
        return {
            "status": "error",
            "message": "Resume PDF is required"
        }, 400

    file = request.files["resume"]

    if file.filename == "":
        return {
            "status": "error",
            "message": "No file selected"
        }, 400

    if not file.filename.lower().endswith(".pdf"):
        return {
            "status": "error",
            "message": "Only PDF files are allowed"
        }, 400

    unique_filename = f"{uuid4().hex}.pdf"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    file.save(file_path)

    try:
        reader = PdfReader(file_path)

        extracted_text = ""

        for page in reader.pages:
            text = page.extract_text()

            if text:
                extracted_text += text + "\n"

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Could not read the PDF file"
        }, 400

    resume = Resume(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        extracted_text=extracted_text.strip()
    )

    db.session.add(resume)
    db.session.commit()

    return {
        "status": "success",
        "message": "Resume uploaded successfully",
        "resume": {
            "id": resume.id,
            "filename": resume.filename,
            "text_length": len(extracted_text.strip())
        }
    }, 201


@resume_bp.route("/<int:resume_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_uploaded_resume(resume_id):

    user_id = int(get_jwt_identity())

    resume = Resume.query.filter_by(
        id=resume_id,
        user_id=user_id
    ).first()

    if not resume:
        return {
            "status": "error",
            "message": "Resume not found"
        }, 404

    if not resume.extracted_text:
        return {
            "status": "error",
            "message": "Resume text is empty"
        }, 400

    try:
        analysis_data = analyze_resume(
            resume.extracted_text
        )

        analysis = ResumeAnalysis.query.filter_by(
            resume_id=resume.id
        ).first()

        if analysis:
            analysis.summary = analysis_data.get("summary", "")
            analysis.skills = analysis_data.get("skills", [])
            analysis.programming_languages = analysis_data.get(
                "programming_languages", []
            )
            analysis.frameworks = analysis_data.get(
                "frameworks", []
            )
            analysis.projects = analysis_data.get(
                "projects", []
            )
            analysis.cs_fundamentals = analysis_data.get(
                "cs_fundamentals", []
            )
            analysis.dsa_topics = analysis_data.get(
                "dsa_topics", []
            )

        else:
            analysis = ResumeAnalysis(
                resume_id=resume.id,
                summary=analysis_data.get("summary", ""),
                skills=analysis_data.get("skills", []),
                programming_languages=analysis_data.get(
                    "programming_languages", []
                ),
                frameworks=analysis_data.get(
                    "frameworks", []
                ),
                projects=analysis_data.get(
                    "projects", []
                ),
                cs_fundamentals=analysis_data.get(
                    "cs_fundamentals", []
                ),
                dsa_topics=analysis_data.get(
                    "dsa_topics", []
                )
            )

            db.session.add(analysis)

        db.session.commit()

        return {
            "status": "success",
            "message": "Resume analyzed successfully",
            "analysis": analysis_data
        }, 200

    except Exception as e:
        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 500