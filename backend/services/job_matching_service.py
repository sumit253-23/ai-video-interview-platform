import json

from groq import Groq

from config import Config


client = Groq(api_key=Config.GROQ_API_KEY)


def match_resume_with_job(resume_analysis, job_description):
    if not job_description or not job_description.strip():
        raise ValueError("Job description is required.")

    resume_data = {
        "summary": resume_analysis.summary or "",
        "skills": resume_analysis.skills or [],
        "programming_languages": (
            resume_analysis.programming_languages or []
        ),
        "frameworks": resume_analysis.frameworks or [],
        "projects": resume_analysis.projects or [],
        "cs_fundamentals": (
            resume_analysis.cs_fundamentals or []
        ),
        "dsa_topics": resume_analysis.dsa_topics or [],
    }

    prompt = f"""
You are an AI career and job-matching assistant.

Compare the candidate's resume analysis with the provided job
description.

Candidate Resume Analysis:
{json.dumps(resume_data, indent=2)}

Job Description:
{job_description}

Return ONLY valid JSON in exactly this structure:

{{
  "match_score": 0,
  "matched_skills": [],
  "missing_skills": [],
  "strengths": [],
  "recommendations": []
}}

Rules:
- match_score must be a number from 0 to 100.
- matched_skills must contain skills that are supported by both
  the resume and job description.
- missing_skills must contain important job requirements that
  are not clearly present in the resume.
- strengths must describe relevant strengths of the candidate.
- recommendations must give practical suggestions for improving
  the candidate's match.
- Do not invent experience that is not present in the resume.
- Keep every array concise and relevant.
- Return JSON only. No markdown.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise resume and job matching "
                    "assistant. Always return valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"AI returned invalid JSON: {error}"
        )

    required_keys = [
        "match_score",
        "matched_skills",
        "missing_skills",
        "strengths",
        "recommendations",
    ]

    for key in required_keys:
        if key not in result:
            raise ValueError(
                f"AI response missing field: {key}"
            )

    score = float(result["match_score"])

    if score < 0 or score > 100:
        raise ValueError(
            "AI returned an invalid match score."
        )

    result["match_score"] = score

    return result