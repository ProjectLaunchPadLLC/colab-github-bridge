#!/usr/bin/env python3
"""
Create or update a file in a GitHub repository using the Contents API.

Usage examples:
  python scripts/create_github_file.py --owner alice --repo myrepo --path "notes/from-colab.txt" --message "Add note" --content-file ./local_note.txt
  python scripts/create_github_file.py --owner alice --repo myrepo --path "notes/quick.txt" --message "Add quick note" --content "Hello from Colab" --branch feature/colab
"""
import os
import sys
import base64
import json
import argparse
from getpass import getpass
from urllib.parse import quote_plus

try:
    import requests
except Exception:
    print("Missing dependency 'requests'. Install with: pip install requests", file=sys.stderr)
    sys.exit(2)

API_BASE = "https://api.github.com"

def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    # Prompt only if running interactively
    try:
        return getpass("GitHub Personal Access Token (used only in this session): ").strip()
    except Exception:
        return None

def file_exists(owner, repo, path, branch, headers):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{quote_plus(path)}"
    params = {"ref": branch} if branch else {}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()  # returns dict with 'sha' etc.
    if r.status_code == 404:
        return None
    r.raise_for_status()

def create_or_update_file(owner, repo, path, content_bytes, message, branch, force_update=False):
    token = get_token()
    if not token:
        raise SystemExit("No GitHub token provided.")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{quote_plus(path)}"
    encoded = base64.b64encode(content_bytes).decode("ascii")
    payload = {"message": message, "content": encoded}
    if branch:
        payload["branch"] = branch

    existing = file_exists(owner, repo, path, branch, headers)
    if existing:
        if not force_update:
            raise SystemExit(f"File already exists at {path} on branch {branch or 'default'}. Use --force to update.")
        payload["sha"] = existing.get("sha")

    r = requests.put(url, headers=headers, data=json.dumps(payload))
    if r.status_code in (200, 201):
        return r.json()
    else:
        # surface helpful error
        try:
            err = r.json()
        except Exception:
            err = r.text
        raise SystemExit(f"GitHub API error ({r.status_code}): {err}")

def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--owner", required=True, help="GitHub owner or org")
    p.add_argument("--repo", required=True, help="Repository name")
    p.add_argument("--path", required=True, help="Target path in repo (e.g., folder/file.txt)")
    p.add_argument("--message", required=True, help="Commit message")
    p.add_argument("--content-file", help="Local file to read content from")
    p.add_argument("--content", help="Inline content (mutually exclusive with --content-file)")
    p.add_argument("--branch", help="Target branch (optional). If omitted, default branch is used")
    p.add_argument("--force", action="store_true", help="If set, update file if it already exists")
    args = p.parse_args(argv)

    if bool(args.content_file) == bool(args.content):
        p.error("Specify exactly one of --content-file or --content")

    if args.content_file:
        with open(args.content_file, "rb") as fh:
            content_bytes = fh.read()
    else:
        content_bytes = args.content.encode("utf-8")

    result = create_or_update_file(args.owner, args.repo, args.path, content_bytes, args.message, args.branch, force_update=args.force)
    print("Success. Response:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main(sys.argv[1:])
