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
