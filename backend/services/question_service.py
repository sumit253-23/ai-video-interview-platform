import json
import os

from groq import Groq


def generate_interview_question(
    resume_analysis,
    job_description=None,
    previous_questions=None,
    previous_answers=None
):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=api_key)

    previous_questions = previous_questions or []
    previous_answers = previous_answers or []

    prompt = f"""
You are an expert technical interviewer conducting a personalized
software engineering interview.

Generate exactly ONE interview question.

Candidate Resume Analysis:
{json.dumps(resume_analysis, indent=2)}

Job Description:
{job_description or "No specific job description provided."}

Previous Questions:
{json.dumps(previous_questions, indent=2)}

Previous Answers:
{json.dumps(previous_answers, indent=2)}

Rules:

1. Ask only ONE question.
2. The question must be relevant to the candidate's resume.
3. Prefer topics from the candidate's actual projects, skills,
   programming languages, frameworks, CS fundamentals, or DSA.
4. Do not invent experience that is not present in the resume.
5. Do not repeat a previous question.
6. Start with reasonable technical questions.
7. The difficulty should gradually increase.
8. Questions should be suitable for a software engineering interview.
9. If a previous answer indicates weakness or uncertainty,
   the next question may explore that topic.
10. Keep the question clear and concise.

Return ONLY valid JSON in exactly this format:

{{
    "question": "",
    "topic": "",
    "category": "",
    "difficulty": ""
}}

Allowed category values:
- Project
- Programming
- Framework
- Database
- CS Fundamentals
- DSA
- System Design
- General Technical

Allowed difficulty values:
- Easy
- Medium
- Hard
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional technical interviewer. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    content = response.choices[0].message.content.strip()

    # Handle accidental markdown code fences
    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "", 1)
        content = content.strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")

def generate_interview_introduction():
    return (
        "Welcome to the AI Interview Platform. "
        "I am your AI interviewer, and I will be conducting your interview today. "
        "Before we begin the technical interview, "
        "please introduce yourself."
    )
def generate_first_question_after_introduction(
    resume_analysis,
    candidate_introduction,
    job_description=None
):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=api_key)

    prompt = f"""
You are a professional human-like technical interviewer.

The candidate has just completed their self-introduction.

Your job is to respond naturally to the candidate and then ask the FIRST
technical interview question.

Candidate Resume Analysis:

{json.dumps(resume_analysis, indent=2)}

Candidate Introduction:

{candidate_introduction}

Job Description:

{job_description or "No specific job description provided."}

Rules:

1. Give a short, natural acknowledgement of the candidate's introduction.
2. Then ask exactly ONE technical question.
3. The question must be based on the candidate's actual resume.
4. Use the candidate's introduction as additional context.
5. Prefer a project, technology, programming language, framework,
   database, DSA, or CS concept actually present in the resume.
6. Do not invent experience.
7. Do not ask the candidate to introduce themselves again.
8. Do not ask multiple questions.
9. Start with Easy or Medium difficulty.
10. Make the interaction feel like a real human technical interview.
11. The acknowledgement should be concise and conversational.
12. Do not evaluate the candidate's technical ability yet because
    the candidate has not answered a technical question.

Return ONLY valid JSON in exactly this format:

{{
    "response": "",
    "question": "",
    "topic": "",
    "category": "",
    "difficulty": ""
}}

Allowed category values:

- Project
- Programming
- Framework
- Database
- CS Fundamentals
- DSA
- System Design
- General Technical

Allowed difficulty values:

- Easy
- Medium
- Hard
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional human-like technical interviewer. "
                    "Be conversational, concise, and return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "", 1)
        content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")
    
def generate_next_interview_question(
    resume_analysis,
    previous_questions,
    previous_answers,
    latest_evaluation,
    job_description=None
):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=api_key)

    previous_questions = previous_questions or []
    previous_answers = previous_answers or []
    latest_evaluation = latest_evaluation or {}

    prompt = f"""
You are a professional human-like adaptive technical interviewer.

The candidate has just answered the previous interview question.

Your job is to:

1. Understand the candidate's latest answer.
2. Consider the latest evaluation.
3. Give a short natural conversational response.
4. Then ask exactly ONE relevant follow-up technical question.

Candidate Resume Analysis:

{json.dumps(resume_analysis, indent=2)}

Job Description:

{job_description or "No specific job description provided."}

Previous Questions:

{json.dumps(previous_questions, indent=2)}

Previous Answers:

{json.dumps(previous_answers, indent=2)}

Latest Answer Evaluation:

{json.dumps(latest_evaluation, indent=2)}

Interview behavior:

- Act like a real professional interviewer.
- Understand what the candidate actually said.
- Do not simply generate an unrelated question.
- The next question should logically follow from the candidate's latest answer.
- Use the candidate's resume and project experience whenever relevant.
- If the candidate mentioned a technology, implementation detail,
  design decision, or project feature, you may probe deeper into it.
- If the answer is weak or incomplete, ask a simpler clarifying or
  foundational follow-up question.
- If the answer is strong, gradually increase the difficulty.
- If the candidate made a technical mistake, the next question may
  carefully probe that concept.
- Do not invent technologies, projects, or experience.
- Never repeat a previous question.
- Avoid asking about personality, intelligence, mental state,
  or other personal traits.
- Do not ask the candidate to introduce themselves again.
- Ask exactly ONE question.
- Keep the conversational response short.
- Keep the question clear and concise.

Conversation response rules:

The "response" should sound natural, for example:

"That's a good approach. You mentioned JWT authentication in your project."

or:

"Good explanation. You clearly separated the frontend and backend responsibilities."

or:

"I see. You mentioned using MongoDB for the project. Let's go a little deeper into that."

Do NOT make the response overly long.

Difficulty guidance:

Easy:
Basic concepts and understanding.

Medium:
Implementation and practical understanding.

Hard:
Deeper technical reasoning, trade-offs, debugging,
architecture, optimization, or edge cases.

Return ONLY valid JSON in exactly this format:

{{
    "response": "",
    "question": "",
    "topic": "",
    "category": "",
    "difficulty": ""
}}

Allowed category values:

- Project
- Programming
- Framework
- Database
- CS Fundamentals
- DSA
- System Design
- General Technical

Allowed difficulty values:

- Easy
- Medium
- Hard
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an adaptive professional human-like "
                    "technical interviewer. "
                    "Understand the candidate's answer, respond naturally, "
                    "and ask one relevant follow-up question. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "", 1)
        content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")