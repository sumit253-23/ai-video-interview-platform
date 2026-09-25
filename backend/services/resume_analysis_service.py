import json
import os

from groq import Groq


def analyze_resume(resume_text):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=api_key)

    prompt = f"""
You are an expert technical interviewer.

Analyze the following candidate resume and return ONLY valid JSON.

The analysis must identify:

1. A short professional summary
2. Technical skills
3. Programming languages
4. Frameworks and libraries
5. Projects
6. Computer Science fundamentals
7. DSA topics

Important:
- Extract information only from the resume.
- Do not invent skills or projects.
- If something is not mentioned, return an empty array.
- For projects, include the project name and a short description.
- Identify CS fundamentals only when there is reasonable evidence from the resume.
- Identify DSA topics only when mentioned or clearly supported.

Return exactly this JSON structure:

{{
    "summary": "",
    "skills": [],
    "programming_languages": [],
    "frameworks": [],
    "projects": [],
    "cs_fundamentals": [],
    "dsa_topics": []
}}

Resume:

{resume_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a resume analysis engine. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")