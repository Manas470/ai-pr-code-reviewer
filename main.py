#!/usr/bin/env python3
"""
AI PR Code Reviewer
Automatically reviews GitHub PRs using NVIDIA Llama-4 Maverick.

Usage:
  Local:          python main.py --owner <owner> --repo <repo> --pr <number>
  GitHub Actions: Triggered automatically on pull_request events
"""

import os
import argparse
import sys
from dotenv import load_dotenv
from src.reviewer import PRReviewer

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="AI-powered GitHub PR Code Reviewer")
    parser.add_argument("--owner", help="GitHub repo owner or org")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--pr", type=int, help="Pull request number")
    return parser.parse_args()


def main():
    args = parse_args()

    owner = args.owner or os.environ.get("GITHUB_REPOSITORY", "/").split("/")[0]
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "/").split("/")[1]
    pr_number = args.pr or int(os.environ.get("PR_NUMBER", 0))

    if not all([owner, repo, pr_number]):
        print("Error: Provide --owner, --repo, --pr or set GITHUB_REPOSITORY and PR_NUMBER env vars")
        sys.exit(1)

    if not os.environ.get("LLM_API_KEY"):
        print("Error: LLM_API_KEY environment variable not set")
        sys.exit(1)

    if not os.environ.get("LLM_MODEL"):
        print("Error: LLM_MODEL environment variable not set")
        sys.exit(1)

    if not os.environ.get("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    reviewer = PRReviewer()
    result = reviewer.review_pr(owner, repo, pr_number)

    if result:
        print(f"\nSummary: Reviewed {result['files_reviewed']} files | Decision: {result['event']}")


if __name__ == "__main__":
    main()
