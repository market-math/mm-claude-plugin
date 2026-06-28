# mm-claude-plugin

## Versioning

This plugin follows semantic versioning (MAJOR.MINOR.PATCH).

### During initial development (0.x.x)
- **MINOR** - new features or breaking changes
- **PATCH** - bug fixes

### Post 1.0.0
- **MAJOR** - breaking changes
- **MINOR** - new features (backward-compatible)
- **PATCH** - bug fixes (backward-compatible)

### When to update the version

The `version` field in `.claude-plugin/plugin.json` is the update cache key: with an explicit
version set, Claude Code delivers changes to installed copies only when this field is bumped. So
bump it (choosing MAJOR / MINOR / PATCH per the rules above) only when you change something a plugin
consumer actually loads. For this repo that means `skills/`, `agents/`, `hooks/` (`hooks.json` and
the scripts it references), or `.claude-plugin/plugin.json` metadata. Other plugin component types
exist; see the Claude Code plugin docs (plugins-reference, "Version management") for the current
authoritative list.

Do not bump the version for changes a consumer never loads, such as developer tooling
(`.worktree.conf`), CI workflows under `.github/`, `README.md`, this `CLAUDE.md`, or `.gitignore`.
A plugin-root `CLAUDE.md` is not shipped as consumer context, so editing it (including this
section) does not require a bump.
