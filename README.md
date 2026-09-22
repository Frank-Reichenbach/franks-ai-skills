# franks-ai-skills

Frank's personal AI skill collection — a Claude Code marketplace and an
[Agent Plugins 1.0](https://agent-plugins.org/) package.

## Install

**Claude Code:**

```
/plugin marketplace add Frank-Reichenbach/franks-ai-skills
/plugin install frank@franks-ai-skills
```

**Codex / other [Agent Plugins 1.0](https://agent-plugins.org/) clients:**
this repo's root `plugin.json` is a standalone, valid Agent Plugins 1.0
package on its own — `skills/` is auto-discovered per that spec, no extra
step needed if your client lets you point directly at a plugin's path or
repo.

For discovery through Codex's own marketplace UI, register this repo as a
marketplace source:

```
codex plugin marketplace add Frank-Reichenbach/franks-ai-skills
```

The ChatGPT desktop app reads `.claude-plugin/marketplace.json` as a
recognized ("legacy-compatible") marketplace format, so this repo's
existing Claude Code marketplace file doubles as the Codex catalog too —
no separate `.agents/plugins/marketplace.json` needed. From there,
installing the plugin happens in the ChatGPT desktop app's Plugins
Directory, not via a documented single-plugin CLI command; see
[Codex's plugin docs](https://developers.openai.com/codex/plugins/build)
for anything that's changed since.

## Structure

- `skills/<name>/SKILL.md` — canonical source for every skill.
- `.claude-plugin/marketplace.json` — Claude Code marketplace and the `frank` plugin entry.
- `plugin.json` — Agent Plugins 1.0 manifest.
- `evals/<name>/` — routing and behavioral test cases per skill.
- `docs/` — repo-wide policy (security, releases, portability).
- `tools/` — `checks.py`, the structural validator, plus `validate.sh` and `requirements.txt`.
- `tools/tests/` — the validator's own unit test suite.

See `skills/skill-writing/SKILL.md` for how to add a new skill.

## Validate

Prerequisites: `python3`, the packages in `tools/requirements.txt`
(`pip install -r tools/requirements.txt`), and the `claude` CLI.

```
./tools/validate.sh
```

Runs on every pull request via `.github/workflows/validate.yml`. It runs the
validator's own unit test suite (`python3 -m unittest discover -s tools/tests`)
before the structural checks.
