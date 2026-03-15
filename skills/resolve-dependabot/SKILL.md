---
name: resolve-dependabot
description: Resolve GitHub Dependabot security alerts by updating vulnerable dependencies, recompiling requirements, and submitting PRs. Use when working on dependabot alerts, security vulnerabilities, or dependency patching.
argument-hint: [severity]
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, AskUserQuestion
---

Resolve open Dependabot security alerts for this repository.

## Preamble: Load Context

1. Detect the repo and default branch dynamically:
```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
```

2. If `$SHIPAWARE_DOCS_PATH` is set, read the runbook for additional edge-case context:
   - `$SHIPAWARE_DOCS_PATH/shipAware/ops/runbooks/dependabot-critical-patches.md`
   - This is optional — proceed with the built-in instructions below if the runbook is unavailable.

## Step 1: Fetch & Triage Open Alerts

Fetch all open Dependabot alerts:
```bash
gh api "repos/${REPO}/dependabot/alerts" --jq '[.[] | select(.state=="open") | {number: .number, severity: .security_advisory.severity, package: .security_vulnerability.package.name, current_version: .security_vulnerability.first_patched_version.identifier, vulnerable_range: .security_vulnerability.vulnerable_version_range, manifest: .dependency.manifest_path, cve: (.security_advisory.cve_id // .security_advisory.ghsa_id), summary: .security_advisory.summary}]'
```

If `$ARGUMENTS` contains a severity filter (e.g. `critical`, `high`, `medium`, `low`), filter to only that severity. Otherwise show all open alerts.

Present a summary table sorted by severity (critical > high > medium > low):

| # | Severity | Package | Vulnerable Range | Fixed Version | Manifest | CVE/GHSA | Summary |
|---|----------|---------|------------------|---------------|----------|----------|---------|

Ask the user which severity tier(s) to resolve. Suggest starting with the highest severity.

## Step 2: Process Each Severity Tier

For each selected severity tier (starting with the highest), repeat steps 2a–2e.

### Step 2a: Create Security Branch

- Ensure we're on a clean default branch, pulled to latest:
```bash
git checkout ${DEFAULT_BRANCH} && git pull origin ${DEFAULT_BRANCH}
```
- Verify working tree is clean (`git status --porcelain`). If not, ask user how to proceed.
- Create a branch: `security/<package-names>` where `<package-names>` is a dash-separated list of the affected packages in this tier (e.g. `security/jinja2-werkzeug`).

### Step 2b: Update Dependencies

For each alert in this tier, determine if the package is a **direct** or **transitive** dependency:

```bash
grep -r "^<package-name>" requirements/*.in
```

- **Direct dependency** (found in a `.in` file): Edit the `.in` file to update the version pin to the fixed version.
- **Transitive dependency** (not in any `.in` file): Run:
  ```bash
  python compose/local/compile_requirements.py -P <package-name>
  ```

### Step 2c: Recompile Requirements

For direct dependency changes, recompile **without** the `--upgrade` flag:
```bash
python compose/local/compile_requirements.py
```

After recompilation, verify the fix:
```bash
git diff requirements/
grep <package-name> requirements/*.txt
```

Confirm the resolved versions match or exceed Dependabot's recommended fix versions.

### Step 2d: Commit & PR

- Commit with format:
  ```text
  fix: patch <severity> vulnerabilities in <packages>

  - <CVE-1>: <package> <old-version> -> <new-version>
  - <CVE-2>: <package> <old-version> -> <new-version>
  ```
- Push and create a PR against the default branch:
  ```bash
  gh pr create --base ${DEFAULT_BRANCH} --title "fix: patch <severity> dependabot vulnerabilities in <packages>" --body "$(cat <<'EOF'
  ## Security Patch — <Severity> Vulnerabilities

  ### Changes
  - <package>: <old-version> → <new-version>

  ### Advisories
  - [<CVE/GHSA>](<advisory-url>): <summary>

  ### Notes
  - Requirements recompiled via `compile_requirements.py`
  - CI will validate tests automatically
  EOF
  )"
  ```
- Add the `security` label:
  ```bash
  gh pr edit --add-label security
  ```

### Step 2e: Return to Default Branch

```bash
git checkout ${DEFAULT_BRANCH}
```

Prepare for the next severity tier if applicable.

## Step 3: Summary

Present a final summary of all PRs created:

| Severity | Packages | PR | Link |
|----------|----------|----|------|

Note that CI will automatically validate tests for each PR.
