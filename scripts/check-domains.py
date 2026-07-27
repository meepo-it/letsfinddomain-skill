#!/usr/bin/env python3
"""Check domain availability and attach reference pricing.

Availability comes from whichever provider is configured (Spaceship, NameSilo,
or the keyless RDAP fallback). Pricing comes from Porkbun's public TLD price
list, which needs no credentials.

Rate limiting is persisted to disk, so the budget is respected across separate
invocations of this script and across parallel agents. See
references/rate-limits.md.

Usage:
    python3 scripts/check-domains.py snapkit.com snapkit.io
    python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly
    cat candidates.txt | python3 scripts/check-domains.py --available-only
    python3 scripts/check-domains.py --json snapkit.com

Run with --help for the full option list.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import fcntl  # POSIX only; used to make the on-disk state parallel-safe
except ImportError:  # pragma: no cover - Windows
    fcntl = None

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / ".cache"

PORKBUN_PRICING_URL = "https://api.porkbun.com/api/json/v3/pricing/get"
SPACESHIP_AVAILABILITY_URL = "https://spaceship.dev/api/v1/domains/available"
NAMESILO_AVAILABILITY_URL = "https://www.namesilo.com/api/checkRegisterAvailability"
IANA_RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
RDAP_QUERY_URL = "https://rdap.org/domain/{domain}"

SPACESHIP_BATCH_SIZE = 20   # hard API limit
NAMESILO_BATCH_SIZE = 20    # self-imposed, keeps the GET URL short

DEFAULT_PRICE_TTL = 86400   # 1 day
DEFAULT_RESULT_TTL = 3600   # 1 hour
MAX_RETRIES = 4

DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9-]+)+$")

# Per-provider request budgets: (max_requests, window_seconds, min_interval).
#
# Spaceship's documented limit is 30 requests per user per 30 seconds. We
# default to 25 so that a second tool sharing the same key does not push us
# over. NameSilo does not publish a precise per-second figure, so the default
# is deliberately conservative. RDAP goes through a shared public proxy that we
# have no business hammering, hence the one-second floor between requests.
RATE_LIMITS = {
    "spaceship": (25, 30.0, 0.2),
    "namesilo": (20, 60.0, 0.5),
    "rdap": (60, 60.0, 1.0),
}


# --------------------------------------------------------------------------
# env
# --------------------------------------------------------------------------

def load_dotenv() -> None:
    """Load REPO_ROOT/.env without overriding variables already in the env."""
    env_file = REPO_ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_int(name: str, default: int) -> int:
    try:
        return int(env(name) or default)
    except ValueError:
        return default


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# shared on-disk state (parallel-safe)
# --------------------------------------------------------------------------

class JsonState:
    """A small JSON file guarded by an advisory lock.

    Several agents may run this script at once. Without the lock they would
    each read a stale request log, conclude they have budget, and collectively
    blow through the provider's limit.
    """

    def __init__(self, path: Path):
        self.path = path
        CACHE_DIR.mkdir(exist_ok=True)

    def _read(self, handle) -> dict:
        handle.seek(0)
        raw = handle.read()
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def update(self, mutate):
        """Atomically read → mutate → write. Returns whatever mutate returns."""
        with open(self.path, "a+", encoding="utf-8") as handle:
            if fcntl:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                data = self._read(handle)
                result = mutate(data)
                handle.seek(0)
                handle.truncate()
                json.dump(data, handle)
                handle.flush()
                return result
            finally:
                if fcntl:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def read(self) -> dict:
        if not self.path.is_file():
            return {}
        with open(self.path, "r", encoding="utf-8") as handle:
            if fcntl:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                return self._read(handle)
            finally:
                if fcntl:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class RateLimiter:
    """Sliding-window limiter whose state survives process exit.

    The window of recent request timestamps lives in `.cache/`, so a budget
    spent by one invocation is still spent as far as the next invocation is
    concerned. This is the whole point: an agent typically calls this script
    many times in a single session, and an in-process sleep would protect
    none of those calls from each other.
    """

    def __init__(self, provider: str, quiet: bool = False):
        limit, window, min_interval = RATE_LIMITS.get(provider, (20, 60.0, 0.5))
        self.provider = provider
        self.limit = env_int(f"DOMAIN_FINDER_{provider.upper()}_LIMIT", limit)
        self.window = float(env_int(f"DOMAIN_FINDER_{provider.upper()}_WINDOW", int(window)))
        self.min_interval = min_interval
        self.quiet = quiet
        self.state = JsonState(CACHE_DIR / f"ratelimit-{provider}.json")
        self.waited = 0.0

    def _prune(self, data: dict) -> list:
        now = time.time()
        stamps = [t for t in data.get("requests", []) if now - t < self.window]
        data["requests"] = stamps
        return stamps

    def acquire(self) -> None:
        """Block until it is safe to issue one request, then record it."""
        while True:
            def mutate(data):
                now = time.time()
                cooldown = data.get("cooldown_until", 0)
                if cooldown > now:
                    return cooldown - now

                stamps = self._prune(data)
                if len(stamps) >= self.limit:
                    # Wait for the oldest request to age out of the window.
                    return (stamps[0] + self.window) - now + 0.05

                last = stamps[-1] if stamps else 0
                gap = self.min_interval - (now - last)
                if gap > 0:
                    return gap

                stamps.append(now)
                return 0.0

            delay = self.state.update(mutate)
            if delay <= 0:
                return
            if delay > 1 and not self.quiet:
                print(f"  · rate limit for {self.provider}: waiting {delay:.0f}s",
                      file=sys.stderr)
            self.waited += delay
            time.sleep(min(delay, 60))

    def penalise(self, retry_after: float) -> None:
        """The provider said 429. Park every worker until the cooldown expires."""
        until = time.time() + retry_after

        def mutate(data):
            data["cooldown_until"] = max(data.get("cooldown_until", 0), until)
            return None

        self.state.update(mutate)
        if not self.quiet:
            print(f"  ! {self.provider} returned 429; backing off {retry_after:.0f}s",
                  file=sys.stderr)

    def estimate(self, requests: int) -> float:
        """Rough seconds needed for `requests` calls, given budget already spent."""
        spent = len(self._prune(dict(self.state.read())))
        free_now = max(0, self.limit - spent)
        if requests <= free_now:
            return requests * self.min_interval
        overflow = requests - free_now
        windows = -(-overflow // self.limit)  # ceil
        return windows * self.window


# --------------------------------------------------------------------------
# result cache
# --------------------------------------------------------------------------

class ResultCache:
    """Short-lived availability cache.

    In practice an agent checks overlapping candidate sets several times in a
    row — generate 30, check, refine, check again. Without a cache those
    repeats burn the request budget for answers we already have. Availability
    does not meaningfully change within the hour, so a short TTL is safe, and
    cached rows are labelled in the output.
    """

    def __init__(self, ttl: int, enabled: bool = True):
        self.ttl = ttl
        self.enabled = enabled and ttl > 0
        self.state = JsonState(CACHE_DIR / "availability.json")
        self._data = self.state.read() if self.enabled else {}

    def get(self, domain: str):
        if not self.enabled:
            return None
        entry = self._data.get(domain)
        if not entry or (time.time() - entry.get("ts", 0)) > self.ttl:
            return None
        return entry

    def put_many(self, results: dict) -> None:
        if not self.enabled or not results:
            return
        now = time.time()

        def mutate(data):
            for domain, payload in results.items():
                data[domain] = {**payload, "ts": now}
            # Keep the file from growing without bound.
            stale = [k for k, v in data.items()
                     if now - v.get("ts", 0) > max(self.ttl * 24, 86400)]
            for key in stale:
                data.pop(key, None)
            return None

        self.state.update(mutate)


# --------------------------------------------------------------------------
# http
# --------------------------------------------------------------------------

def _retry_after(headers, fallback: float) -> float:
    raw = headers.get("Retry-After") if headers else None
    if raw:
        try:
            return max(1.0, float(raw))
        except ValueError:
            pass
    return fallback


def request_json(url, *, method="GET", headers=None, payload=None,
                 limiter=None, timeout=30, quiet=False):
    """One rate-limited HTTP call with backoff. Returns (status, body, headers)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None

    for attempt in range(MAX_RETRIES):
        if limiter:
            limiter.acquire()

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("User-Agent", "domain-finder-skill/1.0")
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            req.add_header(key, value)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                try:
                    return resp.status, json.loads(body), resp.headers
                except json.JSONDecodeError:
                    return resp.status, None, resp.headers

        except urllib.error.HTTPError as exc:
            # 429 = rate limited, 5xx = transient. Both are worth retrying with
            # exponential backoff plus jitter so parallel agents desynchronise.
            if exc.code == 429 or 500 <= exc.code < 600:
                backoff = min(60.0, (2 ** attempt) * 2) + random.uniform(0, 1.5)
                delay = _retry_after(exc.headers, backoff)
                if exc.code == 429 and limiter:
                    limiter.penalise(delay)
                elif not quiet:
                    print(f"  · HTTP {exc.code}, retrying in {delay:.0f}s",
                          file=sys.stderr)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)
                    continue
            body = exc.read().decode("utf-8", "replace")
            try:
                return exc.code, json.loads(body), exc.headers
            except json.JSONDecodeError:
                return exc.code, None, exc.headers

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < MAX_RETRIES - 1:
                delay = min(30.0, (2 ** attempt) * 2) + random.uniform(0, 1)
                if not quiet:
                    print(f"  · network error ({exc}), retrying in {delay:.0f}s",
                          file=sys.stderr)
                time.sleep(delay)
                continue
            if not quiet:
                print(f"  ! network error for {url}: {exc}", file=sys.stderr)
            return 0, None, None

    return 0, None, None


