#!/usr/bin/env python3
"""Structural validation for franks-ai-skills: SKILL.md frontmatter,
plugin.json / marketplace.json shape, and eval file structure.

Not a full JSON-Schema validator — checks the specific constraints this
repo's design calls for: naming/description rules, manifest identity and
skill-list consistency between plugin.json and marketplace.json, and
required top-level keys in eval files. Frontmatter and eval-file YAML
content is parsed with a real YAML parser (PyYAML) rather than hand-rolled
pattern matching, so it's genuinely correct — not just close enough for
the cases someone thought to test.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_NAMES = {"anthropic", "claude"}
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
# SemVer 2.0.0, from semver.org's reference pattern, with [0-9] instead of
# \d so non-ASCII digits don't pass.
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse YAML frontmatter between `---` markers with a real YAML parser.

    Returns an empty dict if the document doesn't open with `---`, if it
    opens with `---` but never finds a closing `---` before EOF (unclosed
    frontmatter), if the YAML block fails to parse, or if it parses to
    something other than a mapping. Keys or values that aren't strings
    (e.g. a YAML null, a number, a nested list) are dropped rather than
    kept — a skill's `name`/`description` are always strings, so anything
    else is equivalent to the key being absent.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    closing_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = i
            break
    if closing_index is None:
        return {}

    block = "\n".join(lines[1:closing_index])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}

    if not isinstance(data, dict):
        return {}

    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def lint_skill_frontmatter(dir_name: str, frontmatter: dict[str, str]) -> list[str]:
    """Check a skill's frontmatter against the spec's naming/description rules."""
    errors: list[str] = []

    name = frontmatter.get("name")
    if not name:
        errors.append("missing 'name' in frontmatter")
    else:
        if not NAME_RE.fullmatch(name):
            errors.append(
                f"name '{name}' must be lowercase letters, numbers, and "
                "hyphens only"
            )
        if len(name) > MAX_NAME_LEN:
            errors.append(f"name '{name}' exceeds {MAX_NAME_LEN} characters")
        # Reserved words are banned anywhere in the name, not just as the
        # whole name — Anthropic's naming rule rejects "claude-tools" and
        # "anthropic-helper", not only a bare "claude"/"anthropic".
        for reserved in sorted(RESERVED_NAMES):
            if reserved in name:
                errors.append(
                    f"name '{name}' contains the reserved word '{reserved}'"
                )
        if name != dir_name:
            errors.append(
                f"name '{name}' does not match directory name '{dir_name}'"
            )

    description = frontmatter.get("description")
    if not description:
        errors.append("missing or empty 'description' in frontmatter")
    else:
        if len(description) > MAX_DESCRIPTION_LEN:
            errors.append(f"description exceeds {MAX_DESCRIPTION_LEN} characters")
        if "<" in description or ">" in description:
            errors.append("description must not contain XML-tag-like characters")

    return errors


def lint_plugin_json(data: dict) -> list[str]:
    errors: list[str] = []
    for field in ("name", "version", "description"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"'{field}' must be a non-empty string")
    name = data.get("name")
    if isinstance(name, str) and not NAME_RE.fullmatch(name):
        errors.append(
            f"name '{name}' must be lowercase letters, numbers, and hyphens only"
        )
    version = data.get("version")
    if isinstance(version, str) and version.strip() and not SEMVER_RE.fullmatch(version):
        errors.append(f"version '{version}' is not SemVer (MAJOR.MINOR.PATCH)")

    if "license" in data:
        license_ = data["license"]
        if not isinstance(license_, str) or not license_.strip():
            errors.append("'license' must be a non-empty string if present")

    if "repository" in data:
        repository = data["repository"]
        if not isinstance(repository, str) or not repository.startswith(
            ("http://", "https://")
        ):
            errors.append(
                "'repository' must be an http(s) URL string if present"
            )

    return errors


def lint_marketplace_json(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        errors.append("'name' must be a non-empty string")
    owner = data.get("owner")
    if (
        not isinstance(owner, dict)
        or not isinstance(owner.get("name"), str)
        or not owner.get("name", "").strip()
    ):
        errors.append("'owner.name' must be a non-empty string")
    if isinstance(owner, dict) and "url" in owner:
        url = owner["url"]
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            errors.append("'owner.url' must be an http(s) URL string if present")

    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append("'plugins' must be a non-empty array")
        plugins = []
    for i, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            errors.append(f"plugins[{i}] must be an object")
            continue
        name = plugin.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(
                f"plugins[{i}].name '{name}' must be lowercase letters, "
                "numbers, and hyphens only"
            )
        if "source" not in plugin:
            errors.append(f"plugins[{i}] is missing 'source'")

        # Required: in this layout Claude Code reads the marketplace entry's
        # version for update detection (see docs/releases.md).
        version = plugin.get("version")
        if version is None:
            errors.append(f"plugins[{i}] is missing 'version'")
        elif not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            errors.append(
                f"plugins[{i}].version '{version}' is not SemVer "
                "(MAJOR.MINOR.PATCH)"
            )

        if "strict" in plugin and not isinstance(plugin["strict"], bool):
            errors.append(f"plugins[{i}].strict must be a boolean if present")

        if "skills" in plugin:
            skills = plugin["skills"]
            if not isinstance(skills, list):
                errors.append(f"plugins[{i}].'skills' must be an array if present")
            else:
                for j, entry in enumerate(skills):
                    if not isinstance(entry, str):
                        errors.append(
                            f"plugins[{i}].skills[{j}] must be a string"
                        )
    return errors


def lint_manifest_consistency(
    plugin_data: dict, marketplace_data: dict, skill_dir_names: set[str]
) -> list[str]:
    """Cross-check plugin.json against marketplace.json and the actual skills/ directory."""
    errors: list[str] = []

    plugin_version = plugin_data.get("version")
    plugins = marketplace_data.get("plugins")
    if isinstance(plugins, list) and plugins and isinstance(plugins[0], dict):
        marketplace_version = plugins[0].get("version")
        if marketplace_version is not None and plugin_version != marketplace_version:
            errors.append(
                f"plugin.json version '{plugin_version}' does not match "
                f"marketplace.json plugins[0].version '{marketplace_version}'"
            )

        skills_array = plugins[0].get("skills")
        if isinstance(skills_array, list):
            listed_names = set()
            for path in skills_array:
                if isinstance(path, str):
                    listed_names.add(path.rstrip("/").rsplit("/", 1)[-1])
            for missing in sorted(skill_dir_names - listed_names):
                errors.append(
                    f"skill '{missing}' exists under skills/ but is not listed in "
                    f"plugins[0].skills in marketplace.json"
                )
            for dangling in sorted(listed_names - skill_dir_names):
                errors.append(
                    f"marketplace.json plugins[0].skills lists '{dangling}' but no "
                    f"matching directory exists under skills/"
                )

    return errors


def lint_eval_required_keys(text: str, required_keys: list[str]) -> list[str]:
    """Check an eval file's required top-level keys and the shape of their items.

    `expect` must be a list of strings — an unquoted "text: more text" item
    parses as a mapping — and each entry of `cases` must be a mapping with a
    string `prompt`.
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [f"invalid YAML ({exc})"]
    if not isinstance(data, dict):
        return ["top-level value must be a YAML mapping"]
    errors = [
        f"missing required top-level key '{key}'"
        for key in required_keys
        if key not in data
    ]

    if "expect" in data:
        expect = data["expect"]
        if not isinstance(expect, list):
            errors.append("'expect' must be a list")
        else:
            for i, item in enumerate(expect):
                if not isinstance(item, str) or not item.strip():
                    errors.append(
                        f"expect[{i}] must be a non-empty string, got "
                        f"{type(item).__name__} (quote items containing ': ')"
                    )

    if "cases" in data:
        cases = data["cases"]
        if not isinstance(cases, list):
            errors.append("'cases' must be a list")
        else:
            for i, case in enumerate(cases):
                if not isinstance(case, dict) or not isinstance(case.get("prompt"), str):
                    errors.append(f"cases[{i}] must be a mapping with a string 'prompt'")

    return errors


