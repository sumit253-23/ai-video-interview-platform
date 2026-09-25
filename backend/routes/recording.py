import os
from uuid import uuid4

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.interview import Interview
from models.interview_question import InterviewQuestion
from models.interview_recording import InterviewRecording
from models.resume import Resume
from models.resume_analysis import ResumeAnalysis

from services.interview_answer_service import process_interview_answer
from services.interview_flow_service import (
    generate_next_question_for_interview
)
from services.question_service import (
    generate_first_question_after_introduction
)


recording_bp = Blueprint(
    "recording",
    __name__,
    url_prefix="/api/recordings"
)


UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "uploads",
    "recordings"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# UPLOAD CANDIDATE INTRODUCTION
# =========================================================

@recording_bp.route("/introduction", methods=["POST"])
@jwt_required()
def upload_introduction():

    user_id = int(get_jwt_identity())

    interview_id = request.form.get("interview_id")
    duration = request.form.get("duration")

    # -----------------------------------------------------
    # Validate interview_id
    # -----------------------------------------------------

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    try:
        interview_id = int(interview_id)

    except ValueError:
        return {
            "status": "error",
            "message": "Invalid interview_id"
        }, 400

    # -----------------------------------------------------
    # Validate recording
    # -----------------------------------------------------

    if "recording" not in request.files:
        return {
            "status": "error",
            "message": "Recording file is required"
        }, 400

    recording_file = request.files["recording"]

    if recording_file.filename == "":
        return {
            "status": "error",
            "message": "No recording selected"
        }, 400

    # -----------------------------------------------------
    # Verify interview ownership
    # -----------------------------------------------------

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    # -----------------------------------------------------
    # Validate interview state
    # -----------------------------------------------------

    if interview.status != "active":
        return {
            "status": "error",
            "message": "Interview is not active"
        }, 400

    if interview.current_stage != "candidate_introduction":
        return {
            "status": "error",
            "message": "Candidate introduction has already been submitted"
        }, 400

    # -----------------------------------------------------
    # Validate file extension
    # -----------------------------------------------------

    original_filename = recording_file.filename

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    allowed_extensions = {
        ".webm",
        ".mp4",
        ".wav",
        ".mp3",
        ".ogg",
        ".m4a"
    }

    if extension not in allowed_extensions:
        return {
            "status": "error",
            "message": "Unsupported recording format"
        }, 400

    # -----------------------------------------------------
    # Generate unique filename
    # -----------------------------------------------------

    unique_filename = f"{uuid4().hex}{extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    # -----------------------------------------------------
    # Save recording
    # -----------------------------------------------------

    try:
        recording_file.save(file_path)

    except Exception:
        return {
            "status": "error",
            "message": "Failed to save introduction recording"
        }, 500

    # -----------------------------------------------------
    # Detect file type
    # -----------------------------------------------------

    content_type = recording_file.content_type or "unknown"

    if content_type.startswith("video"):

        file_type = "video"

    elif content_type.startswith("audio"):

        file_type = "audio"

    else:

        if extension in {
            ".wav",
            ".mp3",
            ".ogg",
            ".m4a"
        }:
            file_type = "audio"

        elif extension in {
            ".webm",
            ".mp4"
        }:
            file_type = "video"

        else:
            file_type = "unknown"

    # -----------------------------------------------------
    # Validate detected type
    # -----------------------------------------------------

    if file_type == "unknown":

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Could not determine recording type"
        }, 400

    # -----------------------------------------------------
    # Convert duration
    # -----------------------------------------------------

    recording_duration = None

    if duration:

        try:
            recording_duration = float(duration)

        except ValueError:
            recording_duration = None

    # -----------------------------------------------------
    # Process recording
    #
    # Video → Audio → Transcript
    # Audio → Transcript
    # -----------------------------------------------------

    try:

        from services.recording_processing_service import (
            process_recording
        )

        processing_result = process_recording(
            recording_path=file_path,
            file_type=file_type
        )

        transcript = processing_result.get(
            "transcript",
            ""
        )

        if not transcript:
            raise ValueError(
                "Could not generate introduction transcript"
            )

    except Exception as e:

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Failed to process introduction recording",
            "processing_error": str(e)
        }, 500

    # -----------------------------------------------------
    # Get resume
    # -----------------------------------------------------

    resume = Resume.query.filter_by(
        id=interview.resume_id,
        user_id=user_id
    ).first()

    if not resume:
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Resume not found"
        }, 404

    # -----------------------------------------------------
    # Get resume analysis
    # -----------------------------------------------------

    analysis = ResumeAnalysis.query.filter_by(
        resume_id=resume.id
    ).first()

    if not analysis:
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Resume analysis not found"
        }, 400

    resume_analysis = {
        "summary": analysis.summary,
        "skills": analysis.skills or [],
        "programming_languages": analysis.programming_languages or [],
        "frameworks": analysis.frameworks or [],
        "projects": analysis.projects or [],
        "cs_fundamentals": analysis.cs_fundamentals or [],
        "dsa_topics": analysis.dsa_topics or []
    }

    # -----------------------------------------------------
    # Generate first technical question
    # -----------------------------------------------------

    try:

        first_question = generate_first_question_after_introduction(
            resume_analysis=resume_analysis,
            candidate_introduction=transcript,
            job_description=interview.job_description
        )

        generated_question = first_question.get(
            "question"
        )

        if not generated_question:
            raise ValueError(
                "AI did not generate the first technical question"
            )

        # -------------------------------------------------
        # Save candidate introduction
        # -------------------------------------------------

        interview.candidate_introduction = transcript
        interview.current_stage = "technical_interview"

        # -------------------------------------------------
        # Create first technical question
        # -------------------------------------------------

        interview_question = InterviewQuestion(
            interview_id=interview.id,
            question=generated_question,
            topic=first_question.get("topic"),
            category=first_question.get("category"),
            difficulty=first_question.get("difficulty"),
            question_order=1
        )

        db.session.add(interview_question)

        db.session.flush()

        # -------------------------------------------------
        # Set current question
        # -------------------------------------------------

        interview.current_question_id = interview_question.id

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Failed to generate first interview question",
            "processing_error": str(e)
        }, 500

    # -----------------------------------------------------
    # Return response
    # -----------------------------------------------------

    return {
        "status": "success",
        "message": (
            "Introduction recorded, "
            "transcribed, and processed successfully"
        ),
        "interview": {
            "id": interview.id,
            "stage": interview.current_stage,
            "status": interview.status
        },
        "transcript": transcript,
        "first_question": {
            "id": interview_question.id,
            "interview_id": interview_question.interview_id,
            "question": interview_question.question,
            "topic": interview_question.topic,
            "category": interview_question.category,
            "difficulty": interview_question.difficulty,
            "question_order": interview_question.question_order
        }
    }, 201

