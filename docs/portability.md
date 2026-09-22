# Portability

This repo publishes two manifests that don't interact:

- `.claude-plugin/marketplace.json` — read by Claude Code, and also recognized by the ChatGPT desktop app as a "legacy-compatible" marketplace format (so registering this repo with `codex plugin marketplace add` works off this same file — no `.agents/plugins/marketplace.json` needed). Defines the `franks-ai-skills` marketplace and the `frank` plugin entry.
- `plugin.json` (repo root) — an [Agent Plugins 1.0](https://agent-plugins.org/specification) manifest. Skills under `skills/` are auto-discovered per that spec. Read by Codex and other Agent-Plugins-1.0-conformant clients; Claude Code ignores it.

Both point at the same canonical `skills/` directory. Nothing is generated or duplicated between them.

Because of this, every `SKILL.md` body should stay vendor-neutral — see the "Vendor-neutral wording" section in the `skill-writing` skill. The manifests are allowed to be client-specific; the skill content underneath them isn't.
