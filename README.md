# AI PR Code Reviewer

An automated GitHub Pull Request reviewer powered by NVIDIA Llama-4 Maverick. It reads every changed file in a PR, identifies real issues at the line level, posts inline comments directly on the problematic code, and submits a final verdict (Approve, Request Changes, or Comment) without any human intervention.

---

## The Problem It Solves

Code review is one of the most time-consuming parts of software development. A senior engineer reviewing a 10-file PR takes 30 to 60 minutes on average. Smaller teams skip reviews entirely. Security vulnerabilities, logic bugs, and performance problems slip through because reviewers are tired, rushed, or simply miss things.

This tool acts as an always-on reviewer that catches issues before a human even looks at the PR.

---

## Real Output from a Test Run

The following results are from running this tool on a real PR that added a user authentication endpoint (5 files changed, 312 lines added):

```
Reviewing PR #7 in testorg/backend-api
  Title: Add user authentication endpoint
  Commit: 3fa92c1
  Files to review: 4/5
  Analyzing: src/auth/login.py
  Analyzing: src/models/user.py
  Analyzing: src/utils/token.py
  Analyzing: tests/test_auth.py
  Generating summary...

Review submitted: Request Changes
Files reviewed: 4
Issues found: 6
  Critical: 1 (SQL injection in login.py line 23)
  High: 2 (plaintext password comparison, missing token expiry)
  Medium: 2 (unhandled exception, overly broad except clause)
  Low: 1 (inconsistent naming)
Overall score: 4/10
Time taken: 31 seconds
```

Inline comment posted on login.py line 23:

```
[SECURITY] CRITICAL

SQL query is built using string concatenation. The username parameter is
directly interpolated into the query string, making this endpoint vulnerable
to SQL injection. An attacker can input the value:  ' OR '1'='1  to bypass
authentication entirely and gain access to any account.

Suggested fix:
Use parameterized queries.
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

---

## ROI Breakdown

Based on testing across 14 real PRs over one week:

| Metric | Manual Review | With AI Reviewer |
|--------|--------------|-----------------|
| Average review time per PR | 41 minutes | 31 seconds |
| Issues caught per PR | 3.2 | 5.8 |
| Critical issues missed | 2 in 14 PRs | 0 in 14 PRs |
| Engineer time saved per week (5 PRs/day team) | - | ~17 hours |

The tool catches on average 81% more issues than a manual review pass on the same code, particularly for security-related patterns that humans normalize over time.

---

## How It Works

1. A developer opens or updates a Pull Request
2. GitHub Actions triggers the reviewer automatically
3. The tool fetches the diff for every changed code file
4. Each file's diff is sent to Llama-4 Maverick with a structured prompt asking it to find bugs, security issues, performance problems, and style violations
5. The model returns a structured JSON response with each issue mapped to a specific line number
6. The tool posts an inline comment on each flagged line inside the PR
7. A final summary comment is posted with an overall score and verdict

---

## Setup

### Option 1: Add to any existing GitHub repository

Copy the workflow file into your repository:

```
.github/
  workflows/
    pr-review.yml
```

Add one secret in your repository Settings under Secrets and variables, then Actions:

- NVIDIA_API_KEY: your NVIDIA NIM API key

GITHUB_TOKEN is provided automatically by GitHub Actions.

From this point, every PR opened against your repository will be automatically reviewed.

### Option 2: Run locally against any PR

```bash
git clone https://github.com/gowthambhuvanam/ai-pr-code-reviewer
cd ai-pr-code-reviewer

pip install -r requirements.txt

cp .env.example .env
# Add your NVIDIA_API_KEY and GITHUB_TOKEN to the .env file

python main.py --owner <github-org-or-username> --repo <repository-name> --pr <pr-number>
```

Example:

```bash
python main.py --owner gowthambhuvanam --repo backend-api --pr 14
```

---

## What It Detects

| Category | Examples |
|----------|---------|
| Security | SQL injection, hardcoded secrets, path traversal, unsafe deserialization, XSS |
| Bugs | Null pointer risks, unhandled exceptions, off-by-one errors, logic errors |
| Performance | N+1 queries, unnecessary loops, missing pagination |
| Complexity | Functions doing too much, deeply nested conditions |
| Style | Inconsistent naming, missing error handling patterns |

---

## Supported Languages

Python, JavaScript, TypeScript, Java, Go, Ruby, PHP, C#, C++, C, Rust, Swift, Kotlin

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| NVIDIA_API_KEY | API key from build.nvidia.com |
| GITHUB_TOKEN | GitHub token with pull-requests write permission |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Model | NVIDIA Llama-4 Maverick 17B 128E Instruct |
| GitHub Integration | GitHub REST API v3 |
| Language | Python 3.11 |
| Automation | GitHub Actions |

---

## Project Structure

```
ai-pr-code-reviewer/
  .github/
    workflows/
      pr-review.yml       triggers on pull_request events
  src/
    llm_client.py         NVIDIA API calls and prompt engineering
    github_client.py      GitHub API - fetch diffs, post comments, submit reviews
    reviewer.py           orchestration logic
  main.py                 entry point, supports CLI and Actions environment
  requirements.txt
  .env.example
```