# =========================================================
# UPLOAD RECORDING
# =========================================================

@recording_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_recording():

    user_id = int(get_jwt_identity())

    interview_id = request.form.get("interview_id")
    question_id = request.form.get("question_id")
    duration = request.form.get("duration")

    # -----------------------------------------------------
    # Validate interview_id
    # -----------------------------------------------------

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    try:
        interview_id = int(interview_id)

    except ValueError:
        return {
            "status": "error",
            "message": "Invalid interview_id"
        }, 400

    # -----------------------------------------------------
    # Validate recording file
    # -----------------------------------------------------

    if "recording" not in request.files:
        return {
            "status": "error",
            "message": "Recording file is required"
        }, 400

    recording_file = request.files["recording"]

    if recording_file.filename == "":
        return {
            "status": "error",
            "message": "No recording selected"
        }, 400

    # -----------------------------------------------------
    # Verify interview ownership
    # -----------------------------------------------------

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    # -----------------------------------------------------
    # Interview must be active
    # -----------------------------------------------------

    if interview.status != "active":
        return {
            "status": "error",
            "message": "Interview is not active"
        }, 400

    # -----------------------------------------------------
    # Current question must exist
    # -----------------------------------------------------

    if not interview.current_question_id:
        return {
            "status": "error",
            "message": "No current question is available"
        }, 400

    # -----------------------------------------------------
    # Get current question
    # -----------------------------------------------------

    current_question = InterviewQuestion.query.filter_by(
        id=interview.current_question_id,
        interview_id=interview.id
    ).first()

    if not current_question:
        return {
            "status": "error",
            "message": "Current interview question not found"
        }, 404

    # -----------------------------------------------------
    # Validate question_id if supplied
    # -----------------------------------------------------

    if question_id:

        try:
            requested_question_id = int(question_id)

        except ValueError:
            return {
                "status": "error",
                "message": "Invalid question_id"
            }, 400

        if requested_question_id != current_question.id:
            return {
                "status": "error",
                "message": "Recording must belong to the current question"
            }, 400

    question = current_question

    # -----------------------------------------------------
    # Prevent duplicate recording
    # -----------------------------------------------------

    existing_recording = InterviewRecording.query.filter_by(
        interview_id=interview.id,
        question_id=current_question.id
    ).first()

    if existing_recording:
        return {
            "status": "error",
            "message": "A recording already exists for this question",
            "recording": {
                "id": existing_recording.id,
                "question_id": existing_recording.question_id
            }
        }, 409

    # -----------------------------------------------------
    # Validate file extension
    # -----------------------------------------------------

    original_filename = recording_file.filename

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    allowed_extensions = {
        ".webm",
        ".mp4",
        ".wav",
        ".mp3",
        ".ogg",
        ".m4a"
    }

    if extension not in allowed_extensions:
        return {
            "status": "error",
            "message": "Unsupported recording format"
        }, 400

    # -----------------------------------------------------
    # Generate unique filename
    # -----------------------------------------------------

    unique_filename = f"{uuid4().hex}{extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    # -----------------------------------------------------
    # Save physical recording
    # -----------------------------------------------------

    try:
        recording_file.save(file_path)

    except Exception:
        return {
            "status": "error",
            "message": "Failed to save recording"
        }, 500

    # -----------------------------------------------------
    # Detect file type
    # -----------------------------------------------------

    content_type = recording_file.content_type or "unknown"

    if content_type.startswith("video"):

        file_type = "video"

    elif content_type.startswith("audio"):

        file_type = "audio"

    else:

        if extension in {
            ".wav",
            ".mp3",
            ".ogg",
            ".m4a"
        }:
            file_type = "audio"

        elif extension in {
            ".webm",
            ".mp4"
        }:
            file_type = "video"

        else:
            file_type = "unknown"

    # -----------------------------------------------------
    # Validate detected type
    # -----------------------------------------------------

    if file_type == "unknown":

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Could not determine recording type"
        }, 400

    # -----------------------------------------------------
    # Convert duration
    # -----------------------------------------------------

    recording_duration = None

    if duration:

        try:
            recording_duration = float(duration)

        except ValueError:
            recording_duration = None

    # -----------------------------------------------------
    # Create database record
    # -----------------------------------------------------

    recording = InterviewRecording(
        interview_id=interview.id,
        question_id=question.id,
        filename=original_filename,
        file_path=file_path,
        file_type=file_type,
        duration=recording_duration
    )

    try:
        db.session.add(recording)
        db.session.commit()

    except Exception:

        db.session.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "error",
            "message": "Failed to save recording information"
        }, 500

    # -----------------------------------------------------
    # Process recording
    #
    # Video → Audio → Transcript
    # Audio → Transcript
    # -----------------------------------------------------

    try:

        from services.recording_processing_service import (
            process_recording
        )

        processing_result = process_recording(
            recording_path=file_path,
            file_type=file_type
        )

        transcript = processing_result.get(
            "transcript",
            ""
        )

        # -------------------------------------------------
        # Validate transcript
        # -------------------------------------------------

        if not transcript.strip():

            return {
                "status": "success",
                "message": (
                    "Recording uploaded but "
                    "no transcript was generated"
                ),
                "recording": {
                    "id": recording.id,
                    "interview_id": recording.interview_id,
                    "question_id": recording.question_id,
                    "filename": recording.filename,
                    "file_type": recording.file_type,
                    "duration": recording.duration
                },
                "transcript": transcript
            }, 201

        # -------------------------------------------------
        # Save answer and generate AI evaluation
        # -------------------------------------------------

        answer_result = process_interview_answer(
            interview=interview,
            interview_question=current_question,
            answer_text=transcript
        )

        answer = answer_result["answer"]
        evaluation = answer_result["evaluation"]
        # -------------------------------------------------
        # Generate next interview question
        # -------------------------------------------------

        next_question = generate_next_question_for_interview( 
              interview=interview,
              user_id=user_id
          )



    except Exception as e:

        # Recording itself is already safely stored.
        # Processing failure should not delete the recording.

        return {
            "status": "success",
            "message": (
                "Recording uploaded, "
                "but processing failed"
            ),
            "recording": {
                "id": recording.id,
                "interview_id": recording.interview_id,
                "question_id": recording.question_id,
                "filename": recording.filename,
                "file_type": recording.file_type,
                "duration": recording.duration
            },
            "transcript": "",
            "processing_error": str(e)
        }, 201

    # -----------------------------------------------------
    # Successful upload + transcription + evaluation
    # -----------------------------------------------------

    return {
        "status": "success",
        "message": (
            "Recording uploaded, transcribed, "
            "and evaluated successfully"
        ),
        "recording": {
            "id": recording.id,
            "interview_id": recording.interview_id,
            "question_id": recording.question_id,
            "filename": recording.filename,
            "file_type": recording.file_type,
            "duration": recording.duration
        },
        "transcript": transcript,
        "answer": {
            "id": answer.id,
            "question_id": answer.question_id,
            "answer": answer.answer,
            "answered_at": (
                answer.answered_at.isoformat()
                if answer.answered_at
                else None
            )
        },
        "evaluation": evaluation,
        "next_question": {
            "id": next_question.id,
             "interview_id": next_question.interview_id,
             "question": next_question.question,
             "topic": next_question.topic,
             "category": next_question.category,
             "difficulty": next_question.difficulty,
              "question_order": next_question.question_order
            
        }
    }, 201

