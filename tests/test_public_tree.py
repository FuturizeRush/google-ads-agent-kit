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
        self.assertIn("ten_digit_identifier", audit.inspect_text("1" * 10))
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
        self.assertIn("ten_digit_identifier", findings)

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


if __name__ == "__main__":
    unittest.main()
