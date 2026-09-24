# Portability

This repo publishes two manifests; neither is generated from the other:

- `.claude-plugin/marketplace.json` — read by Claude Code, and also recognized by the ChatGPT desktop app as a "legacy-compatible" marketplace format (so registering this repo with `codex plugin marketplace add` works off this same file — no `.agents/plugins/marketplace.json` needed). Defines the `franks-ai-skills` marketplace and the `frank` plugin entry.
- `plugin.json` (repo root) — an [Agent Plugins 1.0](https://agent-plugins.org/specification) manifest. Skills under `skills/` are auto-discovered per that spec. Read by Codex and other Agent-Plugins-1.0-conformant clients. Codex takes the marketplace entry from `.claude-plugin/marketplace.json` but uses this file as the plugin's manifest whenever its `$schema` is an agent-plugins.org URI: its `version` wins over the marketplace entry's (source: `openai/codex`, `utils/plugins/src/plugin_namespace.rs` and `core-plugins/src/store.rs`, "A real plugin manifest always wins"). Claude Code does not treat it as a plugin manifest — the path it looks for is `.claude-plugin/plugin.json`, which this repo doesn't have — but "ignores it" would be too strong: `claude plugin tag` reads the root file for the plugin's name and version when no `.claude-plugin/plugin.json` exists. Don't assume either way for a given Claude Code command; check. See `docs/releases.md` for what this means for version resolution.

Both point at the same canonical `skills/` directory. Nothing is generated or duplicated between them.

Because of this, every `SKILL.md` body should stay vendor-neutral — see the "Vendor-neutral wording" section in the `skill-writing` skill. The manifests are allowed to be client-specific; the skill content underneath them isn't.

OpenCode reads neither manifest. It discovers skill folders directly (`.opencode/skills/`, `.claude/skills/`, `.agents/skills/` and their global equivalents) and has no update detection for local skill folders.
