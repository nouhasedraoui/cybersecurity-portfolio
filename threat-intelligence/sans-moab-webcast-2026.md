# SANS Webcast — Better Password Attacks with AI
**Speaker:** Joshua Wright  
**Organizer:** SANS Institute  
**Date:** April 15, 2026  
**My Status:** Attended live — certificate of completion received

---

## What This Session Was About

Joshua Wright analyzed the MOAB (Mother Of All Breaches) — a dataset 
containing 3.46 billion leaked credentials from hundreds of breaches 
combined into one file. Using ClickHouse (a high-performance columnar 
database), he queried this data at scale to extract behavioral patterns 
about how real humans choose and reuse passwords — then showed how AI 
(Claude via MCP) can accelerate this kind of threat intelligence work.

---

## Key Concepts Learned

### 1. What is MOAB?
- Mother Of All Breaches — 108GB of compiled credential data
- Aggregates hundreds of previous breaches into one queryable dataset
- Contains usernames, emails, passwords from real leaked databases
- Used here for **defensive threat intelligence research**, not attacks

### 2. Password Reuse — The Real Numbers
From querying the MOAB dataset:
- 23.2 million unique usernames analyzed in the sample
- **870,000 accounts (3.75%)** had the same password leaked from 4+ 
  different websites
- **180,000 accounts (0.8%)** had it leaked from 8+ different sites

This means credential stuffing attacks are highly effective because 
users reuse passwords across many platforms. One breach = access 
to potentially dozens of other accounts.

### 3. What the Data Reveals About Human Password Behavior

| Pattern | What It Means |
|---------|--------------|
| Most common passwords | "123456", "password" still dominate |
| Password length distribution | Most users choose shortest allowed |
| Keyboard-walk patterns | "qwerty", "12345" remain widespread |
| l33t substitution | "p@ssw0rd" is NOT more secure — attackers know this |
| Year/date patterns | "Summer2024!" is predictable and crackable |
| Username in password | Many users include their own email/name |
| Mutation families | "password1" → "password2" is detectable by AI |

### 4. Key Insight — 90-Day Password Rotation Is Harmful
NIST 800-63B now officially recommends **against** forced periodic 
password changes. The MOAB data confirms why: users respond to forced 
rotation with predictable mutations. Security policy should focus on 
**breach detection and length requirements**, not rotation schedules.

### 5. Fortune 20 Companies Are Not Protected
Leaked corporate credentials found in MOAB:

| Company | Leaked Credentials |
|---------|-------------------|
| Alphabet (Google) | 392,354 |
| Microsoft | 122,400 |
| Bank of America | 67,752 |
| JPMorgan Chase | 46,339 |
| Apple | 32,219 |

Conclusion: company size does not equal password hygiene. 
Employees of major corporations use the same weak passwords as everyone else.

### 6. MFA Is Valuable But Not Bulletproof
- **Prompt bombing:** Attacker sends repeated MFA push notifications 
  hoping user approves accidentally
- **MFA bypass vulnerabilities:** Some authentication endpoints have 
  logic flaws that skip MFA entirely
- **Best practice:** FIDO2/passkeys (phishing-resistant) or number-matching 
  push verification

### 7. ClickHouse — Tool Used for Analysis
- Open source, free columnar database
- Designed for analytical queries on billions of rows
- Can be run locally via Docker:
```bash
docker run -d --name clickhouse \
  -p 8123:8123 -p 9000:9000 \
  clickhouse/clickhouse-server
```
- Allows querying billions of credentials in milliseconds

### 8. MCP — Model Context Protocol (New to Me)
This was something I had not encountered before this session.

MCP = a standard protocol that allows AI models (like Claude) to 
connect directly to external tools and data sources.

**Architecture shown:**
Language Model (Claude)
↓
MCP Client (bridge)
↓
MCP Servers (tools: GitHub, Slack, databases, etc.)
Joshua used Claude connected via MCP to his ClickHouse database — 
and asked it to write SQL queries in natural language. Claude generated 
accurate queries against the breach data in real time.

**Why this matters for cybersecurity:** AI-assisted threat intelligence 
analysis will become a standard skill. Analysts who can connect AI to 
security tooling will work significantly faster than those who cannot.

---

## Defensive Recommendations (From the Session)

1. **Monitor breach databases continuously** — subscribe to services 
   like Have I Been Pwned, SpyCloud, or similar CTI feeds to detect 
   when your organization's emails appear in breach data

2. **Move to phishing-resistant MFA** — FIDO2/passkeys are the gold 
   standard. If not yet possible, use number-matching push verification 
   to prevent prompt bombing

3. **Audit authentication endpoints** — test all login pages for 
   MFA-bypass vulnerabilities, especially public-facing ones

4. **Stop 90-day rotation policies** — replace with breach-triggered 
   resets and minimum length requirements (16+ characters)

5. **Leverage breach data for policy improvement** — analyzing how 
   your users actually behave with passwords is more effective than 
   assuming policy compliance

---

## What I Want to Explore Next

- [ ] Set up ClickHouse locally via Docker and practice SQL queries 
      against sample credential datasets
- [ ] Explore MCP integrations — connecting Claude to security tools
- [ ] Research FIDO2/WebAuthn implementation in web applications
- [ ] Read Joshua Wright's upcoming book: **Dynamic Incident Response**
- [ ] Look into SpyCloud and similar CTI breach monitoring services
- [ ] Practice building detection rules for credential stuffing in Wazuh

---

## Personal Reflection

Before this webcast, I had never heard of MOAB. Seeing 3.46 billion 
credentials queried in real time — and realizing that 392,000 Google 
employee passwords are already circulating in breach databases — made 
the abstract concept of credential threats very concrete.

The MCP demonstration was the most unexpected part. Watching an AI 
generate accurate threat intelligence queries in real time shows that 
the future of security analysis is human + AI collaboration, not one 
replacing the other.

---

## Resources

- [Have I Been Pwned](https://haveibeenpwned.com) — breach monitoring
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) 
  — Digital identity guidelines
- [SANS Institute](https://www.sans.org) — webcast source
- [Model Context Protocol](https://modelcontextprotocol.io) — MCP docs