def request_status(url, *, limiter=None, timeout=20, quiet=False) -> int:
    """Rate-limited probe used by the RDAP fallback. 0 means give up."""
    for attempt in range(MAX_RETRIES):
        if limiter:
            limiter.acquire()
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "domain-finder-skill/1.0")
        req.add_header("Accept", "application/rdap+json")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or 500 <= exc.code < 600:
                backoff = min(60.0, (2 ** attempt) * 2) + random.uniform(0, 1.5)
                delay = _retry_after(exc.headers, backoff)
                if exc.code == 429 and limiter:
                    limiter.penalise(delay)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)
                    continue
            return exc.code
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt < MAX_RETRIES - 1:
                time.sleep(min(30.0, (2 ** attempt) * 2))
                continue
            return 0
    return 0


# --------------------------------------------------------------------------
# pricing (Porkbun public endpoint — no credentials, no rate limiter needed)
# --------------------------------------------------------------------------

def load_tld_prices(ttl: int, quiet: bool = False) -> dict:
    cache_file = CACHE_DIR / "porkbun-pricing.json"
    if cache_file.is_file() and (time.time() - cache_file.stat().st_mtime) < ttl:
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    status, body, _ = request_json(PORKBUN_PRICING_URL, method="POST",
                                   payload={}, quiet=quiet)
    if status != 200 or not body or body.get("status") != "SUCCESS":
        if cache_file.is_file():
            if not quiet:
                print("  · Porkbun pricing unreachable; using stale cache",
                      file=sys.stderr)
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        if not quiet:
            print("  ! could not fetch Porkbun pricing; continuing without prices",
                  file=sys.stderr)
        return {}

    pricing = body.get("pricing", {})
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(pricing), encoding="utf-8")
    return pricing


