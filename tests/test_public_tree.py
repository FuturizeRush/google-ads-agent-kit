import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_tree", ROOT / "scripts/check_public_tree.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class PublicPolicyTests(unittest.TestCase):
    def test_synthetic_google_tokens_are_detected(self):
        cases = [("GOCSPX-" + "X" * 24, "oauth_client_secret"),
                 ("ya29." + "Y" * 24, "oauth_access_token"),
                 ("1//" + "Z" * 24, "oauth_refresh_token")]
        for value, rule in cases:
            self.assertIn(rule, audit.inspect_text(value))

    def test_known_private_values_are_compared_without_echo(self):
        value = "synthetic-" + "private-value"
        findings = audit.inspect_text("content " + value, {value})
        self.assertIn("known_private_value", findings)
        self.assertNotIn(value, json.dumps(findings))

    def test_local_identity_paths_and_account_ids_are_detected(self):
        self.assertIn("personal_mac_path", audit.inspect_text("/Users/" + "exampleperson/folder"))
        self.assertIn("private_email", audit.inspect_text("person" + "@mail.invalid"))
        self.assertIn("ads_sized_identifier", audit.inspect_text("1" * 10))
        self.assertIn("ads_id_with_hyphens", audit.inspect_text("1" * 3 + "-" + "2" * 3 + "-" + "3" * 4))

    def test_public_noreply_author_and_generic_paths_are_allowed(self):
        self.assertEqual(audit.inspect_text("author@users.noreply.github.com $HOME/Downloads/client_secrets.json /ABSOLUTE/PATH"), [])

    def test_json_credential_extraction_is_field_specific(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            path.write_text(json.dumps({"installed": {"client_secret": "synthetic-secret", "auth_uri": "https://accounts.google.com"}}))
            values = audit.private_values([path])
            self.assertIn("synthetic-secret", values)
            self.assertNotIn("https://accounts.google.com", values)

    def test_git_timestamps_are_not_mistaken_for_account_ids(self):
        commit = "author maintainer <author@users.noreply.github.com> " + "1" * 10 + " +0000\n\nSafe message\n"
        self.assertEqual(audit.inspect_commit(commit.encode(), ()), [])

    def test_git_author_and_message_still_receive_private_checks(self):
        commit = "author person <person" + "@mail.invalid> " + "1" * 10 + " +0000\n\nAccount " + "2" * 10
        findings = audit.inspect_commit(commit.encode(), ())
        self.assertIn("private_email", findings)
        self.assertIn("ads_sized_identifier", findings)

    def test_long_campaign_ids_are_detected(self):
        for length in (11, 12, 16, 20):
            self.assertIn("ads_sized_identifier", audit.inspect_text("2" * length))

    def test_private_context_list_catches_noncredential_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            private_name = "Synthetic private audience"
            path.write_text(json.dumps({"sensitive_values": [private_name], "video_id": "synthetic-video"}))
            values = audit.private_values([path])
            self.assertEqual(values, {private_name, "synthetic-video"})
            self.assertEqual(audit.inspect_text(private_name, values), ["known_private_value"])

    def test_invalid_private_list_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            for invalid in ("not-a-list", [None], ["short"]):
                path.write_text(json.dumps({"sensitive_values": invalid}))
                with self.assertRaises(ValueError):
                    audit.private_values([path])

    def test_private_value_in_filename_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            filename = "audience-private-label.txt"
            (root / ".public-files").write_text(".public-files\n" + filename + "\n")
            (root / filename).write_text("Safe body")
            # Keep the comparison input outside the public tree.
            with tempfile.TemporaryDirectory() as inputs:
                private = Path(inputs) / "context.json"
                private.write_text(json.dumps({"sensitive_values": ["audience-private-label"]}))
                report = audit.check(root, private_files=[private])
            self.assertTrue(any(f["rule"] == "filename_known_private_value" for f in report["findings"]))

    def test_binary_files_are_not_silently_skipped(self):
        self.assertEqual(audit.inspect_bytes(bytes([255, 254]), []), ["non_text_file_requires_review"])

    def test_unlisted_file_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".public-files").write_text(".public-files\nREADME.md\n")
            (root / "README.md").write_text("Safe text")
            (root / "unreviewed.txt").write_text("new text")
            self.assertEqual(audit.check(root)["status"], "FAIL")

    def test_symlink_is_not_followed_into_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".public-files").write_text(".public-files\n")
            (root / "link").symlink_to(root / "missing-secret")
            report = audit.check(root)
            self.assertTrue(any(f["rule"] == "symlink_not_allowed" for f in report["findings"]))


class GitGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        audit.git(self.root, "init", "--quiet")
        audit.git(self.root, "config", "user.name", "Synthetic Maintainer")
        audit.git(self.root, "config", "user.email", "maintainer@example.com")
        (self.root / ".public-files").write_text(".public-files\nREADME.md\n")
        (self.root / "README.md").write_text("Safe content")
        audit.git(self.root, "add", ".public-files", "README.md")
        self.commit("Synthetic fixture")

    def commit(self, message):
        audit.git(self.root, "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                  "commit", "--quiet", "-m", message)

    def test_clean_index_and_history_pass(self):
        report = audit.check(self.root, history=True)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["staged_blobs_checked"], 2)

    def test_secret_staged_but_removed_from_worktree_is_detected(self):
        path = self.root / "README.md"
        path.write_text("ya29." + "S" * 24)
        audit.git(self.root, "add", "README.md")
        path.write_text("Safe content again")
        report = audit.check(self.root, history=True)
        self.assertTrue(any(f["rule"] == "staged_oauth_access_token" for f in report["findings"]))

    def test_clean_worktree_cannot_hide_historical_secret(self):
        path = self.root / "README.md"
        path.write_text("GOCSPX-" + "S" * 24)
        audit.git(self.root, "add", "README.md")
        self.commit("Synthetic secret fixture")
        path.write_text("Safe content again")
        audit.git(self.root, "add", "README.md")
        self.commit("Clean fixture")
        report = audit.check(self.root, history=True)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(f["rule"] == "oauth_client_secret" for f in report["findings"]))

    def test_clean_worktree_cannot_hide_staged_symlink(self):
        path = self.root / "README.md"
        path.unlink()
        path.symlink_to("missing-private-file")
        audit.git(self.root, "add", "README.md")
        path.unlink()
        path.write_text("Safe content again")
        report = audit.check(self.root, history=True)
        self.assertTrue(any(f["rule"] == "unsafe_index_entry" for f in report["findings"]))


if __name__ == "__main__":
    unittest.main()
