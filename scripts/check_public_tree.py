#!/usr/bin/env python3
"""Check an explicit public file list, content, and optionally reachable Git history."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", "__pycache__"}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
    "oauth_client_secret": re.compile(r"GOCSPX-[A-Za-z0-9_-]{12,}"),
    "oauth_access_token": re.compile(r"ya29\.[A-Za-z0-9_.-]{16,}"),
    "oauth_refresh_token": re.compile(r"1//[A-Za-z0-9_-]{20,}"),
    "google_api_key": re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
    "github_token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})"),
    "oauth_client_id": re.compile(r"\b\d+-[a-zA-Z0-9_-]+\.apps\.googleusercontent\.com\b"),
    "personal_mac_path": re.compile(r"/" + r"Users/[^/\s\"']+"),
    "personal_windows_path": re.compile(r"[A-Z]:\\Users\\[^\\\s\"']+"),
    "private_email": re.compile(r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com\b|example\.(?:com|org)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "ads_id_with_hyphens": re.compile(r"(?<!\d)\d{3}-\d{3}-\d{4}(?!\d)"),
    "ten_digit_identifier": re.compile(r"(?<![\w])\d{10}(?![\w])"),
}
PRIVATE_KEYS = {
    "client_id", "client_secret", "refresh_token", "access_token", "token", "private_key",
    "private_key_id", "developer_token", "login_customer_id", "customer_id", "client_email",
    "project_id", "quota_project_id", "account", "email",
}


def git(root, *args, binary=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
    return result.stdout if binary else result.stdout.decode("utf-8")


def private_values(paths):
    values = set()

    def collect(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in PRIVATE_KEYS and isinstance(value, str) and len(value) >= 6:
                    values.add(value)
                collect(value)
        elif isinstance(obj, list):
            for value in obj:
                collect(value)

    for path in paths:
        content = Path(path).read_text(encoding="utf-8")
        try:
            collect(json.loads(content))
        except ValueError:
            for line in content.splitlines():
                match = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", line)
                if match and any(word in match[1].lower() for word in ("token", "secret", "client_id", "customer_id", "project", "email")):
                    value = match[2].strip().strip("\"'")
                    if len(value) >= 6:
                        values.add(value)
    return values


def inspect_text(text, known=()):
    findings = [name for name, pattern in PATTERNS.items() if pattern.search(text)]
    if any(value in text for value in known):
        findings.append("known_private_value")
    return findings


def inspect_bytes(data, known):
    try:
        return inspect_text(data.decode("utf-8"), known)
    except UnicodeDecodeError:
        return ["non_text_file_requires_review"]


def inspect_commit(data, known):
    text = data.decode("utf-8")
    headers, separator, message = text.partition("\n\n")
    lines = []
    for line in headers.splitlines():
        if line.startswith(("author ", "committer ")):
            # Git timestamps are public metadata, not Ads account identifiers.
            line = re.sub(r" \d+ [+-]\d{4}$", "", line)
        lines.append(line)
    return inspect_text("\n".join(lines) + separator + message, known)


def check(root, history=False, private_files=()):
    allowed = {line.strip() for line in (root / ".public-files").read_text().splitlines()
               if line.strip() and not line.startswith("#")}
    known = private_values(private_files)
    findings = []
    files = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            findings.append({"path": relative, "rule": "symlink_not_allowed"})
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if not path.is_file():
            continue
        files.add(relative)
        if relative not in allowed:
            findings.append({"path": relative, "rule": "file_not_allowlisted"})
        for rule in inspect_bytes(path.read_bytes(), known):
            findings.append({"path": relative, "rule": rule})
    for missing in sorted(allowed - files):
        findings.append({"path": missing, "rule": "allowlisted_file_missing"})

    commits = 0
    blobs = 0
    if history:
        if Path(git(root, "rev-parse", "--show-toplevel").strip()).resolve() != root.resolve():
            raise ValueError("wrong repository root")
        index = set(git(root, "ls-files", "-z").strip("\0").split("\0"))
        if index != allowed:
            findings.append({"path": "GIT_INDEX", "rule": "index_differs_from_allowlist"})
        revisions = git(root, "rev-list", "--all").splitlines()
        if not revisions:
            raise ValueError("no history to check")
        seen = set()
        for revision in revisions:
            commits += 1
            for rule in inspect_commit(git(root, "cat-file", "commit", revision, binary=True), known):
                findings.append({"path": "COMMIT_METADATA", "rule": rule})
            listing = git(root, "ls-tree", "-r", "-z", revision).split("\0")
            for entry in filter(None, listing):
                header, path = entry.split("\t", 1)
                mode, kind, oid = header.split()
                if path not in allowed or mode not in {"100644", "100755"} or kind != "blob":
                    findings.append({"path": path, "rule": "historical_file_not_allowed"})
                if kind == "blob" and oid not in seen:
                    seen.add(oid)
                    blobs += 1
                    for rule in inspect_bytes(git(root, "cat-file", "blob", oid, binary=True), known):
                        findings.append({"path": path, "rule": rule})
    return {"status": "PASS" if not findings else "FAIL", "files_checked": len(files),
            "commits_checked": commits, "unique_blobs_checked": blobs,
            "private_source_files_checked": len(private_files), "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--private-file", action="append", default=[])
    args = parser.parse_args()
    try:
        report = check(ROOT, args.history, args.private_file)
    except Exception:
        # Never surface the input or credential file contents in exceptions.
        print(json.dumps({"status": "FAIL", "error": "audit_input_or_git_error"}))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