def price_for(domain: str, pricing: dict) -> dict:
    if not pricing:
        return {}
    labels = domain.split(".")
    for i in range(1, len(labels)):  # longest suffix first, so .co.uk beats .uk
        tld = ".".join(labels[i:])
        if tld in pricing:
            entry = pricing[tld]
            return {
                "tld": tld,
                "registration": _to_float(entry.get("registration")),
                "renewal": _to_float(entry.get("renewal")),
            }
    return {}


# --------------------------------------------------------------------------
# availability providers
# --------------------------------------------------------------------------

def check_spaceship(domains, limiter, quiet):
    key, secret = env("SPACESHIP_API_KEY"), env("SPACESHIP_API_SECRET")
    headers = {"X-Api-Key": key, "X-Api-Secret": secret}
    results = {}

    for i in range(0, len(domains), SPACESHIP_BATCH_SIZE):
        batch = domains[i:i + SPACESHIP_BATCH_SIZE]
        status, body, _ = request_json(
            SPACESHIP_AVAILABILITY_URL, method="POST", headers=headers,
            payload={"domains": batch}, limiter=limiter, quiet=quiet)

        if status != 200 or not body:
            detail = (body or {}).get("detail", f"HTTP {status}")
            if not quiet:
                print(f"  ! Spaceship error: {detail}", file=sys.stderr)
            for domain in batch:
                results[domain] = {"status": "error"}
            continue

        for item in body.get("domains", []):
            name = item.get("domain", "")
            raw = item.get("result", "")  # "available" | "taken"
            results[name] = {
                "status": {"available": "available", "taken": "taken"}.get(raw, raw or "unknown"),
                "premium": bool(item.get("premiumPricing")),
            }
    return results


