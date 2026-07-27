# Query recipes

Common constraints, and the exact commands that satisfy them. Use this to
translate what someone asks for into what you run.

All examples assume you are in the repo root with a provider configured.

---

## By constraint

### "Only .com"

`.com` is the default, so there is nothing to configure:

```bash
python3 scripts/check-domains.py --tlds com snapkit vaultly forgehub
```

To make it the default for every command in this checkout, set
`DOMAIN_FINDER_DEFAULT_TLDS=com` in `.env`.

When a user insists on `.com`, exhaust name variations before proposing another
TLD. The generator exists for exactly this — it is cheaper to try forty spellings
of the idea than to talk someone into `.io`.

### "No more than 6 characters"

Length is a property of the *name*, not the domain, so filter at generation:

```bash
python3 scripts/gen-names.py --roots snap,clip,pix,vault --suffixes ify,ly,kit \
  --max-len 6 | python3 scripts/check-domains.py --tlds com --available-only
```

For a list you already have, filter with `awk` on the label before the dot:

```bash
cat candidates.txt | awk -F. 'length($1) <= 6' \
  | python3 scripts/check-domains.py --available-only
```

Note that at six characters or fewer, almost every pronounceable `.com` is
already registered. Expect a very low hit rate and generate accordingly — start
with 100+ candidates, not 10.

### "Something ending in -ify / -ly"

```bash
python3 scripts/gen-names.py \
  --roots snap,clip,vault,forge,craft,thumb \
  --suffixes ify,ly \
  --patterns root+suffix \
  | python3 scripts/check-domains.py --tlds com --available-only
```

Other suffix families worth trying, from
[`naming-guide.md`](naming-guide.md): `kit hub lab box base stack flow` for
tool-shaped products, `io ix ex ai ax` for a technical feel, `er or ist` when
the product acts like a person doing a job.

### "Starting with up- / re- / un-"

```bash
python3 scripts/gen-names.py --roots mock,clip,blur,size \
  --prefixes up,re,un --patterns prefix+root --max-len 8 \
  | python3 scripts/check-domains.py --tlds com --available-only
```

This pattern is unusually productive because it turns a taken generic word into
an available coined one — `mock` is long gone, `upmock` may not be.

### "Under $20 a year"

```bash
python3 scripts/check-domains.py --tlds com,dev,app,xyz snapkit vaultly \
  --available-only --max-price 20
```

`--max-price` filters on the **first-year** price. Always read the renewal
column too — `.xyz` passes a $20 filter at $2.04 and then costs $12.98 every
following year. The script flags jumps above 1.5x in the `Note` column.

### "Try a bunch of TLDs"

```bash
python3 scripts/check-domains.py --tlds com,ai,io,dev,app,co,xyz,net snapkit
```

Cost check before you widen: names × TLDs = domains, and 20 domains per request.
Ten names across eight TLDs is 80 domains, or 4 requests. Run `--plan` first if
the list is large.

### "Blend two words"

```bash
python3 scripts/gen-names.py --roots design,ignite,snap,apex,forge,edge \
  --patterns blend --max-len 12 \
  | python3 scripts/check-domains.py --tlds com --available-only
```

`blend` overlaps a shared letter between two roots — `design` + `ignite`
becomes `designite`, `snap` + `apex` becomes `snapex`.

### "Just tell me if these specific ones are free"

```bash
python3 scripts/check-domains.py acme.com acme.io acme.dev
# or from a file
python3 scripts/check-domains.py < my-shortlist.txt
```

---

## Combining constraints

The realistic case is several constraints at once. "A `.com`, six characters
max, ending in -ly or -ify, under $15":

```bash
python3 scripts/gen-names.py \
  --roots snap,clip,pix,vault,forge,mint,dash,bolt \
  --suffixes ify,ly \
  --patterns root+suffix \
  --max-len 6 \
  | python3 scripts/check-domains.py --tlds com --available-only --max-price 15
```

Order matters for cost: filter at generation (free) before checking (rate
limited). Never generate 500 candidates, check them all, and *then* apply a
length filter — you will have spent 25 requests to throw most of the answers
away.

---

## Working at scale

### Preview the cost first

```bash
python3 scripts/check-domains.py --plan --tlds com,ai,io,dev $(cat names.txt)
```

### Feed the whole list in one call

One call with 200 domains is 10 requests. Two hundred calls with one domain each
is 200 requests, and will get you throttled.

```bash
# good
python3 scripts/check-domains.py $(cat names.txt) --tlds com

# bad
for n in $(cat names.txt); do python3 scripts/check-domains.py "$n.com"; done
```

### Save results for later processing

```bash
python3 scripts/check-domains.py --json --tlds com $(cat names.txt) > results.json

# cheapest available names first
python3 -c "
import json
rows = json.load(open('results.json'))['rows']
avail = [r for r in rows if r['status'] == 'available']
avail.sort(key=lambda r: (r.get('price') or {}).get('registration') or 999)
for r in avail[:20]:
    p = (r.get('price') or {}).get('registration')
    print(f\"{r['domain']:30} \${p}\" if p else r['domain'])
"
```

### Re-check right before buying

Cached results are up to an hour old. Before someone actually pays:

```bash
python3 scripts/check-domains.py --no-cache the-one-you-picked.com
```

---

## Reading the output

| Column value | Meaning |
|---|---|
| `available` | No registration record. Registrable, subject to premium pricing and registry reservations. |
| `taken` | Registered. |
| `no RDAP for this TLD` | The keyless fallback cannot answer for this TLD. **Not** a "no". Configure a real provider, or check by hand. |
| `lookup failed` | The request errored after retries. **Not** confirmed available. |
| `unknown` | Provider returned something unexpected. Treat as unresolved. |
| Note: `renewal 6.4x the first year` | Introductory pricing. Budget for the renewal, not the promo. |
| Note: `premium domain — price differs` | Registry has priced this one specially. Get a real quote. |
| Note: `cached` | Served from cache, up to an hour old. |

The script exits `3` when anything was left unresolved, so you can branch on it
in a pipeline instead of parsing the text.

---

## Before recommending a name

Availability is necessary, not sufficient. For a shortlist you are about to
present:

1. **Search the bare name.** If an established product, company, or well-known
   open-source project already uses it, the user will spend years fighting them
   for their own name in search results. Say so explicitly.
2. **Check social handles** if the project needs them. A free `.com` with the
   handle taken everywhere is a partial win at best.
3. **Say the name aloud.** If it needs spelling out over a phone call, it will
   need spelling out in every podcast, demo, and conference talk.
4. **Check it in other languages** if the audience is not English-only.

None of this is automated here, and none of it should be skipped.