def check_skill_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    if not frontmatter:
        return [f"{path}: no YAML frontmatter found"]
    dir_name = path.parent.name
    return [f"{path}: {e}" for e in lint_skill_frontmatter(dir_name, frontmatter)]


def check_plugin_json_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]
    if not isinstance(data, dict):
        return [f"{path}: top-level value must be a JSON object"]
    return [f"{path}: {e}" for e in lint_plugin_json(data)]


def check_marketplace_json_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]
    if not isinstance(data, dict):
        return [f"{path}: top-level value must be a JSON object"]
    return [f"{path}: {e}" for e in lint_marketplace_json(data)]


def check_eval_file(path: Path, required_keys: list[str]) -> list[str]:
    if not path.exists():
        return [f"{path}: file does not exist"]
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return [f"{path}: file is empty"]
    return [f"{path}: {e}" for e in lint_eval_required_keys(text, required_keys)]


def find_skill_dirs(skills_root: Path) -> list[Path]:
    if not skills_root.is_dir():
        return []
    return sorted((p for p in skills_root.iterdir() if p.is_dir()), key=lambda p: p.name)


def main(root: Path = REPO_ROOT) -> int:
    errors: list[str] = []

    errors += check_plugin_json_file(root / "plugin.json")
    errors += check_marketplace_json_file(root / ".claude-plugin" / "marketplace.json")

    skills_root = root / "skills"
    evals_root = root / "evals"

    skill_names = {d.name for d in find_skill_dirs(skills_root)}
    try:
        plugin_data = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        marketplace_data = json.loads(
            (root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        errors += lint_manifest_consistency(plugin_data, marketplace_data, skill_names)
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # already reported by check_plugin_json_file / check_marketplace_json_file above

    for skill_dir in find_skill_dirs(skills_root):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill_dir}: missing SKILL.md")
            continue
        errors += check_skill_file(skill_md)

        name = skill_dir.name
        errors += check_eval_file(evals_root / name / "routing.yaml", ["cases"])
        errors += check_eval_file(evals_root / name / "behavior.yaml", ["prompt", "expect"])
        for scenario in sorted((evals_root / name).glob("behavior-*.yaml")):
            errors += check_eval_file(scenario, ["prompt", "expect"])

    errors += check_eval_file(evals_root / "catalog" / "collisions.yaml", ["cases"])

    if errors:
        print(f"tools/checks.py: {len(errors)} problem(s) found:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("tools/checks.py: all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