def check_namesilo(domains, limiter, quiet):
    key = env("NAMESILO_API_KEY")
    results = {}

    for i in range(0, len(domains), NAMESILO_BATCH_SIZE):
        batch = domains[i:i + NAMESILO_BATCH_SIZE]
        url = (f"{NAMESILO_AVAILABILITY_URL}?version=1&type=json"
               f"&key={key}&domains={','.join(batch)}")
        status, body, _ = request_json(url, limiter=limiter, quiet=quiet)
        reply = (body or {}).get("reply", {})

        if status != 200 or str(reply.get("code")) != "300":
            detail = reply.get("detail", f"HTTP {status}")
            if not quiet:
                print(f"  ! NameSilo error: {detail}", file=sys.stderr)
            for domain in batch:
                results[domain] = {"status": "error"}
            continue

        for bucket, label in (("available", "available"), ("unavailable", "taken")):
            entry = reply.get(bucket)
            if not entry:
                continue
            names = entry.get("domain", entry)
            if isinstance(names, (str, dict)):
                names = [names]
            for name in names:
                if isinstance(name, dict):
                    name = name.get("#text") or name.get("domain", "")
                if name:
                    results[name] = {"status": label}

        for domain in batch:
            results.setdefault(domain, {"status": "unknown"})
    return results


