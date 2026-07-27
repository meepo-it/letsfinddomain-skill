# Naming guide

A palette of word roots, affixes and combination patterns for generating domain
candidates.

**This is a starting point, not a whitelist.** Nothing here is a rule. There are
no length limits, no price ceilings, and no ranking of TLDs — those belong to
the project and the person naming it, not to a reference file. Take what is
useful, ignore the rest, and invent freely beyond it.

Most entries feed straight into the generator:

```bash
python3 scripts/gen-names.py --roots snap,clip,vault --suffixes ify,ly,kit \
  | python3 scripts/check-domains.py --tlds com --available-only
```

---

## Suffixes

| Family | Members | Feel |
|---|---|---|
| Verb-forming | `ify ize en ate` | turns a noun into an action |
| Technical | `ly io ix ex ai ax ux` | product-shaped, modern |
| Tool / platform | `hub lab box kit base stack flow form ware sync node dash pad dock port` | infrastructure, developer-facing |
| Brandable | `ia ya ora era ova ium um is us o a` | invented-word, company-shaped |
| Agent / role | `er or ist ster ant ent` | the thing does a job for you |
| Place | `ery ary ory` | a collection or a venue |
| Energetic | `up` | motion, startup connotation |
| Other | `oid ette ling ink` | |

## Prefixes

| Family | Members |
|---|---|
| Degree | `super ultra hyper mega meta neo pro prime max plus elite omni` |
| Direction / time | `next pre post re un out up over inter trans multi co` |
| Quantity | `all any one zero uni mono poly pan` |
| Technical | `auto smart cyber digi tech data info web net cloud ai` |

---

## Action roots

| Family | Members |
|---|---|
| Create | Build Make Create Craft Forge Form Gen Render Design Draw Paint Write Code |
| Acquire | Get Grab Fetch Find Seek Hunt Pick Pull Catch Collect |
| Move | Go Run Move Shift Turn Flip Spin Push Drop Launch Ship Send Fly Jump Dash Rush Bolt Jet |
| Process | Edit Cut Trim Clip Crop Slice Split Merge Mix Blend Fuse Morph Transform Convert Swap |
| Store | Save Store Keep Hold Lock Guard Vault Cache Archive Backup |
| Display | Show View See Look Watch Display Present Reveal Preview |
| Interact | Click Tap Snap Scan Swipe Scroll Slide Touch Press |
| Amplify | Boost Grow Scale Expand Lift Rise Amp Power Charge Fuel |
| Connect | Link Connect Join Meet Sync Bridge Bind Wire Chain |
| Share | Share Send Give Pass Post Broadcast Spread |

## Quality roots

| Family | Members |
|---|---|
| Speed | Fast Quick Instant Snap Flash Swift Rapid Turbo Zoom Rush Bolt Jet |
| Simplicity | Easy Simple Clear Clean Pure Plain Lite Slim Lean Minimal Tiny Micro Mini |
| Intelligence | Smart Auto Wise Clever Bright Sharp Deep Neural |
| Quality | Better Best Top First Prime Elite Fine True Real Pro Premium |
| Novelty | New Next Fresh Novel Modern Future Forward Advanced |
| Scale | Big Mega Giant Huge Vast Grand Tiny Micro Mini Nano |

## Place roots

Zone Space Place Spot Point Port Gate Path Way Lane Track Route Field Area
Range Scope Domain Realm World Land Site Base Camp Den Nest Dock Bay Harbor
Station Terminal Depot Forge Mill Shop Studio House Room Vault Locker Bunker
Tower Peak Summit

## Imagery roots

| Family | Members |
|---|---|
| Celestial | Star Sun Moon Luna Solar Nova Cosmic Galaxy Orbit Sky Cloud Air Wind Storm |
| Light | Light Glow Bright Shine Spark Flash Beam Ray Prism Spectrum Shadow Dark |
| Water | Wave Flow Tide Current Stream Drift |
| Fire | Fire Flame Blaze Burn Heat Ember Torch |
| Plant | Tree Leaf Bloom Flower Seed Root Branch Forest Garden Green |
| Colour | Red Blue Green Black White Gold Silver Cyan Violet Amber Coral Indigo |

