# Fortinet Certified Fundamentals (FCF) — Study Notes
**Certification:** Fortinet Certified Fundamentals in Cybersecurity  
**Date:** April 19, 2026 | **Valid until:** April 19, 2028  
**Validation:** 5313161142NS  

---

## FCF Structure — Two Exams

| Exam | Course | Audience |
|------|--------|----------|
| NSE 1 | Introduction to the Threat Landscape | Everyone |
| NSE 2 | Technical Introduction to Cybersecurity | Technical roles |

---

## NSE 1 — Introduction to the Threat Landscape

### Chapter 1 — The Bad Actors
Who is behind cyberattacks and what motivates them:

- **Nation-state actors:** Government-sponsored, highly funded, target 
  critical infrastructure and espionage
- **Cybercriminals:** Financially motivated — ransomware, fraud, theft
- **Hacktivists:** Ideologically motivated — DDoS, defacement
- **Script kiddies:** Low-skill attackers using existing tools
- **Insider threats:** Employees — accidental or malicious
- **Cyberterrorists:** Politically motivated disruption

Attack methods attackers use:
- Zero-day exploits: vulnerabilities unknown to the vendor
- Phishing: deceptive emails/messages to steal credentials
- Botnets: networks of compromised machines used for attacks
- Ransomware: encrypts data and demands payment

### Chapter 2 — Data Security Perspectives
How data breaches affect organizations:

- Financial loss (direct + regulatory fines)
- Reputational damage
- Legal consequences (GDPR, HIPAA violations)
- Operational disruption
- The CISO's role: balance security investment vs business risk

### Chapter 3 — Password Perspectives
Why passwords fail and how to protect them:

- Most common attack: credential stuffing using leaked databases
- Weak passwords remain widespread even in large organizations
- Password reuse across multiple sites multiplies breach impact
- Best practices: length over complexity, unique per site, 
  use a password manager, enable MFA

### Chapter 4 — Internet Threat Perspectives
Threats users face when browsing and communicating:

- Malware delivery: drive-by downloads, malicious attachments
- Social engineering: pretexting, baiting, quid pro quo
- Phishing variants: spear phishing (targeted), whaling (executives), 
  smishing (SMS), vishing (voice)
- Man-in-the-Middle: intercepting communications on unsecured networks

### Chapter 5 — Insider Threat Perspectives
Threats that originate from within the organization:

- **Malicious insider:** intentional data theft or sabotage
- **Negligent insider:** accidental exposure — clicking phishing links, 
  misconfiguring systems, losing devices
- **Compromised insider:** legitimate credentials stolen by attacker
- Mitigation: PoLP, user monitoring, DLP, security awareness training

---

## NSE 2 — Technical Introduction to Cybersecurity

### Chapter 1 — Cryptography and PKI

**Symmetric vs Asymmetric cryptography:**
- Symmetric: one shared key for encrypt + decrypt — fast, 
  used for bulk data (AES, 3DES)
- Asymmetric: key pair — public encrypts, private decrypts — 
  slower, used for key exchange + signatures (RSA, ECC)
- In practice: asymmetric exchanges the symmetric session key, 
  then symmetric handles the actual data (hybrid approach)

**Cipher types:**
- Stream cipher: encrypts one bit/byte at a time — RC4
- Block cipher: encrypts fixed-size chunks (128-bit blocks) — AES, DES

**Hashing:**
- One-way, fixed-length output — SHA-256, SHA-3, MD5 (broken)
- Used for: integrity verification, password storage, digital signatures
- Output is always fixed-length because input is always mapped 
  to the same digest space by the algorithm

**Key stretching (for password protection):**
- PBKDF2: applies hash function thousands of times + adds salt
- Bcrypt: adaptive cost — increases computation as hardware improves
- Salt: random value added before hashing — prevents rainbow table attacks

**PKI (Public Key Infrastructure):**
- CA (Certificate Authority): issues and digitally signs certificates
- RA (Registration Authority): verifies identity before CA issues cert
- Digital certificate: binds public key to an identity — contains 
  subject, issuer, validity dates, public key, CA signature
