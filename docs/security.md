# Security

Rules for anything under `skills/` that bundles executable content (`scripts/`, hooks, or an MCP server reference):

1. Review the script before merging — read it, don't skim it. If you didn't write it yourself, treat it like an unreviewed third-party dependency.
2. Never commit secrets, tokens, or credentials, in a script or in a fixture.
3. Pin third-party sources you depend on (a commit SHA or tag, not a floating branch) so an upstream change can't silently alter behavior.
4. Document required network access and required external binaries directly in the skill's `SKILL.md` — don't leave an agent to discover a missing dependency at runtime.
5. A skill that can take destructive or privileged action (deletes files, pushes to a remote, calls a paid API) gets called out explicitly in its own `description`, so it's never invoked by accident.
6. Don't rely on `SKILL.md` prose ("never run destructive commands") as a security boundary — it's a hint to the agent, not an enforcement mechanism. Real enforcement is the host's tool-permission system.
