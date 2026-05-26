import os
import json
from src.llm_client import NvidiaLLMClient
from src.github_client import GitHubClient

REVIEWABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb",
    ".php", ".cs", ".cpp", ".c", ".h", ".rs", ".swift", ".kt"
}

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

MAX_DIFF_CHARS = 6000


def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def truncate_diff(patch: str, max_chars: int = MAX_DIFF_CHARS) -> str:
    if len(patch) <= max_chars:
        return patch
    return patch[:max_chars] + "\n... (diff truncated for review)"


def determine_review_event(file_reviews: list) -> str:
    max_severity = 0
    for review in file_reviews:
        for issue in review.get("issues", []):
            rank = SEVERITY_RANK.get(issue.get("severity", "low"), 1)
            max_severity = max(max_severity, rank)

    if max_severity >= 3:
        return "REQUEST_CHANGES"
    elif max_severity == 2:
        return "COMMENT"
    return "APPROVE"


class PRReviewer:
    def __init__(self):
        self.llm = NvidiaLLMClient()
        self.github = GitHubClient()

    def review_pr(self, owner: str, repo: str, pr_number: int):
        print(f"Reviewing PR #{pr_number} in {owner}/{repo}")

        pr = self.github.get_pr_details(owner, repo, pr_number)
        pr_title = pr["title"]
        commit_sha = pr["head"]["sha"]
        print(f"  Title: {pr_title}")
        print(f"  Commit: {commit_sha[:7]}")

        files = self.github.get_pr_files(owner, repo, pr_number)
        reviewable = [
            f for f in files
            if get_extension(f["filename"]) in REVIEWABLE_EXTENSIONS
            and f.get("patch")
        ]

        print(f"  Files to review: {len(reviewable)}/{len(files)}")

        if not reviewable:
            self.github.post_pr_comment(
                owner, repo, pr_number,
                "AI PR Reviewer: No reviewable code files found in this PR."
            )
            return

        file_reviews = []
        for file in reviewable:
            filename = file["filename"]
            patch = truncate_diff(file["patch"])
            print(f"  Analyzing: {filename}")

            try:
                review = self.llm.review_code(patch, filename)
                review["filename"] = filename
                file_reviews.append(review)

                for issue in review.get("issues", []):
                    severity = issue.get("severity", "low")
                    issue_type = issue.get("type", "issue").upper()
                    comment_body = (
                        f"[{issue_type}] {severity.upper()} severity\n\n"
                        f"{issue['description']}\n\n"
                        f"Suggested fix: {issue['suggestion']}"
                    )
                    line_num = issue.get("line", 1)
                    self.github.post_review_comment(
                        owner, repo, pr_number, commit_sha,
                        filename, line_num, comment_body
                    )

            except Exception as e:
                print(f"  Could not review {filename}: {e}")
                file_reviews.append({"filename": filename, "error": str(e), "issues": []})

        print("  Generating summary...")
        summary = self.llm.generate_summary_comment(file_reviews, pr_title)
        event = determine_review_event(file_reviews)

        event_labels = {
            "APPROVE": "Approved",
            "REQUEST_CHANGES": "Changes Requested",
            "COMMENT": "Comment"
        }
        event_label = event_labels.get(event, event)
        full_summary = f"## AI Code Review - {event_label}\n\n{summary}\n\nPowered by NVIDIA Llama-4 Maverick"

        self.github.submit_review(owner, repo, pr_number, commit_sha, full_summary, event)
        print(f"\nReview submitted: {event_label}")

        return {"pr": pr_number, "files_reviewed": len(reviewable), "event": event, "reviews": file_reviews}