## Social roots

Team Crew Squad Group Club Circle Community Network Link Bond Bridge Friend
Buddy Mate Pal Partner Ally Fellow Peer Member Guest Host

## Abstract roots

| Family | Members |
|---|---|
| Mind | Mind Brain Think Idea Concept Logic Reason Vision Dream Imagine |
| Core | Core Heart Soul Essence Center Focus Key Prime Main Central |
| Energy | Power Energy Force Charge Fuel Drive Pulse Volt Amp Watt |
| Time | Time Moment Instant Now Ever Always Forever Daily Hour Chrono |
| Trust | Trust Safe Secure Guard Shield Protect Defend Cover Armor |

---

## Combination patterns

| Pattern | Generator flag | Examples |
|---|---|---|
| prefix + root | `--patterns prefix+root` | SuperArt, AutoGen, SmartPic, NextGen, ReCreate |
| root + suffix | `--patterns root+suffix` | Craftify, Artly, Pixio, Vaultbase, Flowstack |
| root + root | `--patterns root+root` | Dreamforge, Skylab, Mindflow, Cloudcraft |
| prefix + root + suffix | `--patterns prefix+root+suffix` | Ultragenify, Neocraftly, Proartify |
| blended overlap | `--patterns blend` | design + ignite → Designite; snap + apex → Snapex |

## Patterns that recur in the wild

| Pattern | Real examples |
|---|---|
| verb + ify | Spotify, Shopify, Netlify |
| noun + ly | Bitly, Fastly, Grammarly |
| noun + hub | GitHub, Segmenthub |
| noun + lab | GitLab, Designlab |
| noun + base | Firebase, Coinbase, Supabase |
| noun + box | Dropbox, Sandbox, Pitchbox |
| noun + flow | Webflow, Cashflow, Userflow |
| noun + stack | Fullstack, Techstack |
| adjective + noun | Clearbit, Brightcove, DeepMind |
| verb + noun | Snapchat, Dropbox, Pushover |
| re + verb | Remix, Replit, Retool |
| noun + up | Meetup, Popup, Signup, Roundup, Standup |

---

## A strategy worth knowing: coin the word, take the .com

The idea: someone reading the domain can guess what the product does, but the
word itself is invented — so the `.com` is obtainable and the search results
belong to you alone.

Take the keyword for your space and deform it until it becomes a new word:

| Space | Deformation | Result |
|---|---|---|
| thumbnail maker | truncate `thumb` + suffix `ify` | thumbify |
| mock | prefix `up` + variant `moker` | upmoker |
| screenshot | contract to `snp` + `shot` | snpshot |
| invoice | `invo` + root `craft` | invocraft |

Four techniques that produce most of these:

1. **Truncate and attach** — take the front of the keyword, add a suffix
   (`thumb` + `ify`, `snap` + `kit`)
2. **Prefix a generic** — `up` / `re` / `un` + a taken word makes an untaken one
   (`upmock`, `reclip`, `unblur`)
3. **Respell** — nudge the spelling while keeping it readable
   (`pix` → `pixl`, `click` → `clik`)
4. **Blend syllables** — overlap two keywords (`design` + `ignite` → `designite`)

The target: the name hints at the function, but on a search engine the word is
yours.

Techniques 1, 2 and 4 are all available in the generator — see
[`query-recipes.md`](query-recipes.md).

---

## Things generally worth weighing

Not rules. Considerations that tend to matter, which you can trade away
deliberately when there's a reason.

- **Say it out loud.** If it needs spelling out on a phone call, it will need
  spelling out forever.
- **One spelling.** If a listener could plausibly write it two ways, you will
  lose traffic to whoever owns the other one.
- **Check the collision.** Someone else's established product with your name is
  an SEO fight you did not choose and may not win.
- **Check other languages** if the audience is not English-only.
- **Generate more than feels necessary.** Good short names are mostly taken;
  hit rates are low, and checking is cheap in bulk.
- **Renewal price, not launch price.** A $2 first year that renews at $13 is a
  $13 domain.
