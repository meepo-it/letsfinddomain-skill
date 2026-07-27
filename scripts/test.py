#!/usr/bin/env python3
"""Run the repository's fast, offline checks before a commit."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_DIR = ROOT / "docs" / "providers"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def local_markdown_links(path: Path):
    for target in re.findall(r"\]\(([^)]+)\)", read(path)):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = target.split("#", 1)[0]
        if target:
            yield (path.parent / target).resolve()


class RepositoryTests(unittest.TestCase):
    def test_python_scripts_compile(self):
        for path in sorted((ROOT / "scripts").glob("*.py")):
            if path.name == "test.py":
                continue
            compile(read(path), str(path), "exec")

    def test_cli_help(self):
        for name in ("check-domains.py", "gen-names.py"):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / name), "--help"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_provider_document_pairs(self):
        english = sorted(PROVIDER_DIR.glob("*/setup.md"))
        self.assertGreater(len(english), 0)
        for en in english:
            zh = en.with_name("setup.zh-CN.md")
            self.assertTrue(zh.exists(), f"missing Chinese pair for {en}")
            en_text, zh_text = read(en), read(zh)

            en_steps = re.findall(r"^## ([123])\. ", en_text, re.MULTILINE)
            zh_steps = re.findall(r"^## ([123])\. ", zh_text, re.MULTILINE)
            self.assertEqual(en_steps, ["1", "2", "3"], en)
            self.assertEqual(zh_steps, en_steps, zh)

            env_pattern = r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b"
            self.assertEqual(
                sorted(set(re.findall(env_pattern, en_text))),
                sorted(set(re.findall(env_pattern, zh_text))),
                f"environment variables differ: {en}",
            )

            self.assertEqual(
                sorted(set(re.findall(r"https?://[^)\s]+", en_text))),
                sorted(set(re.findall(r"https?://[^)\s]+", zh_text))),
                f"official URLs differ: {en}",
            )
            self.assertEqual(
                sorted(set(re.findall(r"!\[[^]]*\]\(([^)]+)\)", en_text))),
                sorted(set(re.findall(r"!\[[^]]*\]\(([^)]+)\)", zh_text))),
                f"screenshots differ: {en}",
            )

            self.assertIn("/letsfinddomain-skill", en_text)
            self.assertIn("/letsfinddomain-skill", zh_text)
            self.assertNotIn("python3 scripts/check-domains.py", en_text)
            self.assertNotIn("python3 scripts/check-domains.py", zh_text)

        for zh in sorted(PROVIDER_DIR.glob("*/setup.zh-CN.md")):
            self.assertTrue(zh.with_name("setup.md").exists(), f"missing English pair for {zh}")

    def test_readme_provider_coverage(self):
        en, zh = read(ROOT / "README.md"), read(ROOT / "README.zh-CN.md")
        providers = [p.name for p in sorted(PROVIDER_DIR.iterdir()) if p.is_dir()]
        for provider in providers:
            display = {
                "cloudflare": "Cloudflare Registrar",
                "dynadot": "Dynadot",
                "godaddy": "GoDaddy",
                "namecheap": "Namecheap",
                "namecom": "Name.com",
                "namesilo": "NameSilo",
                "porkbun": "Porkbun",
                "spaceship": "Spaceship",
            }[provider]
            self.assertIn(display, en)
            self.assertIn(display, zh)
        self.assertIn("Spaceship (default)", en)
        self.assertIn("Spaceship（默认）", zh)
        self.assertEqual(
            len(re.findall(r"^## ", en, re.MULTILINE)),
            len(re.findall(r"^## ", zh, re.MULTILINE)),
            "README section structure differs",
        )

    def test_local_markdown_links(self):
        missing = []
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts or ".cache" in path.parts:
                continue
            for target in local_markdown_links(path):
                if not target.exists():
                    missing.append(f"{path}: {target}")
        self.assertEqual(missing, [], "missing local Markdown links")

    def test_pre_commit_hook(self):
        hook = ROOT / ".githooks" / "pre-commit"
        self.assertTrue(hook.exists())
        self.assertTrue(os.access(hook, os.X_OK), "pre-commit hook must be executable")


if __name__ == "__main__":
    unittest.main(verbosity=2)
