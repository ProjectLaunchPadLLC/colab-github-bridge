"""
colab/colab_helper.py

Small helper utilities used by the Colab notebook to interact with a GitHub repository.
Designed to be safe for interactive use in ephemeral runtimes (e.g., Colab).
Do not store tokens in files; pass them at runtime and clear them from memory when finished.
"""

from typing import Optional, Dict, Any
import os
import subprocess
import requests
import json
import shutil
from pathlib import Path
from datetime import datetime

# ---- Utility helpers -------------------------------------------------------

def run_cmd(cmd: list, cwd: Optional[str] = None, check: bool = True) -> Dict[str, Any]:
    """
    Run a shell command and return a dict with returncode, stdout, stderr.
    Uses subprocess.run to avoid shell=True where possible.
    """
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    result = {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr}")
    return result

# ---- Git / repo helpers ----------------------------------------------------

def configure_git(user_name: str, user_email: str) -> None:
    """Configure global git user.name and user.email for the runtime."""
    run_cmd(["git", "config", "--global", "user.name", user_name])
    run_cmd(["git", "config", "--global", "user.email", user_email])

def clone_repo(username: str, repo: str, token: str, dest: Optional[str] = None) -> Path:
    """
    Clone a GitHub repository using an HTTPS URL with token authentication.
    Returns the Path to the cloned repository.
    WARNING: token is used only in the runtime command and should not be persisted.
    """
    if dest is None:
        dest = f"/content/{repo}"
    dest_path = Path(dest)
    if dest_path.exists():
        shutil.rmtree(dest_path)
    clone_url = f"https://{username}:{token}@github.com/{username}/{repo}.git"
    run_cmd(["git", "clone", clone_url, str(dest_path)])
    return dest_path

def set_remote_with_token(repo_dir: Path, username: str, repo: str, token: str) -> None:
    """Set the origin remote URL to include the token for authenticated pushes."""
    push_url = f"https://{username}:{token}@github.com/{username}/{repo}.git"
    run_cmd(["git", "remote", "set-url", "origin", push_url], cwd=str(repo_dir))

def create_branch(repo_dir: Path, branch: str) -> None:
    """Create and checkout a new branch in the repository."""
    run_cmd(["git", "checkout", "-b", branch], cwd=str(repo_dir))

def commit_changes(repo_dir: Path, message: str, paths: Optional[list] = None) -> bool:
    """
    Stage and commit changes. If paths is None, stages all changes.
    Returns True if a commit was created, False if there were no changes to commit.
    """
    if paths:
        run_cmd(["git", "add"] + paths, cwd=str(repo_dir))
    else:
        run_cmd(["git", "add", "-A"], cwd=str(repo_dir))

    # Attempt commit; if nothing to commit, git returns non-zero and we catch it
    try:
        run_cmd(["git", "commit", "-m", message], cwd=str(repo_dir))
        return True
    except RuntimeError as e:
        # Common case: "nothing to commit"
        stderr = str(e)
        if "nothing to commit" in stderr or "no changes added to commit" in stderr:
            return False
        raise

def push_branch(repo_dir: Path, branch: str, set_upstream: bool = True) -> None:
    """Push the current branch to origin. If set_upstream is True, sets upstream on first push."""
    cmd = ["git", "push"]
    if set_upstream:
        cmd += ["--set-upstream", "origin", branch]
    else:
        cmd += ["origin", branch]
    run_cmd(cmd, cwd=str(repo_dir))

# ---- GitHub API helpers ----------------------------------------------------

def create_pull_request(username: str, repo: str, token: str, head: str, base: str, title: str, body: str) -> Dict[str, Any]:
    """
    Create a pull request via the GitHub REST API.
    Returns the parsed JSON response.
    """
    url = f"https://api.github.com/repos/{username}/{repo}/pulls"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"title": title, "head": head, "base": base, "body": body}
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create PR: {resp.status_code} {resp.text}")
    return resp.json()

# ---- Convenience high-level flow -------------------------------------------

def safe_colab_update(
    username: str,
    repo: str,
    token: str,
    branch: str = "colab/auto-update",
    base: str = "main",
    commit_message: Optional[str] = None,
    repo_dest: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High-level helper that:
      - clones the repo
      - creates a branch
      - writes a small timestamp file as a demo change
      - commits and pushes the branch
      - creates a PR into base
    Returns a dict with keys: repo_dir, branch, pr_url (if created), commit_made (bool).
    """
    if commit_message is None:
        commit_message = f"Colab: automated update at {datetime.utcnow().isoformat()}Z"

    repo_dir = clone_repo(username, repo, token, dest=repo_dest)
    try:
        configure_git(user_name=username, user_email=f"{username}@users.noreply.github.com")
        create_branch(repo_dir, branch)

        # Demo change: write a timestamp file. Replace with real processing outputs.
        demo_file = repo_dir / "colab_update.txt"
        demo_file.write_text(f"Updated from Colab at {datetime.utcnow().isoformat()}Z\n")

        commit_made = commit_changes(repo_dir, commit_message, paths=[str(demo_file)])
        set_remote_with_token(repo_dir, username, repo, token)
        push_branch(repo_dir, branch, set_upstream=True)

        pr = create_pull_request(username, repo, token, head=branch, base=base, title=commit_message, body="Automated PR created from Colab.")
        pr_url = pr.get("html_url")
        return {"repo_dir": str(repo_dir), "branch": branch, "commit_made": commit_made, "pr_url": pr_url}
    finally:
        # Do not remove the repo_dir here; let the caller decide. Caller should clear token variable.
        pass

# ---- Cleanup helpers -------------------------------------------------------

def remove_cloned_repo(repo_dir: str) -> None:
    """Remove the cloned repository directory from the runtime filesystem."""
    path = Path(repo_dir)
    if path.exists():
        shutil.rmtree(path)

def clear_token(token_var_name: str, globals_dict: dict) -> None:
    """
    Clear a token variable from the provided globals dict by name.
    Example: clear_token('token', globals())
    """
    if token_var_name in globals_dict:
        globals_dict[token_var_name] = None

# ---- Example usage guard ---------------------------------------------------

if __name__ == "__main__":
    # Minimal demo when run directly (not used in Colab import)
    print("colab_helper module. Import and call functions from your notebook.")
