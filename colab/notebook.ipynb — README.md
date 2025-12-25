# colab/notebook.ipynb — README

## Purpose
This notebook is a ready-to-run Google Colab template that demonstrates a secure, minimal workflow for interacting with a GitHub repository from a Colab runtime. It shows how to:

- Prompt for a GitHub Personal Access Token (PAT) at runtime (not stored).
- Clone a repository using the PAT for authentication.
- Run project scripts and tests.
- Make a small change, commit to a new branch, and push the branch.
- Create a Pull Request via the GitHub REST API.
- Clear secrets from memory and clean up the runtime.

## How to use
1. **Open the notebook in Google Colab.**  
   - If the notebook is stored in the repo, open it via the GitHub UI or Colab's "Open notebook" → "GitHub" option.

2. **Set your GitHub username and repo (optional).**  
   - By default the notebook reads `GITHUB_USER` and `GITHUB_REPO` from environment variables if set. Otherwise replace the placeholder values in the second cell before running.

3. **Run cells in order.**  
   - When prompted, paste your GitHub PAT into the input box. The token is used only in memory for the session.

4. **Review changes on GitHub.**  
   - The notebook pushes to a branch named `colab/auto-update` and attempts to create a PR into `main`. Adjust the base branch if your repository uses a different default branch.

5. **Cleanup.**  
   - The final cell clears the token variable and removes the cloned repository from the Colab VM.

## Security guidance
- **Never commit tokens** or other secrets to the repository. This notebook intentionally prompts for the PAT at runtime.
- **Use minimal scopes** for the PAT. For typical push/PR workflows, `repo` is sufficient for private repos; for public-only operations, narrower scopes may be possible.
- **Prefer PRs over direct pushes** to protected branches to enable review and CI checks.
- **Rotate tokens** regularly and revoke them if you suspect compromise.

## Customization tips
- Replace the demo change (`colab_update.txt`) with your actual processing outputs or artifacts.
- If you prefer OAuth, install and use the `gh` CLI and run `gh auth login` interactively instead of embedding the token in the clone URL.
- Add additional validation steps (linting, unit tests) before committing and pushing.

## Troubleshooting
- If `git clone` fails, ensure the token has the correct scopes and the `GITHUB_USER`/`GITHUB_REPO` values are correct.
- If `git push` fails, check branch protection rules and consider pushing to a different branch or creating a PR via the API.
- If the PR creation returns an error, inspect the API response printed by the notebook for details.

## License
Follow the repository license. This notebook is provided as an example; adapt it to your security policies and workflows.
