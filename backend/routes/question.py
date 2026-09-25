from flask import Blueprint, request

from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db

from models.resume import Resume
from models.resume_analysis import ResumeAnalysis
from models.interview import Interview
from models.interview_answer import InterviewAnswer
from models.interview_question import InterviewQuestion

from services.evaluation_service import evaluate_answer

from services.question_service import (
    generate_interview_question,
    generate_interview_introduction,
    generate_first_question_after_introduction,
    generate_next_interview_question
)


question_bp = Blueprint(
    "question",
    __name__,
    url_prefix="/api/questions"
)

# ============================================================
# GENERATE QUESTION
# ============================================================

@question_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_question():

    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    resume_id = data.get("resume_id")
    job_description = data.get("job_description")

    if not resume_id:
        return {
            "status": "error",
            "message": "resume_id is required"
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

    analysis = ResumeAnalysis.query.filter_by(
        resume_id=resume.id
    ).first()

    if not analysis:
        return {
            "status": "error",
            "message": "Resume analysis not found. Analyze the resume first."
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

    try:

        question = generate_interview_question(
            resume_analysis=resume_analysis,
            job_description=job_description
        )

        return {
            "status": "success",
            "question": question
        }, 200

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }, 500


# ============================================================
# START INTERVIEW
# ============================================================

@question_bp.route("/start", methods=["POST"])
@jwt_required()
def start_interview():

    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    resume_id = data.get("resume_id")
    job_description = data.get("job_description")

    if not resume_id:
        return {
            "status": "error",
            "message": "resume_id is required"
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

    analysis = ResumeAnalysis.query.filter_by(
        resume_id=resume.id
    ).first()

    if not analysis:
        return {
            "status": "error",
            "message": "Resume analysis not found. Analyze the resume first."
        }, 400

    try:

        interview = Interview(
            user_id=user_id,
            resume_id=resume.id,
            job_description=job_description,
            status="active",
            current_stage="candidate_introduction"
        )

        db.session.add(interview)
        db.session.commit()

        introduction = generate_interview_introduction()

        return {
            "status": "success",
            "interview": {
                "id": interview.id,
                "introduction": introduction,
                "stage": interview.current_stage,
                "status": interview.status
            }
        }, 201

    except Exception as e:

        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 500



@question_bp.route("/introduction", methods=["POST"])
@jwt_required()
def submit_introduction():

    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    interview_id = data.get("interview_id")
    candidate_introduction = data.get("introduction")

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    if not candidate_introduction:
        return {
            "status": "error",
            "message": "Candidate introduction is required"
        }, 400

    # --------------------------------------------------------
    # Find interview
    # --------------------------------------------------------

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

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

    # --------------------------------------------------------
    # Get resume
    # --------------------------------------------------------

    resume = Resume.query.filter_by(
        id=interview.resume_id,
        user_id=user_id
    ).first()

    if not resume:
        return {
            "status": "error",
            "message": "Resume not found"
        }, 404

    # --------------------------------------------------------
    # Get resume analysis
    # --------------------------------------------------------

    analysis = ResumeAnalysis.query.filter_by(
        resume_id=resume.id
    ).first()

    if not analysis:
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

    try:

        # ----------------------------------------------------
        # Generate first technical question
        # ----------------------------------------------------

        first_question = generate_first_question_after_introduction(
            resume_analysis=resume_analysis,
            candidate_introduction=candidate_introduction,
            job_description=interview.job_description
        )

        generated_question = first_question.get("question")

        if not generated_question:
            raise ValueError(
                "AI did not generate the first technical question"
            )

        # ----------------------------------------------------
        # Save candidate introduction
        # ----------------------------------------------------

        interview.candidate_introduction = candidate_introduction
        interview.current_stage = "technical_interview"

        # ----------------------------------------------------
        # Save first technical question
        # ----------------------------------------------------

        interview_question = InterviewQuestion(
            interview_id=interview.id,
            question=generated_question,
            topic=first_question.get("topic"),
            category=first_question.get("category"),
            difficulty=first_question.get("difficulty"),
            question_order=1
        )

        db.session.add(interview_question)

        # ----------------------------------------------------
        # Generate question ID before commit
        # ----------------------------------------------------

        db.session.flush()

        # ----------------------------------------------------
        # Set current/active question
        # ----------------------------------------------------

        interview.current_question_id = interview_question.id

        # ----------------------------------------------------
        # Commit everything
        # ----------------------------------------------------

        db.session.commit()

        # ----------------------------------------------------
        # Return response
        # ----------------------------------------------------

        return {
            "status": "success",
            "stage": interview.current_stage,
            "current_question_id": interview.current_question_id,
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

    except Exception as e:

        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 500

# ============================================================
# SUBMIT INTERVIEW ANSWER
# ============================================================

@question_bp.route("/answer", methods=["POST"])
@jwt_required()
def submit_answer():

    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    interview_id = data.get("interview_id")
    question_id = data.get("question_id")
    answer = data.get("answer")

    # --------------------------------------------------------
    # Validate request
    # --------------------------------------------------------

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    if not question_id:
        return {
            "status": "error",
            "message": "question_id is required"
        }, 400

    if not answer or not answer.strip():
        return {
            "status": "error",
            "message": "answer is required"
        }, 400

    # --------------------------------------------------------
    # Find interview
    # --------------------------------------------------------

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    if interview.status != "active":
        return {
            "status": "error",
            "message": "Interview is not active"
        }, 400

    if interview.current_stage != "technical_interview":
        return {
            "status": "error",
            "message": "Interview is not in technical stage"
        }, 400

    # --------------------------------------------------------
    # Check current/active question
    # --------------------------------------------------------

    if not interview.current_question_id:
        return {
            "status": "error",
            "message": "No active question found"
        }, 400

    if int(question_id) != interview.current_question_id:
        return {
            "status": "error",
            "message": "This is not the current active question"
        }, 409

    # --------------------------------------------------------
    # Find question
    # --------------------------------------------------------

    interview_question = InterviewQuestion.query.filter_by(
        id=question_id,
        interview_id=interview.id
    ).first()

    if not interview_question:
        return {
            "status": "error",
            "message": "Question not found for this interview"
        }, 404

    try:

        # ----------------------------------------------------
        # Prevent duplicate answer
        # ----------------------------------------------------

        existing_answer = InterviewAnswer.query.filter_by(
            question_id=interview_question.id
        ).first()

        if existing_answer:
            return {
                "status": "error",
                "message": "This question has already been answered"
            }, 409

        # ----------------------------------------------------
        # Create answer
        # ----------------------------------------------------

        interview_answer = InterviewAnswer(
            interview_id=interview.id,
            question_id=interview_question.id,
            question=interview_question.question,
            topic=interview_question.topic,
            category=interview_question.category,
            difficulty=interview_question.difficulty,
            answer=answer.strip()
        )

        db.session.add(interview_answer)

        # Get answer ID before evaluation
        db.session.flush()

        # ----------------------------------------------------
        # AI evaluation
        # ----------------------------------------------------

        evaluation = evaluate_answer(
            question=interview_question.question,
            answer=answer.strip(),
            topic=interview_question.topic,
            category=interview_question.category,
            difficulty=interview_question.difficulty
        )

        # ----------------------------------------------------
        # Save evaluation
        # ----------------------------------------------------

        interview_answer.score = evaluation.get("score")

        interview_answer.technical_accuracy = evaluation.get(
            "technical_accuracy"
        )

        interview_answer.relevance = evaluation.get(
            "relevance"
        )

        interview_answer.completeness = evaluation.get(
            "completeness"
        )

        interview_answer.feedback = evaluation.get(
            "feedback"
        )

        interview_answer.strengths = evaluation.get(
            "strengths",
            []
        )

        interview_answer.improvements = evaluation.get(
            "improvements",
            []
        )

        interview_answer.answered_at = db.func.now()

        db.session.commit()

        # ----------------------------------------------------
        # Return answer + evaluation
        # ----------------------------------------------------

        return {
            "status": "success",
            "message": "Answer evaluated successfully",

            "answer": {
                "id": interview_answer.id,
                "interview_id": interview_answer.interview_id,
                "question_id": interview_answer.question_id,
                "question": interview_answer.question,
                "answer": interview_answer.answer
            },

            "evaluation": {
                "score": interview_answer.score,
                "technical_accuracy": interview_answer.technical_accuracy,
                "relevance": interview_answer.relevance,
                "completeness": interview_answer.completeness,
                "feedback": interview_answer.feedback,
                "strengths": interview_answer.strengths,
                "improvements": interview_answer.improvements
            }
        }, 201

    except Exception as e:

        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 500

# ============================================================
# GENERATE NEXT INTERVIEW QUESTION
# ============================================================

@question_bp.route("/next-question", methods=["POST"])
@jwt_required()
def next_question():
    

    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    interview_id = data.get("interview_id")

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    # --------------------------------------------------------
    # Find interview
    # --------------------------------------------------------

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    if interview.status != "active":
        return {
            "status": "error",
            "message": "Interview is not active"
        }, 400

    if interview.current_stage != "technical_interview":
        return {
            "status": "error",
            "message": "Interview is not in technical stage"
        }, 400

    if not interview.current_question_id:
        return {
            "status": "error",
            "message": "No active question found"
        }, 400

    try:

        # ----------------------------------------------------
        # Verify current question
        # ----------------------------------------------------

        current_question = InterviewQuestion.query.filter_by(
            id=interview.current_question_id,
            interview_id=interview.id
        ).first()

        if not current_question:
            return {
                "status": "error",
                "message": "Current question not found"
            }, 404

        # ----------------------------------------------------
        # Check whether current question has been answered
        # ----------------------------------------------------

        current_answer = InterviewAnswer.query.filter_by(
            question_id=current_question.id
        ).first()

        if not current_answer:
            return {
                "status": "error",
                "message": "Please answer the current question first"
            }, 400

        # ----------------------------------------------------
        # Get resume
        # ----------------------------------------------------

        resume = Resume.query.filter_by(
            id=interview.resume_id,
            user_id=user_id
        ).first()

        if not resume:
            return {
                "status": "error",
                "message": "Resume not found"
            }, 404

        # ----------------------------------------------------
        # Get resume analysis
        # ----------------------------------------------------

        analysis = ResumeAnalysis.query.filter_by(
            resume_id=resume.id
        ).first()

        if not analysis:
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

        # ----------------------------------------------------
        # Get all previous questions
        # ----------------------------------------------------

        previous_question_records = InterviewQuestion.query.filter_by(
            interview_id=interview.id
        ).order_by(
            InterviewQuestion.question_order.asc()
        ).all()

        previous_questions = [
            item.question
            for item in previous_question_records
        ]

        # ----------------------------------------------------
        # Get all previous answers
        # ----------------------------------------------------

        answers = InterviewAnswer.query.filter_by(
            interview_id=interview.id
        ).order_by(
            InterviewAnswer.id.asc()
        ).all()

        previous_answers = [
            item.answer
            for item in answers
        ]

        # ----------------------------------------------------
        # Latest evaluation
        # ----------------------------------------------------

        latest_answer = answers[-1]

        latest_evaluation = {
            "score": latest_answer.score,
            "technical_accuracy": latest_answer.technical_accuracy,
            "relevance": latest_answer.relevance,
            "completeness": latest_answer.completeness,
            "feedback": latest_answer.feedback,
            "strengths": latest_answer.strengths or [],
            "improvements": latest_answer.improvements or []
        }

        # ----------------------------------------------------
        # Generate next question
        # ----------------------------------------------------

        next_question_data = generate_next_interview_question(
            resume_analysis=resume_analysis,
            previous_questions=previous_questions,
            previous_answers=previous_answers,
            latest_evaluation=latest_evaluation,
            job_description=interview.job_description
        )

        generated_question = next_question_data.get("question")

        if not generated_question:
            raise ValueError(
                "AI did not generate a next question"
            )

        # ----------------------------------------------------
        # Duplicate question protection
        # ----------------------------------------------------

        normalized_question = generated_question.strip().lower()

        for previous_question in previous_questions:

            if normalized_question == previous_question.strip().lower():

                return {
                    "status": "error",
                    "message": "AI generated a duplicate question. Please try again."
                }, 409

        # ----------------------------------------------------
        # Determine next question order
        # ----------------------------------------------------

        next_order = len(previous_question_records) + 1

        # ----------------------------------------------------
        # Save next question
        # ----------------------------------------------------

        interview_question = InterviewQuestion(
            interview_id=interview.id,
            question=generated_question,
            topic=next_question_data.get("topic"),
            category=next_question_data.get("category"),
            difficulty=next_question_data.get("difficulty"),
            question_order=next_order
        )

        db.session.add(interview_question)

        # Generate database ID
        db.session.flush()

        # ----------------------------------------------------
        # Set new question as current question
        # ----------------------------------------------------

        interview.current_question_id = interview_question.id

        db.session.commit()

        # ----------------------------------------------------
        # Return next question
        # ----------------------------------------------------

        return {
            "status": "success",
            "message": "Next question generated successfully",
            "question": {
                "id": interview_question.id,
                "interview_id": interview_question.interview_id,
                "question": interview_question.question,
                "topic": interview_question.topic,
                "category": interview_question.category,
                "difficulty": interview_question.difficulty,
                "question_order": interview_question.question_order
            },
            "current_question_id": interview.current_question_id
        }, 201

    except Exception as e:

        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 500



@question_bp.route("/end", methods=["POST"])
@jwt_required()
def end_interview():

    user_id = int(get_jwt_identity())

    data = request.get_json() or {}

    interview_id = data.get("interview_id")

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    interview = Interview.query.filter_by(
        id=interview_id,
        user_id=user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    if interview.status == "completed":
        return {
            "status": "error",
            "message": "Interview is already completed"
        }, 400

    if interview.status != "active":
        return {
            "status": "error",
            "message": "Interview cannot be ended"
        }, 400

    try:

        interview.status = "completed"
        interview.current_stage = "completed"

        db.session.commit()

        return {
            "status": "success",
            "message": "Interview ended successfully",
            "interview": {
                "id": interview.id,
                "status": interview.status,
                "stage": interview.current_stage
            }
        }, 200

    except Exception as e:

        db.session.rollback()

        return {
            "status": "error",
            "message": str(e)
        }, 500
@question_bp.route("/current", methods=["GET"])
@jwt_required()
def get_current_question():

    user_id = int(get_jwt_identity())

    interview_id = request.args.get("interview_id")

    if not interview_id:
        return {
            "status": "error",
            "message": "interview_id is required"
        }, 400

    interview = Interview.query.filter(
        Interview.id == int(interview_id),
        Interview.user_id == user_id
    ).first()

    if not interview:
        return {
            "status": "error",
            "message": "Interview not found"
        }, 404

    if interview.status != "active":
        return {
            "status": "error",
            "message": "Interview is not active"
        }, 400

    if interview.current_stage != "technical_interview":
        return {
            "status": "error",
            "message": "Interview is not in technical stage"
        }, 400

    if not interview.current_question_id:
        return {
            "status": "error",
            "message": "No current question found"
        }, 404

    current_question = InterviewQuestion.query.filter(
        InterviewQuestion.id == interview.current_question_id,
        InterviewQuestion.interview_id == interview.id
    ).first()

    if not current_question:
        return {
            "status": "error",
            "message": "Current question not found"
        }, 404

    return {
        "status": "success",
        "question": {
            "id": current_question.id,
            "interview_id": current_question.interview_id,
            "question": current_question.question,
            "topic": current_question.topic,
            "category": current_question.category,
            "difficulty": current_question.difficulty,
            "question_order": current_question.question_order
        }
    }, 200