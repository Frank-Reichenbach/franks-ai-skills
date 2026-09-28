# Codex: commit attribution

Codex adds its own co-author trailer only when the `codex_git_commit`
feature flag is enabled. It then appends
`Co-authored-by: <commit_attribution>`, with
`Codex <noreply@openai.com>` when `commit_attribution` is unset. That
trailer breaks `git-flow`'s attribution rules: an AI model gets
`Assisted-by: <model> (code generation)`, without an email address.
Source: openai/codex#21379, `docs/config.md`, "Commit attribution".

## Turning it off

With the feature enabled, set an empty `commit_attribution` in
`~/.codex/config.toml`:

```toml
commit_attribution = ""

[features]
codex_git_commit = true
```

An empty or whitespace-only value disables the trailer. With the
feature flag off, Codex adds no trailer and nothing needs to change.
Whether a project-level `.codex/config.toml` also takes this setting
is not documented — check before relying on it.
