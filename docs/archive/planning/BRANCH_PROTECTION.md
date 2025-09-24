# Branch protection recommendations

For a smooth PR flow and high signal in CI, set these protections on `main` in your GitHub repo settings.

- Require a pull request before merging
  - Require approvals: 1+ (2+ for riskier changes)
  - Dismiss stale approvals when new commits are pushed
- Require status checks to pass before merging
  - Required checks:
    - Trunk Lint (trunk.yml)
    - CI (ci.yml)
- Require conversation resolution before merging
- Require branches to be up to date before merging (optional if using automerge)
- Restrict who can push to matching branches (allow admins/maintainers only)
- Enforce for administrators (recommended)

Tips:

- Use branch rules to also protect `release/*` branches if you cut releases.
- Consider enabling auto-merge for PRs that pass all checks and have at least one approval.
