#!/usr/bin/env python3
"""Generate candidate names by combining roots with affixes.

Emits bare names, one per line, so it pipes straight into the checker:

    python3 scripts/gen-names.py --roots snap,clip,vault --suffixes ify,ly,kit \
      --max-len 8 | python3 scripts/check-domains.py --tlds com --available-only

This is deliberately mechanical. It expands combinations and applies length and
character filters — it has no taste. Judgement about which of the survivors is
actually a good name stays with you.
"""

from __future__ import annotations

import argparse
import re
import sys

VOWELS = set("aeiou")


def split_list(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def combine(prefixes, roots, suffixes, patterns) -> list[str]:
    out, seen = [], set()

    def add(name):
        if name and name not in seen:
            seen.add(name)
            out.append(name)

    for pattern in patterns:
        if pattern == "root":
            for root in roots:
                add(root)
        elif pattern == "root+suffix":
            for root in roots:
                for suffix in suffixes:
                    add(root + suffix)
        elif pattern == "prefix+root":
            for prefix in prefixes:
                for root in roots:
                    add(prefix + root)
        elif pattern == "prefix+root+suffix":
            for prefix in prefixes:
                for root in roots:
                    for suffix in suffixes:
                        add(prefix + root + suffix)
        elif pattern == "root+root":
            for first in roots:
                for second in roots:
                    if first != second:
                        add(first + second)
        elif pattern == "blend":
            # Overlap the tail of one root with the head of another where they
            # share a letter — design + ignite -> designite.
            for first in roots:
                for second in roots:
                    if first == second:
                        continue
                    for overlap in range(min(3, len(first), len(second)), 0, -1):
                        if first[-overlap:] == second[:overlap]:
                            add(first + second[overlap:])
                            break
    return out


def pronounceable(name: str) -> bool:
    """Reject names with no vowel or with 4+ consonants in a row."""
    if not VOWELS & set(name):
        return False
    return not re.search(r"[^aeiou]{4,}", name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Combine roots and affixes into candidate names.")
    parser.add_argument("--roots", required=True,
                        help="Comma-separated word roots, e.g. snap,clip,vault")
    parser.add_argument("--prefixes", default="",
                        help="Comma-separated prefixes, e.g. up,re,neo")
    parser.add_argument("--suffixes", default="",
                        help="Comma-separated suffixes, e.g. ify,ly,kit,hub")
    parser.add_argument("--patterns", default="root+suffix,prefix+root",
                        help="Comma-separated: root, root+suffix, prefix+root, "
                             "prefix+root+suffix, root+root, blend")
    parser.add_argument("--min-len", type=int, default=3, help="Minimum length.")
    parser.add_argument("--max-len", type=int, default=0,
                        help="Maximum length. 0 means no limit.")
    parser.add_argument("--no-filter", action="store_true",
                        help="Skip the pronounceability filter.")
    args = parser.parse_args()

    roots = split_list(args.roots)
    prefixes = split_list(args.prefixes)
    suffixes = split_list(args.suffixes)
    patterns = split_list(args.patterns)

    needs = {
        "root+suffix": (suffixes, "--suffixes"),
        "prefix+root": (prefixes, "--prefixes"),
        "prefix+root+suffix": (prefixes and suffixes, "--prefixes and --suffixes"),
    }
    for pattern in patterns:
        required, flag = needs.get(pattern, (True, ""))
        if not required:
            print(f"  ! pattern '{pattern}' needs {flag}; skipping", file=sys.stderr)

    names = combine(prefixes, roots, suffixes, patterns)

    kept = []
    for name in names:
        if not name.isalnum():
            continue
        if len(name) < args.min_len:
            continue
        if args.max_len and len(name) > args.max_len:
            continue
        if not args.no_filter and not pronounceable(name):
            continue
        kept.append(name)

    if not kept:
        print("No candidates survived the filters. Loosen --max-len or add roots.",
              file=sys.stderr)
        return 1

    print("\n".join(kept))
    print(f"  {len(kept)} candidate(s) from {len(names)} combination(s)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