def load_rdap_tlds(quiet=False) -> set:
    cache_file = CACHE_DIR / "rdap-tlds.json"
    if cache_file.is_file() and (time.time() - cache_file.stat().st_mtime) < 604800:
        try:
            return set(json.loads(cache_file.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    status, body, _ = request_json(IANA_RDAP_BOOTSTRAP_URL, quiet=quiet)
    if status != 200 or not body:
        return set()
    tlds = {t.lower() for service in body.get("services", []) for t in service[0]}
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(sorted(tlds)), encoding="utf-8")
    return tlds


def check_rdap(domains, limiter, quiet):
    """Keyless availability via RDAP.

    404 means no registration record (available), 200 means taken. A TLD with
    no RDAP server ALSO 404s, which would be a false "available" — so TLDs
    outside the IANA bootstrap list are reported as unsupported, not guessed.
    """
    rdap_tlds = load_rdap_tlds(quiet)
    results = {}
    for domain in domains:
        tld = domain.rsplit(".", 1)[-1].lower()
        if rdap_tlds and tld not in rdap_tlds:
            results[domain] = {"status": "unsupported"}
            continue
        status = request_status(RDAP_QUERY_URL.format(domain=domain),
                                limiter=limiter, quiet=quiet)
        results[domain] = {"status": {404: "available", 200: "taken"}.get(status, "unknown")}
    return results


PROVIDERS = {
    "spaceship": check_spaceship,
    "namesilo": check_namesilo,
    "rdap": check_rdap,
}


def pick_provider() -> str:
    if env("SPACESHIP_API_KEY") and env("SPACESHIP_API_SECRET"):
        return "spaceship"
    if env("NAMESILO_API_KEY"):
        return "namesilo"
    if env("DOMAIN_FINDER_ALLOW_RDAP") in ("1", "true", "yes"):
        return "rdap"
    return ""


def requests_needed(provider: str, count: int) -> int:
    if provider == "spaceship":
        return -(-count // SPACESHIP_BATCH_SIZE)
    if provider == "namesilo":
        return -(-count // NAMESILO_BATCH_SIZE)
    return count  # rdap: one per domain


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

STATUS_LABEL = {
    "available": "available",
    "taken": "taken",
    "unsupported": "no RDAP for this TLD",
    "error": "lookup failed",
    "unknown": "unknown",
}


def build_note(row: dict) -> str:
    notes = []
    price = row.get("price") or {}
    reg, ren = price.get("registration"), price.get("renewal")
    if row["status"] == "available" and reg and ren and ren > reg * 1.5:
        notes.append(f"renewal {ren / reg:.1f}x the first year")
    if row.get("premium"):
        notes.append("premium domain — price differs")
    if row["status"] == "unsupported":
        notes.append("check manually at a registrar")
    if row["status"] == "error":
        notes.append("retry this one")
    if row.get("cached"):
        notes.append("cached")
    return "; ".join(notes)


def render_table(rows) -> str:
    lines = ["| Domain | Status | Reg. (1st yr) | Renewal | Note |",
             "|---|---|---|---|---|"]
    for row in rows:
        price = row.get("price") or {}
        if row["status"] == "available":
            reg = f"${price['registration']:.2f}" if price.get("registration") is not None else "—"
            ren = f"${price['renewal']:.2f}" if price.get("renewal") is not None else "—"
        else:
            reg = ren = "—"
        lines.append(f"| {row['domain']} | {STATUS_LABEL.get(row['status'], row['status'])} "
                     f"| {reg} | {ren} | {row.get('note', '')} |")
    return "\n".join(lines)


def humanise(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    return f"{seconds / 60:.0f}m{seconds % 60:.0f}s"


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def expand_domains(items, tlds):
    out, seen = [], set()
    for item in items:
        item = item.strip().lower().lstrip(".")
        if not item:
            continue
        for candidate in ([item] if "." in item else [f"{item}.{t}" for t in tlds]):
            if candidate not in seen:
                seen.add(candidate)
                out.append(candidate)
    return out


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Check domain availability with reference pricing.")
    parser.add_argument("domains", nargs="*",
                        help="Full domains (snapkit.com) or bare names (snapkit).")
    parser.add_argument("--tlds", default=env("DOMAIN_FINDER_DEFAULT_TLDS", "com"),
                        help="Comma-separated TLDs for bare names. Default: com")
    parser.add_argument("--available-only", action="store_true",
                        help="Only print domains that are available.")
    parser.add_argument("--max-price", type=float,
                        default=_to_float(env("DOMAIN_FINDER_MAX_PRICE")),
                        help="Hide available domains above this first-year price (USD).")
    parser.add_argument("--no-price", action="store_true",
                        help="Skip the Porkbun price lookup entirely.")
    parser.add_argument("--no-cache", action="store_true",
                        help="Ignore cached results and re-query every domain.")
    parser.add_argument("--plan", action="store_true",
                        help="Show the request plan and time estimate, then exit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages.")
    args = parser.parse_args()

    raw = list(args.domains)
    if not sys.stdin.isatty():
        raw.extend(sys.stdin.read().split())
    if not raw:
        parser.error("no domains given (pass them as arguments or on stdin)")

    tlds = [t.strip().lstrip(".") for t in args.tlds.split(",") if t.strip()]
    domains = expand_domains(raw, tlds or ["com"])

    invalid = [d for d in domains if not DOMAIN_RE.match(d)]
    domains = [d for d in domains if DOMAIN_RE.match(d)]
    if invalid and not args.quiet:
        print(f"  ! skipping invalid: {', '.join(invalid)}", file=sys.stderr)
    if not domains:
        print("No valid domains to check.", file=sys.stderr)
        return 1

    provider = pick_provider()
    if not provider:
        print("No availability provider configured.\n"
              "Set SPACESHIP_API_KEY + SPACESHIP_API_SECRET (recommended),\n"
              "or NAMESILO_API_KEY, or DOMAIN_FINDER_ALLOW_RDAP=1 for the keyless\n"
              "fallback. See references/environment.md.", file=sys.stderr)
        return 2

    limiter = RateLimiter(provider, args.quiet)
    cache = ResultCache(env_int("DOMAIN_FINDER_CACHE_TTL", DEFAULT_RESULT_TTL),
                        enabled=not args.no_cache)

    cached, to_query = {}, []
    for domain in domains:
        hit = cache.get(domain)
        if hit and hit.get("status") not in ("error", "unknown"):
            cached[domain] = {**hit, "cached": True}
        else:
            to_query.append(domain)

    calls = requests_needed(provider, len(to_query))
    eta = limiter.estimate(calls)

    if args.plan:
        print(f"provider:        {provider}")
        print(f"domains:         {len(domains)} ({len(cached)} cached, {len(to_query)} to query)")
        print(f"requests:        {calls}")
        print(f"budget:          {limiter.limit} requests / {limiter.window:.0f}s")
        print(f"estimated time:  {humanise(eta)}")
        return 0

    if not args.quiet and to_query:
        note = f", {len(cached)} from cache" if cached else ""
        eta_note = f", ~{humanise(eta)}" if eta > 10 else ""
        print(f"  checking {len(to_query)} domain(s) via {provider} "
              f"in {calls} request(s){note}{eta_note}…", file=sys.stderr)
    elif not args.quiet and cached:
        print(f"  all {len(cached)} domain(s) served from cache", file=sys.stderr)

    fresh = PROVIDERS[provider](to_query, limiter, args.quiet) if to_query else {}
    cache.put_many({d: v for d, v in fresh.items()
                    if v.get("status") in ("available", "taken")})

    pricing = {} if args.no_price else load_tld_prices(
        env_int("DOMAIN_FINDER_PRICE_TTL", DEFAULT_PRICE_TTL), args.quiet)

    rows = []
    for domain in domains:
        entry = cached.get(domain) or fresh.get(domain) or {"status": "unknown"}
        row = {
            "domain": domain,
            "status": entry.get("status", "unknown"),
            "premium": entry.get("premium", False),
            "cached": entry.get("cached", False),
            "price": price_for(domain, pricing),
        }
        row["note"] = build_note(row)
        rows.append(row)

    failed = [r["domain"] for r in rows if r["status"] in ("error", "unknown")]

    if args.available_only:
        rows = [r for r in rows if r["status"] == "available"]
    if args.max_price is not None:
        rows = [r for r in rows
                if r["status"] != "available"
                or (r.get("price") or {}).get("registration") is None
                or r["price"]["registration"] <= args.max_price]

    if args.json:
        print(json.dumps({"rows": rows, "unresolved": failed}, indent=2, ensure_ascii=False))
    else:
        print(render_table(rows) if rows else "No domains matched.")
        if pricing and rows:
            print("\n> Prices are Porkbun list prices in USD, shown as a reference. "
                  "Your registrar will differ. Premium domains are priced separately.")
        if failed:
            print(f"\n> {len(failed)} domain(s) could not be resolved and are NOT "
                  f"confirmed available: {', '.join(failed[:10])}"
                  f"{' …' if len(failed) > 10 else ''}")

    # Partial success is still a non-zero exit, so a caller can tell.
    return 3 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