- Chain of trust: Root CA → Intermediate CA → End Entity
- OCSP: real-time certificate revocation status checking
- CRL: list of all revoked certificates
- HSM: tamper-resistant hardware device for storing private keys

### Chapter 2 — Secure Network

**Network perimeter concepts:**
- Trusted zone: internal network
- Untrusted zone: internet/external
- DMZ: semi-trusted zone for public-facing servers
- Defense-in-depth: layered security, not just perimeter

**Filtering at OSI layers:**
- Layer 2: MAC filtering, VLANs, 802.1X port security
- Layer 3: ACLs, IP-based firewall rules
- Layer 4: Port-based filtering, stateful TCP tracking
- Layer 7: DPI, WAF, application-aware NGFW

**5-tuple:** Source IP | Destination IP | Src Port | Dst Port | Protocol  
Used by stateful firewalls to track every connection.

**Firewall types:**
- Stateless (packet filtering): checks each packet independently, 
  no session awareness — simple and fast
- Stateful: tracks connection state — knows if packet belongs 
  to an established session
- UTM: firewall + IPS + antivirus + content filtering combined
- NGFW: adds application awareness, user identity, SSL inspection
- pfSense/OPNsense: open-source stateful firewalls with UTM features

**Network segmentation:**
- VLANs: logical separation at Layer 2 (same switch, different network)
- Subnets + ACLs: isolation at Layer 3
- Bastion host/Jump box: single hardened entry point to sensitive segments
- SD-WAN: software-defined WAN — overlay on physical underlay, 
  application-aware routing
- SASE: combines SD-WAN + cloud-delivered security (SWG, CASB, 
  ZTNA, FWaaS) — secures distributed users accessing cloud resources

**CAM table attacks and switching security:**
- MAC flooding: overwhelm CAM table → switch enters hub mode → 
  all traffic visible to attacker
- Mitigation: sticky MAC, static MAC entries, 802.1X port security

**Sandboxing generations:**
1. First gen: signature-based static analysis
2. Second gen: dynamic — runs code in isolated VM, watches behavior
3. Third gen: full system emulation — detects sandbox-aware malware

**Common network attacks:**
- MITM: intercepts traffic between two parties (ARP/DNS spoofing)
- Replay attack: re-sends captured valid traffic — prevented by nonces
- SYN flood: exhausts server with half-open TCP connections
- Smurf attack: ICMP broadcast amplification with spoofed source IP
- Ping of death: oversized ICMP packet causes buffer overflow
- Teardrop: malformed fragments crash reassembly process
- Christmas tree: all TCP flags set — causes processing overhead

### Chapter 3 — Authentication and Access Control

**Authentication factors:**
- Knowledge: password, PIN, security question
- Possession: hardware token, smart card, OTP device
- Inherence: fingerprint, iris, face recognition
- Behavior: typing rhythm, mouse movement patterns

**OTP types:**
- HOTP: counter-based, valid until used
- TOTP: time-based 30-second window (Google Authenticator)

**SSO (Single Sign-On):**
Authenticate once → token issued → accepted by multiple services  
Reduces password fatigue but creates single point of failure.

**SAML vs OAuth:**
- SAML: XML-based enterprise SSO — authentication + authorization
- OAuth: token-based delegated authorization ("Login with Google")

**Key protocols:**
- RADIUS: centralized authentication for network access
- TACACS+: separates authentication/authorization/accounting (AAA) — 
  more granular than RADIUS, used for admin device access
- LDAP: directory protocol for querying user identity stores
- 802.1X (PNAC): port-based network access control — 
  supplicant → authenticator → auth server

**Access control models:**
- MAC: system enforces access based on labels — military/government
- DAC: owner decides who accesses their resources
- RBAC: access based on job role
- ABAC: access based on attributes (user, resource, environment)
- PoLP: give only minimum permissions required for the job

### Chapter 4 — Secure Remote Access

**VPN types:**
- IPsec VPN: Layer 3, encrypts entire IP packet — tunnel and transport modes
  - Tunnel mode: full packet encrypted (site-to-site)
  - Transport mode: only payload encrypted (host-to-host)
  - AH: provides authentication only
  - ESP: provides authentication + encryption (most common)
  - IKE: handles key exchange negotiation
