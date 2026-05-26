import os
import requests


class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ["GITHUB_TOKEN"]
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_pr_details(self, owner: str, repo: str, pr_number: int) -> dict:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def post_review_comment(self, owner: str, repo: str, pr_number: int,
                             commit_sha: str, path: str, line: int, body: str):
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        payload = {
            "body": body,
            "commit_id": commit_sha,
            "path": path,
            "line": line,
            "side": "RIGHT"
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code not in (200, 201):
            print(f"  Warning: Could not post inline comment on {path}:{line} — {response.json().get('message')}")
        return response

    def post_pr_comment(self, owner: str, repo: str, pr_number: int, body: str):
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        response = requests.post(url, headers=self.headers, json={"body": body})
        response.raise_for_status()
        return response.json()

    def submit_review(self, owner: str, repo: str, pr_number: int,
                      commit_sha: str, body: str, event: str):
        """event: APPROVE | REQUEST_CHANGES | COMMENT"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        # GitHub requires body to be non-empty for REQUEST_CHANGES and COMMENT
        safe_body = body.strip() if body and body.strip() else "Review completed."
        payload = {
            "commit_id": commit_sha,
            "body": safe_body,
            "event": event
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if not response.ok:
            error_data = response.json()
            errors = error_data.get("errors", [])
            # GitHub does not allow APPROVE or REQUEST_CHANGES on your own PR
            # Fall back to COMMENT event which is always allowed
            if any("own pull request" in str(e) for e in errors) and event != "COMMENT":
                print(f"  Note: Cannot submit {event} on own PR - falling back to COMMENT")
                payload["event"] = "COMMENT"
                response = requests.post(url, headers=self.headers, json=payload)
                if response.ok:
                    return response.json()
            print(f"  Review submission error {response.status_code}: {error_data}")
            self.post_pr_comment(owner, repo, pr_number, safe_body)
            return None
        return response.json()
