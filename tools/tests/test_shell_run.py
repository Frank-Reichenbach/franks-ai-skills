#!/usr/bin/env python3
"""Executable tests for the shell skill's scripts/run.sh wrapper.

These test real process behavior (subprocess invocation, exit status,
stdout/stderr, file I/O) — not something tools/checks.py's structural
validation covers, and not something that needs a live model. See
skills/shell/SKILL.md for what this wrapper does and does not guarantee.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_SH = REPO_ROOT / "skills" / "shell" / "scripts" / "run.sh"


def run_wrapper(args, cwd=None, env=None):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", str(RUN_SH), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=full_env,
    )


class QuotingAndExitStatusTests(unittest.TestCase):
    def test_quoting_is_preserved(self):
        result = run_wrapper(['echo "hello world"'])
        lines = [
            line for line in result.stdout.splitlines()
            if line.strip() and not line.startswith("$")
        ]
        self.assertTrue(
            any(line.strip() == "hello world" for line in lines),
            f"expected a line exactly 'hello world', got: {lines!r}",
        )

    def test_successful_exit_status_is_preserved(self):
        result = run_wrapper(["true"])
        self.assertEqual(result.returncode, 0)

    def test_failing_exit_status_is_preserved(self):
        result = run_wrapper(["exit 7"])
        self.assertEqual(result.returncode, 7)

    def test_failure_stderr_is_surfaced(self):
        # Checking result.stderr specifically is what makes this test
        # valid — the diagnostic string is also present in the command
        # text itself, and the echoed "$ ..." command line goes to
        # result.stdout, so a stdout check here would pass even if the
        # wrapped command's real stderr were never captured at all.
        result = run_wrapper(
            ['echo some-stdout; echo REAL_STDERR_DIAGNOSTIC_XYZ >&2; exit 1']
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("REAL_STDERR_DIAGNOSTIC_XYZ", result.stderr)


class LargeOutputTests(unittest.TestCase):
    def test_stdout_past_limit_is_truncated_with_marker(self):
        result = run_wrapper(
            ["head -c 5000 /dev/zero | tr '\\0' 'a'"],
            env={"RUN_SH_MAX_OUTPUT_BYTES": "100"},
        )
        self.assertIn("truncated", result.stdout.lower())
        self.assertLess(result.stdout.count("a"), 5000)

    def test_output_under_limit_is_not_truncated(self):
        result = run_wrapper(
            ["printf 'ok'"],
            env={"RUN_SH_MAX_OUTPUT_BYTES": "100"},
        )
        self.assertNotIn("truncated", result.stdout.lower())
        self.assertIn("ok", result.stdout)

    def test_stdout_truncation_backs_off_a_split_multibyte_character(self):
        # Regression: head -c cuts at a raw byte offset, which can land
        # inside a multibyte UTF-8 character even when the full output
        # was valid — 49 ASCII bytes + 'é' (2 bytes) is 51 bytes; a
        # 50-byte limit used to cut 'é' in half, producing invalid UTF-8
        # from valid input and crashing any text-mode consumer.
        result = run_wrapper(
            ['python3 -c "import sys; sys.stdout.write(chr(65)*49 + chr(233))"'],
            env={"RUN_SH_MAX_OUTPUT_BYTES": "50"},
        )
        # subprocess with text=True already decoded this — reaching here
        # at all (rather than raising UnicodeDecodeError) is part of what
        # this test verifies. It should also back off to 49, not 50.
        self.assertIn("showing first 49", result.stdout)
        self.assertNotIn("\xe9", result.stdout)  # the dangling 'é' itself

    def test_stderr_truncation_backs_off_a_split_multibyte_character(self):
        # Same regression, the tail -c direction: 'é' (2 bytes) + 49
        # ASCII bytes is 51 bytes; a 50-byte limit used to cut off 'é''s
        # leading byte, leaving a dangling continuation byte.
        result = run_wrapper(
            [
                'python3 -c "import sys; '
                'sys.stderr.write(chr(233) + chr(65)*49); sys.exit(1)"'
            ],
            env={"RUN_SH_MAX_OUTPUT_BYTES": "50"},
        )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("\xe9", result.stderr)

    def test_stderr_diagnostic_survives_large_stdout_truncation(self):
        # Regression: a prior version combined stdout+stderr and kept
        # only the first N bytes, so a large stdout could push a later
        # failure's stderr diagnostic out of the visible window entirely.
        result = run_wrapper(
            [
                'printf "%0.sA" $(seq 1 100); echo; '
                'echo ACTUAL_FAILURE_DETAIL >&2; exit 7'
            ],
            env={"RUN_SH_MAX_OUTPUT_BYTES": "50"},
        )
        self.assertEqual(result.returncode, 7)
        self.assertIn("ACTUAL_FAILURE_DETAIL", result.stderr)

    def test_invalid_byte_limit_is_rejected_before_execution(self):
        # Regression: an invalid RUN_SH_MAX_OUTPUT_BYTES used to crash
        # the size comparison *after* the command had already run,
        # losing the real exit status and silently producing side
        # effects from a command that was never meant to execute.
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "side_effect.txt"
            result = run_wrapper(
                [f'echo wrote > {marker} ; exit 7'],
                env={"RUN_SH_MAX_OUTPUT_BYTES": "not-a-number"},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotEqual(result.returncode, 7)
            self.assertFalse(marker.exists(), "command should not have run")

    def test_leading_zero_byte_limit_is_rejected(self):
        # Regression: bash's arithmetic context treats a leading "0" as
        # octal ("08"/"09" aren't even valid octal digits, so this used
        # to blow up mid-comparison after the command had already run).
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "side_effect.txt"
            result = run_wrapper(
                [f'echo wrote > {marker} ; exit 7'],
                env={"RUN_SH_MAX_OUTPUT_BYTES": "08"},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotEqual(result.returncode, 7)
            self.assertFalse(marker.exists(), "command should not have run")

    def test_octal_looking_byte_limit_is_rejected_not_reinterpreted(self):
        # Regression: "010" was silently treated as octal (== 8 decimal)
        # instead of the intended 10, shrinking the budget unexpectedly.
        result = run_wrapper(["echo hi"], env={"RUN_SH_MAX_OUTPUT_BYTES": "010"})
        self.assertNotEqual(result.returncode, 0)

    def test_overflowing_byte_limit_is_rejected(self):
        # Regression: a value beyond signed 64-bit range wrapped around
        # during arithmetic and was treated as an effectively negative
        # limit, causing stdout to be omitted entirely even though the
        # real output was tiny.
        result = run_wrapper(
            ["echo hello-world-test"],
            env={"RUN_SH_MAX_OUTPUT_BYTES": "9223372036854775808"},
        )
        self.assertNotEqual(result.returncode, 0)


class SecretPathCheckTests(unittest.TestCase):
    def test_known_secret_path_is_blocked_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("SECRET=do-not-print-me\n")
            result = run_wrapper(["cat .env"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("do-not-print-me", result.stdout)

    def test_known_secret_path_succeeds_with_explicit_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("SECRET=do-not-print-me\n")
            result = run_wrapper(["--allow-secret-path", "cat .env"], cwd=tmp)
            self.assertEqual(result.returncode, 0)
            self.assertIn("do-not-print-me", result.stdout)

    def test_unrelated_command_is_not_blocked(self):
        result = run_wrapper(["echo hello"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)

    def test_double_quoted_path_is_still_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("do-not-print-me\n")
            result = run_wrapper(['cat ".env"'], cwd=tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("do-not-print-me", result.stdout)

    def test_single_quoted_path_is_still_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("do-not-print-me\n")
            result = run_wrapper(["cat '.env'"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("do-not-print-me", result.stdout)

    def test_semicolon_separated_path_is_still_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("do-not-print-me\n")
            result = run_wrapper(["cat .env; true"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("do-not-print-me", result.stdout)

    def test_redirect_into_path_is_still_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("do-not-print-me\n")
            result = run_wrapper(["cat <.env"], cwd=tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("do-not-print-me", result.stdout)

    def test_blocked_diagnostic_does_not_repeat_glued_secrets(self):
        # Regression: the diagnostic used to print the raw regex match, and
        # the .pem alternative extends back to the previous whitespace, so a
        # secret glued to the path was printed in full. PASSWORD= is a format
        # redact() doesn't know, so redacting the match would not be enough.
        for cmd in (
            "TOKEN=FAKE_TEST_SECRET_1234;cat<client.pem",
            "PASSWORD=FAKE_PW_5678;cat<client.pem",
        ):
            with self.subTest(cmd=cmd):
                result = run_wrapper([cmd])
                self.assertEqual(result.returncode, 3)
                secret = cmd.split("=", 1)[1].split(";", 1)[0]
                self.assertNotIn(secret, result.stdout + result.stderr)
                self.assertIn(".pem file", result.stderr)

    def test_blocked_diagnostic_names_only_the_category(self):
        cases = [
            ("cat .env.local", ".env file"),
            ("cat server.pem", ".pem file"),
            ("cat ~/.ssh/id_ed25519", "SSH key file"),
            ("cat ~/.ssh/id_rsa.pub", "SSH key file"),
            ("ls ~/.ssh/", ".ssh directory"),
            ("cat ~/.aws/credentials", "AWS credentials file"),
            ("cat credentials.json", "credentials file"),
            ("cat ~/.netrc", ".netrc file"),
        ]
        for cmd, label in cases:
            with self.subTest(cmd=cmd):
                result = run_wrapper([cmd])
                self.assertEqual(result.returncode, 3)
                self.assertIn(f"(matched: {label})", result.stderr)
                # The command text itself never appears in the diagnostic.
                self.assertNotIn(cmd, result.stderr)

    def test_invalid_utf8_does_not_bypass_the_check(self):
        # Regression: in a UTF-8 locale an invalid byte made the regex
        # match fail, so `cat .env #\xff` ran and printed the file.
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("PASSWORD=FAKE_PW_5678\n")
            result = subprocess.run(
                ["bash", str(RUN_SH), b"cat .env #\xff"],
                capture_output=True,
                cwd=tmp,
                env={**os.environ, "LC_ALL": "en_US.UTF-8"},
            )
            self.assertEqual(result.returncode, 3)
            self.assertNotIn(b"FAKE_PW_5678", result.stdout + result.stderr)
            self.assertIn(b"(matched: .env file)", result.stderr)


class RedactionFailureTests(unittest.TestCase):
    def test_unredactable_stdout_is_withheld_not_shown_raw_or_partial(self):
        # Regression: a captured stream sed can't fully process (e.g. a
        # byte sequence invalid under the current locale) used to be
        # silently dropped with no indication anything went wrong, and
        # the wrapper reported success regardless.
        result = run_wrapper(
            [
                'printf "VALID_PREFIX_XYZ\\xc3\\x28_INVALID_TAIL\\n"; '
                'printf "FINAL_DIAGNOSTIC_XYZ\\n" >&2'
            ]
        )
        # The command text itself legitimately appears once, in the
        # echoed "$ ..." line — the regression is the *actual output*
        # leaking as a second, separate occurrence.
        self.assertEqual(result.stdout.count("VALID_PREFIX_XYZ"), 1)
        self.assertIn("withheld", result.stdout.lower())
        # A stream that failed independently (stderr here) still comes
        # through normally.
        self.assertIn("FINAL_DIAGNOSTIC_XYZ", result.stderr)
        # sed's own raw error text must not leak through unattributed.
        self.assertNotIn("illegal byte sequence", result.stderr.lower())


class RedactionTests(unittest.TestCase):
    def test_bearer_token_is_redacted_by_bearer_rule_specifically(self):
        # Uses a token that does NOT start with "sk-", so this actually
        # exercises the Bearer-specific rule rather than incidentally
        # passing via the independent sk- rule.
        result = run_wrapper(
            ['echo "Authorization: Bearer ghp_FAKEFAKEFAKEFAKE1234"']
        )
        self.assertNotIn("ghp_FAKEFAKEFAKEFAKE1234", result.stdout)
        self.assertIn("REDACTED", result.stdout)

    def test_sk_style_key_is_redacted(self):
        result = run_wrapper(["echo sk-FAKEFAKEFAKEFAKE1234"])
        self.assertNotIn("sk-FAKEFAKEFAKEFAKE1234", result.stdout)
        self.assertIn("REDACTED", result.stdout)

    def test_api_key_style_value_is_redacted(self):
        result = run_wrapper(["echo API_KEY=abcd1234efgh5678"])
        self.assertNotIn("abcd1234efgh5678", result.stdout)
        self.assertIn("REDACTED", result.stdout)

    def test_plain_key_form_is_redacted(self):
        result = run_wrapper(["echo key=abcd1234efgh5678"])
        self.assertNotIn("abcd1234efgh5678", result.stdout)
        self.assertIn("REDACTED", result.stdout)

    def cat_through_wrapper(self, text):
        # Prints text through the wrapper on stdout and on stderr, from a
        # file, so bash doesn't interpret the quotes in it.
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "input.txt"
            f.write_text(text)
            return (
                run_wrapper([f"cat {f}"]).stdout,
                run_wrapper([f"cat {f} >&2"]).stderr,
            )

    def test_quoted_values_are_redacted_completely(self):
        # (input, fragments of the secret that must not appear)
        cases = (
            ('API_KEY="abcd1234 efgh5678"\n', ("abcd1234", "efgh5678")),
            ('SECRET_KEY="correct horse battery staple"\n', ("correct", "horse", "staple")),
            ('KEY="abcd\\"efgh ijkl"\n', ("abcd", "efgh", "ijkl")),
            ("TOKEN=$'abcd1234efgh 5678'\n", ("abcd1234efgh", "5678")),
            ("KEY='abcd'\\''efgh ijkl'\n", ("abcd", "efgh", "ijkl")),
            # Text inside a value that looks like a setting doesn't end it.
            ('SECRET_KEY="pass trailer.foo.key=lettersonlysecret"\n', ("pass", "lettersonlysecret")),
            # A value spanning lines, and one the input ends inside.
            ('KEY="abcd1234\nefgh5678\nijkl"\n', ("abcd1234", "efgh5678", "ijkl")),
            ("TOKEN='abcd1234\nefgh5678\n", ("abcd1234", "efgh5678")),
            ('KEY="abcd1234\nefgh5678"\'ijkl\nmnop\'\n', ("efgh5678", "ijkl", "mnop")),
            # A name inside an open value doesn't end it either.
            ('KEY="abcd token=efgh5678\nijkl"\n', ("abcd", "efgh5678", "ijkl")),
            # A quote opened after an unquoted part continues the value,
            # and so does a backslash at the end of the line.
            ('KEY=abcd1234"efgh\nijkl"\n', ("efgh", "ijkl")),
            ("KEY=abcd1234\\\nefgh5678\n", ("abcd1234", "efgh5678")),
            ("TOKEN=\\\nefgh5678\n", ("efgh5678",)),
            ('KEY="abcd1234\nefgh5678"\\\nijkl\n', ("efgh5678", "ijkl")),
            # $'…' allows \' inside; '…' doesn't, so a $' is never read
            # as a $ followed by a single-quoted fragment.
            ("TOKEN=$'abcdefgh\nijkl\\' LEAKTAIL\nlast'\n", ("abcdefgh", "ijkl", "LEAKTAIL", "last")),
            # Moving from one quote style to the next across lines.
            ("KEY=\"abcd1234\nefgh\"'ijkl\nmnop'$'qrst\\'\nuvwx'\n", ("efgh", "ijkl", "mnop", "qrst", "uvwx")),
            ('KEY=$"abcd efgh"\n', ("abcd", "efgh")),
        )
        for text, fragments in cases:
            with self.subTest(text=text):
                for stream in self.cat_through_wrapper(text):
                    for fragment in fragments:
                        self.assertNotIn(fragment, stream)
                    self.assertIn("REDACTED", stream)

    def test_text_around_quoted_values_stays_readable(self):
        cases = (
            # Short values stay readable, as before (8-character minimum,
            # counted over the value as written, quotes included).
            ("key=abc\n", "key=abc"),
            ('KEY="ab"\n', 'KEY="ab"'),
            # Text after a value's closing quote is not part of it.
            ('KEY="abcd1234\nefgh5678" && echo visible\n', "&& echo visible"),
            ('KEY="abcd1234 efgh5678"\nnext line\n', "next line"),
            # A name inside a closed value doesn't open a quote.
            ('KEY="pass key=abcd1234efgh"\nnext line\n', "next line"),
            ("KEY=abcd1234\\\nefgh5678 visible\n", " visible"),
            # A $'…' value closed after an escaped quote leaves the next
            # line alone, and so do the other quote transitions.
            ("TOKEN=$'abcd\\'efgh'\nvisible line\n", "visible line"),
            ("KEY=\"abcd1234\nefgh\"'ijkl\nmnop'$'qrst\\'\nuvwx'\nafter\n", "after"),
            ('KEY=$"abcd efgh"\nvisible line\n', "visible line"),
            # A $ at the end of a value belongs to it.
            ("KEY=abcd1234$ next\n", "KEY=[REDACTED] next"),
            # A quote outside a secret assignment starts nothing.
            ('say "open\nplain text\n', "plain text"),
        )
        for text, visible in cases:
            with self.subTest(text=text):
                for stream in self.cat_through_wrapper(text):
                    self.assertIn(visible, stream)

    def test_quoted_value_in_command_echo_is_redacted(self):
        for cmd in (
            'export API_KEY="abcd1234 efgh5678"; echo done',
            'export KEY="abcd1234\nefgh5678"; echo done',
        ):
            with self.subTest(cmd=cmd):
                result = run_wrapper([cmd])
                self.assertNotIn("abcd1234", result.stdout)
                self.assertNotIn("efgh5678", result.stdout)
                self.assertIn("done", result.stdout)

    def test_many_values_on_one_line_take_linear_time(self):
        # Regression: masking one value at a time rescanned the line from
        # its start each time, so 1,600 values on one line took 4.5 s
        # and doubling them took four times as long.
        import time

        start = time.monotonic()
        stdout, _ = self.cat_through_wrapper("key=abcdefgh " * 3200 + "\n")
        self.assertLess(time.monotonic() - start, 5)
        self.assertNotIn("abcdefgh", stdout)

    def test_line_continuations_are_joined_as_bash_joins_them(self):
        # Bash removes a backslash-newline before it reads names, quotes
        # and $'…', so each of these is one assignment.
        cases = (
            ("TOKEN=$\\\n'abcdefgh\\' LEAKTAIL\nlast'\n", ("abcdefgh", "LEAKTAIL", "last")),
            ('KEY=$\\\n"abcd efgh"\n', ("abcd", "efgh")),
            ("export API_KE\\\nY=lettersonlysecret1\n", ("lettersonlysecret1",)),
            ("AP\\\nI_K\\\nEY=lettersonlysecret1\n", ("lettersonlysecret1",)),
            ("KEY\\\n=lettersonlysecret1\n", ("lettersonlysecret1",)),
            ("KEY=\\\nlettersonlysecret1\n", ("lettersonlysecret1",)),
        )
        for text, fragments in cases:
            with self.subTest(text=text):
                for stream in self.cat_through_wrapper(text):
                    for fragment in fragments:
                        self.assertNotIn(fragment, stream)
                    self.assertIn("REDACTED", stream)

    def test_control_characters_are_kept(self):
        # A US (\x1f) comes out unchanged; a NUL comes out as US, because
        # BSD awk would cut the line at it.
        stdout, _ = self.cat_through_wrapper("a\x1fb key=abcd\x1f<efgh>1234\nc\x00d key=abcdefgh1\ne\n")
        self.assertIn("a\x1fb key=[REDACTED]\n", stdout)
        self.assertIn("c\x1fd key=[REDACTED]\ne\n", stdout)
        self.assertNotIn("efgh", stdout)

    def test_missing_final_newline_is_kept(self):
        for text, end in (("key=abc", "key=abc"), ("KEY=abcdefgh1", "KEY=[REDACTED]")):
            with self.subTest(text=text):
                stdout, _ = self.cat_through_wrapper(text)
                self.assertTrue(stdout.endswith("\n" + end), repr(stdout[-30:]))

    def test_quoted_value_is_fully_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "quoted.txt"
            f.write_text('TOKEN="FAKE_QUOTED_VALUE_123456"\n')
            result = run_wrapper([f"cat {f}"])
            self.assertNotIn("FAKE_QUOTED_VALUE_123456", result.stdout)
            self.assertIn("REDACTED", result.stdout)

    def test_base64_shaped_value_is_fully_redacted(self):
        # Regression: a value containing '+' or '/' used to terminate
        # the match early, leaking everything after the first such char.
        result = run_wrapper(
            ['echo "Bearer FAKE_REMAINDER_TOKEN_TEST+FAKE_REMAINDER/=="']
        )
        self.assertNotIn("FAKE_REMAINDER", result.stdout)

    def test_redaction_applies_before_truncation(self):
        # Regression: truncating raw output before redaction could cut a
        # secret mid-token, dropping it below the redaction rule's
        # minimum length and leaking the (shortened) prefix.
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "secret.txt"
            f.write_text("API_KEY=FAKESECRET123456789\n")
            result = run_wrapper(
                [f"cat {f}"],
                env={"RUN_SH_MAX_OUTPUT_BYTES": "12"},
            )
            self.assertNotIn("FAKESECRET123456789", result.stdout)
            self.assertNotIn("FAKE", result.stdout)


if __name__ == "__main__":
    unittest.main()