- SSL VPN: uses TLS, works through browser or lightweight client
  - Portal (web) VPN: browser-only, limited protocols
  - Tunnel VPN: full network access via client
- VPN tunnel concept: data is encapsulated inside another packet — 
  like putting a letter inside another envelope with a different address

**ZTNA (Zero Trust Network Access):**
- Never trust, always verify — every access request authenticated
- Replaces VPN's "inside = trusted" model
- Components: ZTNA client, access proxy, IDaaS, security policy server
- Grants per-application access, not full network access
- Available from multiple vendors — not Fortinet-exclusive

### Chapter 5 — Endpoint Security

**IoT security:**
- Personal IoT: smartwatches, fitness trackers
- Residential IoT: smart TVs, thermostats, cameras
- Industrial IoT (ICS/SCADA): factory sensors, medical devices, PLCs
- Securing IoT: VLAN isolation by device role, device registration, 
  network segmentation

**Endpoint hardening:**
- Firmware: low-level software controlling hardware — 
  firmware attacks are dangerous because they persist below the OS, 
  survive reinstalls, and are invisible to standard antivirus
- UEFI vs BIOS: UEFI restricts boot to signed/approved software — 
  Secure Boot prevents unsigned OS/bootloader from loading
- Full Disk Encryption (FDE): protects data if device is stolen
- TPM: hardware chip storing encryption keys securely
- DLP: prevents sensitive data from leaving the endpoint

**Endpoint protection:**
- EPP (Endpoint Protection Platform): prevents known threats — 
  antivirus, anti-malware, firewall (examples: CrowdStrike, Defender)
- EDR (Endpoint Detection and Response): detects unknown threats 
  using behavioral analysis, IOCs, AI — responds automatically

### Chapter 6 — Secure Data and Applications

**Data classification:**
- PII: Personally Identifiable Information
- PHI: Protected Health Information (HIPAA)
- PCI: Payment Card Industry data
- CUI: Controlled Unclassified Information

**Data lifecycle:** Create → Store → Use → Archive → Destroy  
Each phase requires specific protection controls.

**Email security:**
- SPF: verifies sending server is authorized for the domain
- DKIM: cryptographic signature proving email not tampered
- DMARC: policy defining what to do when SPF/DKIM fail
- SEG (Secure Email Gateway): filters malicious email before delivery
- Bayesian filters: learn spam patterns from historical data
- Spam signals: sender reputation, SPF/DKIM/DMARC results, 
  content analysis, links, IP blacklists, user feedback

**WAF (Web Application Firewall):**
- Protects web apps from: SQLi, XSS, CSRF, file inclusion
- IP reputation: blocks known malicious source IPs
- DPI: inspects payload content, not just headers

### Chapter 7 — Cloud Security and Virtualization

**Cloud service models and responsibility:**
- IaaS: you manage OS up — provider manages physical hardware
- PaaS: you manage application — provider manages runtime + infra
- SaaS: provider manages everything — you manage access and data

**Virtualization risks:**
- VM escape: attacker breaks out of VM to reach hypervisor
- VM sprawl: uncontrolled VM creation — unpatched VMs become risks
- Data remanence: data persists after deletion — 
  mitigated by overwriting, crypto-erasure, degaussing
- Live migration attack: intercepting VM data during host transfer

**Cloud threats:**
- Misconfiguration: #1 cause of cloud breaches — open S3 buckets, 
  public snapshots, over-permissive IAM roles
- API security: APIs must use HTTPS, authentication, rate limiting, 
  API gateway with schema validation

**Cloud security services:**
- CASB: Cloud Access Security Broker — visibility and control 
  over SaaS app usage
- SASE: cloud-delivered security + SD-WAN combined
- SOCaaS / SECaaS: outsourced SOC and security operations

---

## What to Study Next (FCF → FCA path)

- [ ] Fortinet FCA — Fortinet Certified Associate (next level)
- [ ] Deeper practice: pfSense/FortiGate lab setup
- [ ] Apply NSE 2 concepts in TryHackMe SOC and network paths
- [ ] NSE 4 (FCP) — FortiGate Administrator (advanced, requires 
      hands-on FortiGate experience)
