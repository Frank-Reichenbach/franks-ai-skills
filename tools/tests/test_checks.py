#!/usr/bin/env python3
"""Unit tests for tools/checks.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import checks  # noqa: E402


class ParseFrontmatterTests(unittest.TestCase):
    def test_parses_simple_keys(self):
        text = "---\nname: skill-writing\ndescription: Does a thing.\n---\nBody text.\n"
        result = checks.parse_frontmatter(text)
        self.assertEqual(
            result, {"name": "skill-writing", "description": "Does a thing."}
        )

    def test_strips_quotes(self):
        text = '---\nname: "skill-writing"\n---\n'
        result = checks.parse_frontmatter(text)
        self.assertEqual(result["name"], "skill-writing")

    def test_no_frontmatter_returns_empty(self):
        self.assertEqual(checks.parse_frontmatter("# Just a heading\n"), {})

    def test_unclosed_frontmatter_returns_empty(self):
        text = (
            "---\n"
            "name: test-skill\n"
            "description: A test.\n"
            "This is body text with no closing delimiter.\n"
            "More body text.\n"
        )
        self.assertEqual(checks.parse_frontmatter(text), {})

    def test_folded_block_scalar_is_joined_with_spaces(self):
        text = (
            "---\n"
            "name: test-skill\n"
            "description: >\n"
            "  Reviews code for bugs and style issues.\n"
            "  Use when reviewing a pull request.\n"
            "---\n"
        )
        result = checks.parse_frontmatter(text)
        self.assertEqual(
            result["description"],
            "Reviews code for bugs and style issues. Use when reviewing a pull request.",
        )

    def test_literal_block_scalar_is_joined_with_newlines(self):
        text = (
            "---\n"
            "name: test-skill\n"
            "description: |\n"
            "  Line one.\n"
            "  Line two.\n"
            "---\n"
        )
        result = checks.parse_frontmatter(text)
        self.assertEqual(result["description"], "Line one.\nLine two.")

    def test_empty_stripped_block_scalar_is_empty_string(self):
        text = "---\nname: test-skill\ndescription: |-\n---\n"
        result = checks.parse_frontmatter(text)
        self.assertEqual(result["description"], "")

    def test_null_literal_is_treated_as_absent(self):
        text = "---\nname: test-skill\ndescription: null\n---\n"
        result = checks.parse_frontmatter(text)
        self.assertNotIn("description", result)

    def test_tilde_null_literal_is_treated_as_absent(self):
        text = "---\nname: test-skill\ndescription: ~\n---\n"
        result = checks.parse_frontmatter(text)
        self.assertNotIn("description", result)

    def test_value_with_trailing_comment_is_stripped(self):
        text = "---\nname: test-skill\ndescription: null # TODO\n---\n"
        result = checks.parse_frontmatter(text)
        self.assertNotIn("description", result)

    def test_empty_value_with_trailing_comment_is_absent(self):
        text = "---\nname: test-skill\ndescription: # TODO\n---\n"
        result = checks.parse_frontmatter(text)
        self.assertNotIn("description", result)

    def test_literal_block_with_trailing_comment_on_header_is_parsed(self):
        text = (
            "---\n"
            "name: test-skill\n"
            "description: | # TODO\n"
            "  actual content here\n"
            "---\n"
        )
        result = checks.parse_frontmatter(text)
        self.assertEqual(result["description"], "actual content here")

    def test_folded_block_with_trailing_comment_on_header_is_parsed(self):
        text = (
            "---\n"
            "name: test-skill\n"
            "description: > # routing\n"
            "  Reviews code for bugs and style issues.\n"
            "  Use when reviewing a pull request.\n"
            "---\n"
        )
        result = checks.parse_frontmatter(text)
        self.assertEqual(
            result["description"],
            "Reviews code for bugs and style issues. Use when reviewing a pull request.",
        )

    def test_plain_scalar_with_embedded_colon_is_invalid_yaml(self):
        # `key: value` inside an unquoted plain scalar is genuinely invalid
        # YAML (ambiguous with a nested mapping) - a real parser rejects it
        # rather than silently accepting whatever follows the first colon.
        text = "---\nname: test-skill\ndescription: Reviews code: finds bugs.\n---\n"
        result = checks.parse_frontmatter(text)
        self.assertEqual(result, {})


class LintSkillFrontmatterTests(unittest.TestCase):
    def test_valid_frontmatter_has_no_errors(self):
        errors = checks.lint_skill_frontmatter(
            "skill-writing",
            {
                "name": "skill-writing",
                "description": "Does a thing. Use when doing it.",
            },
        )
        self.assertEqual(errors, [])

    def test_missing_name(self):
        errors = checks.lint_skill_frontmatter("skill-writing", {"description": "x"})
        self.assertIn("missing 'name' in frontmatter", errors)

    def test_name_with_uppercase_is_rejected(self):
        errors = checks.lint_skill_frontmatter(
            "Skill-Writing", {"name": "Skill-Writing", "description": "x"}
        )
        self.assertTrue(any("lowercase letters" in e for e in errors))

    def test_name_mismatch_with_directory(self):
        errors = checks.lint_skill_frontmatter(
            "skill-writing", {"name": "other-name", "description": "x"}
        )
        self.assertTrue(any("does not match directory name" in e for e in errors))

    def test_reserved_name_rejected(self):
        errors = checks.lint_skill_frontmatter(
            "claude", {"name": "claude", "description": "x"}
        )
        self.assertTrue(any("reserved word" in e for e in errors))

    def test_missing_description(self):
        errors = checks.lint_skill_frontmatter("skill-writing", {"name": "skill-writing"})
        self.assertIn("missing or empty 'description' in frontmatter", errors)

    def test_description_too_long_is_rejected(self):
        errors = checks.lint_skill_frontmatter(
            "skill-writing", {"name": "skill-writing", "description": "x" * 1025}
        )
        self.assertTrue(any("exceeds 1024 characters" in e for e in errors))

    def test_description_with_xml_tag_is_rejected(self):
        errors = checks.lint_skill_frontmatter(
            "skill-writing",
            {"name": "skill-writing", "description": "Do <b>this</b>."},
        )
        self.assertTrue(any("XML-tag-like" in e for e in errors))

    def test_valid_folded_description_from_real_file_is_not_rejected(self):
        # Regression test: a properly written `description: >` block scalar
        # must not be misread as the literal string ">" and flagged as
        # containing XML-tag-like characters.
        text = (
            "---\n"
            "name: skill-writing\n"
            "description: >\n"
            "  Reviews code for bugs and style issues.\n"
            "  Use when reviewing a pull request.\n"
            "---\n"
        )
        frontmatter = checks.parse_frontmatter(text)
        errors = checks.lint_skill_frontmatter("skill-writing", frontmatter)
        self.assertEqual(errors, [])


class LintPluginJsonTests(unittest.TestCase):
    def test_valid_plugin_has_no_errors(self):
        errors = checks.lint_plugin_json(
            {"name": "frank", "version": "0.1.0", "description": "Frank's skills"}
        )
        self.assertEqual(errors, [])

    def test_missing_field_is_rejected(self):
        errors = checks.lint_plugin_json({"name": "frank", "version": "0.1.0"})
        self.assertTrue(any("'description'" in e for e in errors))

    def test_bad_name_format_is_rejected(self):
        errors = checks.lint_plugin_json(
            {"name": "Frank_Skills", "version": "0.1.0", "description": "x"}
        )
        self.assertTrue(any("lowercase letters" in e for e in errors))

    def test_empty_license_is_rejected(self):
        errors = checks.lint_plugin_json(
            {
                "name": "frank",
                "version": "0.1.0",
                "description": "x",
                "license": "",
            }
        )
        self.assertTrue(any("license" in e for e in errors))

    def test_non_string_license_is_rejected(self):
        errors = checks.lint_plugin_json(
            {
                "name": "frank",
                "version": "0.1.0",
                "description": "x",
                "license": 42,
            }
        )
        self.assertTrue(any("license" in e for e in errors))

    def test_valid_license_has_no_errors(self):
        errors = checks.lint_plugin_json(
            {
                "name": "frank",
                "version": "0.1.0",
                "description": "x",
                "license": "GPL-3.0-or-later",
            }
        )
        self.assertEqual(errors, [])

    def test_repository_not_a_url_is_rejected(self):
        errors = checks.lint_plugin_json(
            {
                "name": "frank",
                "version": "0.1.0",
                "description": "x",
                "repository": "not-a-url",
            }
        )
        self.assertTrue(any("repository" in e for e in errors))

    def test_valid_repository_has_no_errors(self):
        errors = checks.lint_plugin_json(
            {
                "name": "frank",
                "version": "0.1.0",
                "description": "x",
                "repository": "https://github.com/Frank-Reichenbach/franks-ai-skills",
            }
        )
        self.assertEqual(errors, [])


class LintMarketplaceJsonTests(unittest.TestCase):
    def test_valid_marketplace_has_no_errors(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank Reichenbach"},
            "plugins": [{"name": "frank", "source": "./"}],
        }
        self.assertEqual(checks.lint_marketplace_json(data), [])

    def test_empty_plugins_is_rejected(self):
        data = {"name": "franks-ai-skills", "owner": {"name": "Frank"}, "plugins": []}
        errors = checks.lint_marketplace_json(data)
        self.assertTrue(any("non-empty array" in e for e in errors))

    def test_plugin_missing_source_is_rejected(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank"},
            "plugins": [{"name": "frank"}],
        }
        errors = checks.lint_marketplace_json(data)
        self.assertTrue(any("missing 'source'" in e for e in errors))

    def test_non_bool_strict_is_rejected(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank"},
            "plugins": [{"name": "frank", "source": "./", "strict": "false"}],
        }
        errors = checks.lint_marketplace_json(data)
        self.assertTrue(any("strict" in e for e in errors))

    def test_bool_strict_has_no_errors(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank"},
            "plugins": [{"name": "frank", "source": "./", "strict": False}],
        }
        self.assertEqual(checks.lint_marketplace_json(data), [])

    def test_non_string_skills_entry_is_rejected(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank"},
            "plugins": [
                {"name": "frank", "source": "./", "skills": ["./skills/x", 42]}
            ],
        }
        errors = checks.lint_marketplace_json(data)
        self.assertTrue(any("skills[1]" in e for e in errors))

    def test_non_list_skills_is_rejected(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank"},
            "plugins": [{"name": "frank", "source": "./", "skills": "./skills/x"}],
        }
        errors = checks.lint_marketplace_json(data)
        self.assertTrue(any("'skills' must be an array" in e for e in errors))

    def test_owner_url_not_a_url_is_rejected(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {"name": "Frank", "url": "not-a-url"},
            "plugins": [{"name": "frank", "source": "./"}],
        }
        errors = checks.lint_marketplace_json(data)
        self.assertTrue(any("owner.url" in e for e in errors))

    def test_owner_url_valid_has_no_errors(self):
        data = {
            "name": "franks-ai-skills",
            "owner": {
                "name": "Frank",
                "url": "https://github.com/Frank-Reichenbach/franks-ai-skills",
            },
            "plugins": [{"name": "frank", "source": "./"}],
        }
        self.assertEqual(checks.lint_marketplace_json(data), [])


class LintManifestConsistencyTests(unittest.TestCase):
    def test_matching_skills_and_versions_has_no_errors(self):
        plugin_data = {"name": "frank", "version": "0.1.0", "description": "x"}
        marketplace_data = {
            "plugins": [
                {
                    "name": "frank",
                    "version": "0.1.0",
                    "skills": ["./skills/skill-writing"],
                }
            ]
        }
        errors = checks.lint_manifest_consistency(
            plugin_data, marketplace_data, {"skill-writing"}
        )
        self.assertEqual(errors, [])

    def test_skill_dir_not_listed_in_marketplace_is_reported(self):
        plugin_data = {"name": "frank", "version": "0.1.0", "description": "x"}
        marketplace_data = {
            "plugins": [
                {
                    "name": "frank",
                    "version": "0.1.0",
                    "skills": ["./skills/skill-writing"],
                }
            ]
        }
        errors = checks.lint_manifest_consistency(
            plugin_data, marketplace_data, {"skill-writing", "orphan-skill"}
        )
        self.assertTrue(any("orphan-skill" in e for e in errors))

    def test_marketplace_entry_without_matching_dir_is_reported(self):
        plugin_data = {"name": "frank", "version": "0.1.0", "description": "x"}
        marketplace_data = {
            "plugins": [
                {
                    "name": "frank",
                    "version": "0.1.0",
                    "skills": ["./skills/skill-writing", "./skills/ghost-skill"],
                }
            ]
        }
        errors = checks.lint_manifest_consistency(
            plugin_data, marketplace_data, {"skill-writing"}
        )
        self.assertTrue(any("ghost-skill" in e for e in errors))

    def test_mismatched_versions_is_reported(self):
        plugin_data = {"name": "frank", "version": "0.2.0", "description": "x"}
        marketplace_data = {
            "plugins": [
                {
                    "name": "frank",
                    "version": "0.1.0",
                    "skills": ["./skills/skill-writing"],
                }
            ]
        }
        errors = checks.lint_manifest_consistency(
            plugin_data, marketplace_data, {"skill-writing"}
        )
        self.assertTrue(any("0.2.0" in e and "0.1.0" in e for e in errors))


class LintEvalRequiredKeysTests(unittest.TestCase):
    def test_all_keys_present(self):
        text = "cases:\n  - prompt: hi\n    expect_skill: skill-writing\n"
        self.assertEqual(checks.lint_eval_required_keys(text, ["cases"]), [])

    def test_missing_key_is_reported(self):
        text = "cases:\n  - prompt: hi\n"
        errors = checks.lint_eval_required_keys(text, ["cases", "prompt"])
        self.assertTrue(any("prompt" in e for e in errors))

    def test_indented_key_does_not_count_as_top_level(self):
        text = "cases:\n  prompt: nested, not top-level\n"
        errors = checks.lint_eval_required_keys(text, ["prompt"])
        self.assertTrue(any("prompt" in e for e in errors))

    def test_malformed_yaml_is_rejected(self):
        text = 'cases:\n  - prompt: "unterminated string\n    expect_skill: skill-writing\n'
        errors = checks.lint_eval_required_keys(text, ["cases"])
        self.assertTrue(errors)

    def test_non_mapping_top_level_is_rejected(self):
        text = "- just\n- a\n- list\n"
        errors = checks.lint_eval_required_keys(text, ["cases"])
        self.assertTrue(errors)


import json
import tempfile


class FileBasedChecksTests(unittest.TestCase):
    def test_check_skill_file_reports_errors_for_real_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "my-skill"
            skill_dir.mkdir(parents=True)
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text("---\nname: wrong-name\ndescription: x\n---\nBody\n")
            errors = checks.check_skill_file(skill_md)
            self.assertTrue(any("does not match directory name" in e for e in errors))

    def test_check_skill_file_reports_unclosed_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skills" / "my-skill"
            skill_dir.mkdir(parents=True)
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\nname: my-skill\ndescription: x\nBody with no closing delimiter.\n"
            )
            errors = checks.check_skill_file(skill_md)
            self.assertTrue(any("no YAML frontmatter found" in e for e in errors))

    def test_check_plugin_json_file_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plugin.json"
            path.write_text("{not valid json")
            errors = checks.check_plugin_json_file(path)
            self.assertTrue(any("invalid JSON" in e for e in errors))

    def test_check_plugin_json_file_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plugin.json"
            errors = checks.check_plugin_json_file(path)
            self.assertEqual(errors, [f"{path}: file does not exist"])

    def test_check_marketplace_json_file_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "marketplace.json"
            errors = checks.check_marketplace_json_file(path)
            self.assertEqual(errors, [f"{path}: file does not exist"])

    def test_check_marketplace_json_file_accepts_valid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "marketplace.json"
            path.write_text(
                json.dumps(
                    {
                        "name": "franks-ai-skills",
                        "owner": {"name": "Frank"},
                        "plugins": [{"name": "frank", "source": "./"}],
                    }
                )
            )
            self.assertEqual(checks.check_marketplace_json_file(path), [])

    def test_check_eval_file_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.yaml"
            errors = checks.check_eval_file(path, ["cases"])
            self.assertTrue(any("does not exist" in e for e in errors))

    def test_check_eval_file_reports_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.yaml"
            path.write_text("   \n")
            errors = checks.check_eval_file(path, ["cases"])
            self.assertTrue(any("file is empty" in e for e in errors))

    def test_find_skill_dirs_returns_empty_list_for_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(checks.find_skill_dirs(Path(tmp) / "skills"), [])

    def test_find_skill_dirs_lists_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            (skills_root / "b-skill").mkdir(parents=True)
            (skills_root / "a-skill").mkdir(parents=True)
            (skills_root / "not-a-dir.txt").write_text("x")
            dirs = checks.find_skill_dirs(skills_root)
            self.assertEqual([d.name for d in dirs], ["a-skill", "b-skill"])


class MainIntegrationTests(unittest.TestCase):
    def _write_valid_repo(self, root: Path) -> None:
        (root / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "frank",
                    "version": "0.1.0",
                    "description": "Frank's personal AI skill collection",
                }
            )
        )
        claude_plugin_dir = root / ".claude-plugin"
        claude_plugin_dir.mkdir()
        (claude_plugin_dir / "marketplace.json").write_text(
            json.dumps(
                {
                    "name": "franks-ai-skills",
                    "owner": {"name": "Frank Reichenbach"},
                    "plugins": [
                        {
                            "name": "frank",
                            "source": "./",
                            "strict": False,
                            "skills": ["./skills/demo-skill"],
                        }
                    ],
                }
            )
        )
        skill_dir = root / "skills" / "demo-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Demonstrates a valid skill.\n---\nBody.\n"
        )
        evals_dir = root / "evals" / "demo-skill"
        evals_dir.mkdir(parents=True)
        (evals_dir / "routing.yaml").write_text("cases:\n  - prompt: hi\n    expect_skill: demo-skill\n")
        (evals_dir / "behavior.yaml").write_text("prompt: hi\nexpect:\n  - does the thing\n")
        catalog_dir = root / "evals" / "catalog"
        catalog_dir.mkdir(parents=True)
        (catalog_dir / "collisions.yaml").write_text("cases: []\n")

    def test_main_returns_zero_for_valid_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_repo(root)
            self.assertEqual(checks.main(root), 0)

    def test_main_returns_nonzero_when_skill_name_mismatched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_repo(root)
            skill_md = root / "skills" / "demo-skill" / "SKILL.md"
            skill_md.write_text(
                "---\nname: wrong-name\ndescription: Demonstrates a valid skill.\n---\nBody.\n"
            )
            self.assertEqual(checks.main(root), 1)

    def test_main_returns_nonzero_for_orphaned_skill_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_repo(root)
            orphan_dir = root / "skills" / "orphan-skill"
            orphan_dir.mkdir(parents=True)
            (orphan_dir / "SKILL.md").write_text(
                "---\nname: orphan-skill\ndescription: Not listed in marketplace.json.\n---\nBody.\n"
            )
            evals_dir = root / "evals" / "orphan-skill"
            evals_dir.mkdir(parents=True)
            (evals_dir / "routing.yaml").write_text(
                "cases:\n  - prompt: hi\n    expect_skill: orphan-skill\n"
            )
            (evals_dir / "behavior.yaml").write_text("prompt: hi\nexpect:\n  - does the thing\n")
            self.assertEqual(checks.main(root), 1)


if __name__ == "__main__":
    unittest.main()
