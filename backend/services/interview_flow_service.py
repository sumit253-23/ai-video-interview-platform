from extensions import db

from models.resume import Resume
from models.resume_analysis import ResumeAnalysis
from models.interview import Interview
from models.interview_answer import InterviewAnswer
from models.interview_question import InterviewQuestion

from services.question_service import generate_next_interview_question


def generate_next_question_for_interview(
    interview,
    user_id
):
    """
    Generate and save the next adaptive interview question.
    """

    # -----------------------------------------------------
    # Verify current question
    # -----------------------------------------------------

    if not interview.current_question_id:
        raise ValueError("No active question found")

    current_question = InterviewQuestion.query.filter_by(
        id=interview.current_question_id,
        interview_id=interview.id
    ).first()

    if not current_question:
        raise ValueError("Current question not found")

    # -----------------------------------------------------
    # Verify current question has an answer
    # -----------------------------------------------------

    current_answer = InterviewAnswer.query.filter_by(
        question_id=current_question.id
    ).first()

    if not current_answer:
        raise ValueError(
            "Please answer the current question first"
        )

    # -----------------------------------------------------
    # Get resume
    # -----------------------------------------------------

    resume = Resume.query.filter_by(
        id=interview.resume_id,
        user_id=user_id
    ).first()

    if not resume:
        raise ValueError("Resume not found")

    # -----------------------------------------------------
    # Get resume analysis
    # -----------------------------------------------------

    analysis = ResumeAnalysis.query.filter_by(
        resume_id=resume.id
    ).first()

    if not analysis:
        raise ValueError("Resume analysis not found")

    resume_analysis = {
        "summary": analysis.summary,
        "skills": analysis.skills or [],
        "programming_languages": (
            analysis.programming_languages or []
        ),
        "frameworks": analysis.frameworks or [],
        "projects": analysis.projects or [],
        "cs_fundamentals": (
            analysis.cs_fundamentals or []
        ),
        "dsa_topics": analysis.dsa_topics or []
    }

    # -----------------------------------------------------
    # Get previous questions
    # -----------------------------------------------------

    previous_question_records = (
        InterviewQuestion.query
        .filter_by(interview_id=interview.id)
        .order_by(
            InterviewQuestion.question_order.asc()
        )
        .all()
    )

    previous_questions = [
        item.question
        for item in previous_question_records
    ]

    # -----------------------------------------------------
    # Get previous answers
    # -----------------------------------------------------

    answers = (
        InterviewAnswer.query
        .filter_by(interview_id=interview.id)
        .order_by(
            InterviewAnswer.id.asc()
        )
        .all()
    )

    previous_answers = [
        item.answer
        for item in answers
    ]

    # -----------------------------------------------------
    # Latest evaluation
    # -----------------------------------------------------

    latest_answer = answers[-1]

    latest_evaluation = {
        "score": latest_answer.score,
        "technical_accuracy": (
            latest_answer.technical_accuracy
        ),
        "relevance": latest_answer.relevance,
        "completeness": latest_answer.completeness,
        "feedback": latest_answer.feedback,
        "strengths": latest_answer.strengths or [],
        "improvements": (
            latest_answer.improvements or []
        )
    }

    # -----------------------------------------------------
    # Generate next question
    # -----------------------------------------------------

    next_question_data = generate_next_interview_question(
        resume_analysis=resume_analysis,
        previous_questions=previous_questions,
        previous_answers=previous_answers,
        latest_evaluation=latest_evaluation,
        job_description=interview.job_description
    )

    generated_question = next_question_data.get(
        "question"
    )

    if not generated_question:
        raise ValueError(
            "AI did not generate a next question"
        )

    # -----------------------------------------------------
    # Prevent duplicate question
    # -----------------------------------------------------

    normalized_question = (
        generated_question.strip().lower()
    )

    for previous_question in previous_questions:

        if (
            normalized_question
            == previous_question.strip().lower()
        ):
            raise ValueError(
                "AI generated a duplicate question. "
                "Please try again."
            )

    # -----------------------------------------------------
    # Determine question order
    # -----------------------------------------------------

    next_order = len(
        previous_question_records
    ) + 1

    # -----------------------------------------------------
    # Save next question
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Set new current question
    # -----------------------------------------------------

    interview.current_question_id = (
        interview_question.id
    )

    db.session.commit()

    return interview_question