import json
import os

from groq import Groq


def evaluate_answer(
    question,
    answer,
    topic=None,
    category=None,
    difficulty=None
):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=api_key)

    prompt = f"""
You are an expert technical interviewer.

Evaluate the candidate's answer to the interview question.

Question:
{question}

Candidate Answer:
{answer}

Topic:
{topic or "Not specified"}

Category:
{category or "Not specified"}

Difficulty:
{difficulty or "Not specified"}

Evaluate ONLY the quality of the candidate's answer.

Do NOT judge:
- Personality
- Intelligence
- Mental state
- Confidence as a personality trait
- Background or personal characteristics

Evaluate these areas:

1. Technical accuracy
2. Relevance to the question
3. Completeness
4. Clarity of explanation
5. Overall answer quality

Scoring:
- score must be a number from 0 to 10.
- Use the actual content of the answer.
- Do not give a high score simply because the answer sounds confident.
- If the answer is partially correct, reflect that in the score.
- If the answer is incorrect or irrelevant, score accordingly.

Return ONLY valid JSON in exactly this format:

{{
    "score": 0,
    "technical_accuracy": "",
    "relevance": "",
    "completeness": "",
    "feedback": "",
    "strengths": [],
    "improvements": []
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a technical interview evaluation engine. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "", 1)
        content = content.strip()

    try:
        result = json.loads(content)

    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")

    return result