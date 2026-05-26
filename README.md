# AI PR Code Reviewer

An automated GitHub Pull Request reviewer that works with any LLM provider. It reads every changed file in a PR, identifies real issues at the line level, posts inline comments directly on the problematic code, and submits a final verdict (Approve, Request Changes, or Comment) without any human intervention.

Works with OpenAI, NVIDIA NIM, Groq, Together AI, Ollama, or any OpenAI-compatible API.

---
## The Problem It Solves

Code review is one of the most time-consuming parts of software development. A senior engineer reviewing a 10-file PR takes 30 to 60 minutes on average. Smaller teams skip reviews entirely. Security vulnerabilities, logic bugs, and performance problems slip through because reviewers are tired, rushed, or simply miss things.

This tool acts as an always-on reviewer that catches issues before a human even looks at the PR.

---

## Real Output from a Test Run

The following results are from running this tool on a real PR that added a user authentication endpoint (3 files changed, 128 lines added):

```
Reviewing PR #1 in gowthambhuvanam/ai-reviewer-test-project
  Title: Add user authentication module and API endpoints
  Commit: 9760a0c
  Files to review: 3/3
  Analyzing: src/api.py
  Analyzing: src/auth.py
  Analyzing: tests/test_auth.py
  Generating summary...

Review submitted: Request Changes
Files reviewed: 3
Time taken: 31 seconds
```

Issues caught:

| Severity | Count | Examples |
|----------|-------|---------|
| Critical | 3 | SQL injection line 14, XSS line 33, command injection line 32 |
| High | 10 | Hardcoded secret, no auth on endpoints, path traversal, MD5 passwords |
| Medium | 5 | No JWT expiry, DB connection leak, empty test assertions |

Inline comment example posted on auth.py line 14:

```
[SECURITY] CRITICAL severity

SQL query is built using string concatenation. The username parameter is
directly interpolated into the query string, making this endpoint vulnerable
to SQL injection. An attacker can input: ' OR '1'='1 to bypass authentication.

Suggested fix: Use parameterized queries.
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

---

## Setup

### Option 1: Add to any existing GitHub repository (recommended)

Copy the workflow file into your repository:

```
.github/
  workflows/
    pr-review.yml
```

Add three secrets in your repository Settings under Secrets and variables, then Actions:

| Secret | Description |
|--------|-------------|
| LLM_API_KEY | Your API key from whichever provider you use |
| LLM_BASE_URL | API base URL for your provider (see examples below) |
| LLM_MODEL | Model name to use |

Provider examples:

```
# OpenAI
LLM_API_KEY     = sk-...
LLM_BASE_URL    = https://api.openai.com/v1
LLM_MODEL       = gpt-4o

# NVIDIA NIM
LLM_API_KEY     = nvapi-...
LLM_BASE_URL    = https://integrate.api.nvidia.com/v1
LLM_MODEL       = meta/llama-4-maverick-17b-128e-instruct

# Groq
LLM_API_KEY     = gsk_...
LLM_BASE_URL    = https://api.groq.com/openai/v1
LLM_MODEL       = llama-3.3-70b-versatile

# Ollama (local/self-hosted)
LLM_API_KEY     = ollama
LLM_BASE_URL    = http://localhost:11434/v1
LLM_MODEL       = codellama
```

GITHUB_TOKEN is provided automatically by GitHub Actions, no action needed.

From this point, every PR opened against your repository will be automatically reviewed.

### Option 2: Run locally against any PR

```bash
git clone https://github.com/gowthambhuvanam/ai-pr-code-reviewer
cd ai-pr-code-reviewer

pip install -r requirements.txt

cp .env.example .env
# Fill in your LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, and GITHUB_TOKEN

python main.py --owner <github-username> --repo <repository-name> --pr <pr-number>
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
| LLM_API_KEY | API key for your chosen LLM provider |
| LLM_BASE_URL | Base URL of the provider API (optional if using OpenAI directly) |
| LLM_MODEL | Model name to use for reviews |
| GITHUB_TOKEN | GitHub token with pull-requests write permission |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM Integration | Any OpenAI-compatible API |
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
    llm_client.py         provider-agnostic LLM client
    github_client.py      GitHub API - fetch diffs, post comments, submit reviews
    reviewer.py           orchestration logic
  main.py                 entry point, supports CLI and Actions environment
  requirements.txt
  .env.example
```
