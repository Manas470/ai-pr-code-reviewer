import os
import json
import re
from openai import OpenAI


class NvidiaLLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.environ["NVIDIA_API_KEY"]
        )
        self.model = "meta/llama-4-maverick-17b-128e-instruct"

    def review_code(self, code_diff: str, filename: str) -> dict:
        prompt = f"""You are a senior software engineer and security expert doing a thorough code review.

File: {filename}

Code Diff (lines starting with + are additions, - are removals):
{code_diff}

Analyze this diff and return a JSON object with exactly this structure:
{{
  "summary": "2-3 sentence overall assessment",
  "severity": "low|medium|high|critical",
  "issues": [
    {{
      "line": <line number in the diff where issue occurs, integer>,
      "type": "bug|security|performance|style|complexity",
      "severity": "low|medium|high|critical",
      "description": "Clear explanation of the issue",
      "suggestion": "Specific fix or improvement"
    }}
  ],
  "positive_aspects": ["list", "of", "good", "things"],
  "overall_score": <integer 1-10>
}}

Rules:
- Only report real issues, not nitpicks
- For security issues: check for SQL injection, XSS, hardcoded secrets, unsafe deserialization, path traversal
- For bugs: check for null pointer risks, off-by-one errors, unhandled exceptions, logic errors
- For performance: check for N+1 queries, unnecessary loops, missing index hints
- If no issues found, return empty issues array
- Return ONLY valid JSON, no markdown, no explanation"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a code review expert. Always respond with valid JSON only, no markdown code blocks."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```json\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        return json.loads(content)

    def generate_summary_comment(self, file_reviews: list, pr_title: str) -> str:
        reviews_text = json.dumps(file_reviews, indent=2)
        prompt = f"""Based on these code review results for PR: "{pr_title}", write a professional GitHub PR review comment.

Reviews: {reviews_text}

Write a markdown comment that includes:
1. A TL;DR section with overall verdict (Approve / Request Changes / Comment)
2. A summary table of issues by severity
3. Top 3 most important issues to fix
4. What was done well

Keep it concise, actionable, and professional. Do not use emojis."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a senior engineer writing PR review comments. Do not use emojis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
