from datetime import datetime

from extensions import db
from models.interview_answer import InterviewAnswer
from services.evaluation_service import evaluate_answer


def process_interview_answer(
    interview,
    interview_question,
    answer_text
):
    """
    Save candidate answer and evaluate it using AI.

    Used by automatic audio/video interview pipeline.
    """

    # Validate answer
    if not answer_text or not answer_text.strip():
        raise ValueError("Answer cannot be empty")

    answer_text = answer_text.strip()

    # Prevent duplicate answer
    existing_answer = InterviewAnswer.query.filter_by(
        interview_id=interview.id,
        question_id=interview_question.id
    ).first()

    if existing_answer:
        raise ValueError(
            "This question has already been answered"
        )

    # Create answer record
    answer = InterviewAnswer(
        interview_id=interview.id,
        question_id=interview_question.id,
        question=interview_question.question,
        topic=interview_question.topic,
        category=interview_question.category,
        difficulty=interview_question.difficulty,
        answer=answer_text
    )

    db.session.add(answer)
    db.session.flush()

    # AI evaluation
    evaluation = evaluate_answer(
        question=interview_question.question,
        answer=answer_text,
        topic=interview_question.topic,
        category=interview_question.category,
        difficulty=interview_question.difficulty
    )

    # Save evaluation
    answer.score = evaluation.get("score")
    answer.technical_accuracy = evaluation.get(
        "technical_accuracy"
    )
    answer.relevance = evaluation.get(
        "relevance"
    )
    answer.completeness = evaluation.get(
        "completeness"
    )
    answer.feedback = evaluation.get(
        "feedback"
    )
    answer.strengths = evaluation.get(
        "strengths"
    )
    answer.improvements = evaluation.get(
        "improvements"
    )
    answer.answered_at = datetime.utcnow()

    db.session.commit()

    return {
        "answer": answer,
        "evaluation": evaluation
    }