# =========================================================
# GET ALL RECORDINGS OF AN INTERVIEW
# =========================================================

@recording_bp.route(
    "/interview/<int:interview_id>",
    methods=["GET"]
)
@jwt_required()
def get_interview_recordings(interview_id):

    user_id = int(get_jwt_identity())

    # -----------------------------------------------------
    # Verify interview belongs to logged-in user
    # -----------------------------------------------------

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    # -----------------------------------------------------
    # Get recordings
    # -----------------------------------------------------

    recordings = InterviewRecording.query.filter_by(
        interview_id=interview.id
    ).order_by(
        InterviewRecording.created_at.asc()
    ).all()

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "status": "success",
        "interview_id": interview.id,
        "recordings": [
            {
                "id": recording.id,
                "question_id": recording.question_id,
                "filename": recording.filename,
                "file_type": recording.file_type,
                "duration": recording.duration,
                "file_path": recording.file_path,
                "created_at": recording.created_at.isoformat()
            }
            for recording in recordings
        ]
    }, 200


# =========================================================
# GET SINGLE RECORDING
# =========================================================

@recording_bp.route(
    "/<int:recording_id>",
    methods=["GET"]
)
@jwt_required()
def get_recording(recording_id):

    user_id = int(get_jwt_identity())

    # -----------------------------------------------------
    # Find recording
    # -----------------------------------------------------

    recording = InterviewRecording.query.get(recording_id)

    if not recording:
        return {
            "status": "error",
            "message": "Recording not found"
        }, 404

    # -----------------------------------------------------
    # Verify ownership through interview
    # -----------------------------------------------------

    interview = Interview.query.filter_by(
        id=recording.interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Recording not found"
        }, 404

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "status": "success",
        "recording": {
            "id": recording.id,
            "interview_id": recording.interview_id,
            "question_id": recording.question_id,
            "filename": recording.filename,
            "file_type": recording.file_type,
            "duration": recording.duration,
            "file_path": recording.file_path,
            "created_at": recording.created_at.isoformat()
        }
    }, 200