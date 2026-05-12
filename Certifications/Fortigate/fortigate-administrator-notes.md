# FortiGate Administrator — Study Notes
**Course:** Fortinet FortiGate Administrator  
**Certification track:** FCA / FCP — FortiGate Administrator  
**Duration:** 22 hours (12h lecture + 10h labs)  
**Status:** Completed ✓

---

## Official Course Agenda (15 Modules)

| # | Module |
|---|--------|
| 01 | System and Network Settings |
| 02 | Firewall Policies and NAT |
| 03 | Routing |
| 04 | Firewall Authentication |
| 05 | Fortinet Single Sign-On (FSSO) |
| 06 | Certificate Operations |
| 07 | Antivirus |
| 08 | Web Filtering |
| 09 | Intrusion Prevention and Application Control |
| 10 | SSL VPN |
| 11 | IPsec VPN |
| 12 | SD-WAN Configuration and Monitoring |
| 13 | Security Fabric |
| 14 | High Availability |
| 15 | Diagnostics and Troubleshooting |

---

## 01 — System and Network Settings

### FortiGate Overview

**What is FortiGate?**
FortiGate is a Next-Generation Firewall (NGFW) — core product of
the Fortinet security ecosystem.

**FortiGate Platform Structure:**
- FortiOS: the operating system running on all FortiGate devices
- SPUs (Security Processing Units): dedicated hardware chips that
  accelerate security processing without impacting performance
- FortiGuard Subscription Services: cloud threat intelligence feeds
  keeping FortiGate updated with latest signatures

**FortiGate Models:**
- Entry-level: small offices and branches
- Mid-range: medium enterprise environments
- High-end: data centers and large enterprise deployments

**Key Features:**
- Authentication: local and remote user authentication
- VPNs: IPsec and SSL VPN for secure remote access
- Security scanning: antivirus, web filtering, application control
- Monitoring and logging: traffic visibility and audit trails
- Advanced:
  - SD-WAN: software-defined WAN for application-aware routing
  - VDOMs (Virtual Domains): divide one physical FortiGate into
    multiple independent virtual firewalls — each with its own
    policies, interfaces, and routing table
  - Automated stitches: event-driven automation — when a trigger
    occurs (e.g. threat detected) a predefined action fires
    automatically (e.g. block IP, send alert, quarantine host)

### Admin Account Best Practices

The default `admin` account is a known target for attackers.

**Best practices:**
- Create additional administrator accounts — reduces dependence on
  default admin and limits access based on job role
- Admin accounts are NOT the same as regular user accounts

**Creating an admin account:**
```
System > Administrators > Create New (Admin)
→ Account name
→ Account type
→ Admin profile (defines permissions)
→ MFA and password configuration
```

**Admin profile permissions:**
- Read and Write (R/W)
- Read Only
- No Access
- Custom

### FortiGate Interfaces

Each interface configurable with:
- Alias (friendly name)
- IP address and netmask
- Admin access: protocols allowed for management (HTTPS, SSH, PING)
- DHCP server settings

### VLANs

**What is a VLAN?**
Technology that splits one physical LAN into multiple logical LANs.
Each VLAN = a separate broadcast domain.
Traffic is tagged with a VLAN ID to identify which VLAN it belongs to.

**Most popular tagging protocol:** 802.1Q

**VLAN tags:** 4-byte field added to the Ethernet frame containing
the VLAN ID (12-bit value = up to 4094 VLANs possible)

**802.1Q vs 802.1AD:**
- 802.1Q: single VLAN tag — standard enterprise VLAN tagging
- 802.1AD (Q-in-Q): double tag — used by service providers to
  tunnel customer VLANs across provider networks

**VLAN use cases:**
- Isolate network segments for security
- Separate traffic between departments
- Segregate traffic by type: data, voice, IoT, management

**VLAN Modes in FortiGate:**

| Mode | Layer | Description |
|------|-------|-------------|
| NAT mode | Layer 3 | FortiGate routes traffic between VLANs and external networks — most common deployment |
| Transparent mode | Layer 2 | FortiGate acts as a bridge — applies security without routing. SSL VPN, DHCP, NAT not supported. Ideal when network changes must be minimal |
| Virtual VLAN Switch | Layer 2 | Hardware switch ports function as a managed Layer 2 switch — ports assigned to VLANs or configured as trunks. Useful in HA scenarios |

**Creating a VLAN interface:**
```
Network > Interfaces > Create New
→ Type: VLAN
→ Interface: select physical parent interface
→ VLAN ID
→ Name
→ IP/Netmask
→ Admin access protocols
→ DHCP server (if needed)
→ Role: LAN / WAN / DMZ
```

### DHCP Server

FortiGate can run one or more DHCP servers on any interface.

**DHCP server configuration includes:**
- Address range (start IP — end IP)
- Netmask
- Default gateway
- DNS server — required so devices know where to resolve domain
  names. Without DNS, a device with a valid IP still cannot browse
  the internet by hostname

**One shared DHCP vs one per interface:**
- One shared: simpler but requires careful scope management to
  avoid overlapping address ranges across interfaces
- One per interface: cleaner — each subnet has its own dedicated
  scope, easier to manage and troubleshoot individually

### Static Routing

**Static routing:** manually configured routes — basic way to tell
FortiGate where to forward traffic for specific destinations.

**Static route components:**
- Destination: target network address
- Gateway: next-hop IP address
- Interface: which FortiGate interface to use

**Default route:** tells FortiGate where to send traffic when no
specific match exists in the routing table. Points to the ISP
gateway — provides internet access.

**Monitoring routes:**
```
All configured routes:       Network > Static Routes
Active routing table only:   Dashboard > Network > Static and Dynamic Routing
```

The active routing table (dashboard) is the FIRST place to check
when troubleshooting network connectivity issues.

**Reasons a route may not appear in the routing table:**
- Route is misconfigured
- Associated interface is down or disabled
- A better route (lower metric) already exists for that destination

---

## 02 — Firewall Policies and NAT

### Firewall Policy Fundamentals

**Firewall policy matching criteria:**
- Incoming interface
- Outgoing interface
- Source: IP address or user identity
- Destination: IP address or internet service
- Service: destination port
- Schedule: time-based rule activation

**Actions:** Accept or Deny

**Policy table logic:**
Rules are evaluated top to bottom — first match wins.
Order matters: more specific rules must be placed above broader rules.

### Firewall Address Objects

Instead of typing raw IPs in policies, create named address objects:
```
Policy & Objects > Addresses > Create New
→ Name: descriptive label
→ Type: Subnet / IP Range / FQDN / Geography
→ Subnet or IP range value
```

Benefits: reusable across policies, easier to read and audit.

**Default "all" object:** matches any possible IP address —
available for both source and destination.

**Internet Service objects:** pre-built objects from the FortiGuard
Internet Service Database representing known cloud services
(e.g. Google, AWS, YouTube, Microsoft 365).
These are NOT ISPs — they are application-layer service destinations.

### Inspection Modes

| Mode | How it Works | Performance | Coverage |
|------|-------------|-------------|----------|
| Flow-based | Examines traffic as it passes through — no buffering | Faster | Less thorough |
| Proxy-based | Buffers and examines the full data object | Adds latency | More thorough — can inspect more data points |

**Buffering** = temporarily holding data in memory to examine the
complete object (e.g. full file or full email) before allowing it through.

---

## 03 — Routing

### Static Routes
Covered in Module 01 — System and Network Settings.

**Additional routing concepts:**
- FortiGate routing table contains only active routes
- Policy-based routing: route traffic based on source, destination,
  service, or interface — overrides standard routing table decisions
- Equal-cost multi-path (ECMP): multiple routes with same metric —
  FortiGate load-balances across them

---

## 04 — Firewall Authentication

### Why Authenticate Users?

Without authentication, FortiGate can only identify traffic by
source IP address — not by user identity. Authentication links
traffic to specific users for granular policy enforcement and logging.

### Authentication Methods

**Local password authentication:**
- User credentials stored directly on FortiGate
- Includes guest accounts with temporary credentials

**Steps for local authentication:**
```
1. Create a local user
2. Add user to a group
3. Add the user group as source in a firewall policy
4. Verify by testing login success
5. Monitor via authentication logs
```

**Remote password authentication:**
- FortiGate sends credentials to an external authentication server
- Supports LDAP, RADIUS, TACACS+

**Steps for remote authentication:**
```
1. Add the remote server to FortiGate
2. Create a user group linked to remote server
3. Add the user group as source in a firewall policy
4. Verify by testing login success
5. Monitor via authentication logs
```

### LDAP — Bind and DN Explained

When configuring LDAP on FortiGate for remote authentication:

**What is Bind?**
Bind = the process of authenticating to the LDAP server so FortiGate
can query it. FortiGate must present credentials to the LDAP server
before it can search the directory.

**What is the long DN string (uid=..., ou=..., cn=...)?**
DN = Distinguished Name — the full unique address of an object in
the LDAP directory tree.

```
uid=admin,ou=users,dc=company,dc=com
```

Breaking it down:
- `dc=company,dc=com` → the root domain (company.com)
- `ou=users` → Organizational Unit called "users"
- `uid=admin` → the specific user account named "admin"

Think of it like a file path:
`/company.com/users/admin`

The DN tells LDAP exactly where in the directory tree to find
the object you are authenticating as or searching for.

---

## 05 — Fortinet Single Sign-On (FSSO)

FSSO allows FortiGate to identify users based on their Windows
Active Directory login — without requiring them to authenticate
again at the firewall.

**How it works:**
1. User logs into Windows domain with AD credentials
2. FSSO agent on the domain controller detects the login
3. FSSO agent sends username + IP mapping to FortiGate
4. FortiGate now knows which user is at which IP
5. Identity-based firewall policies apply automatically

**Benefit:** seamless authentication — users never see a login prompt
from the firewall.

---

## 06 — Certificate Operations

### SSL/TLS Inspection

**Why inspect SSL?**
HTTPS encrypts web traffic — which is good for privacy but
attackers also use encryption to hide malware and bypass defenses.

**Two types of SSL inspection:**

| Type | How It Works | Used With |
|------|-------------|-----------|
| Certificate inspection | Inspects TLS handshake — verifies server identity without decrypting content | Web filtering only |
| Deep inspection | Decrypts traffic → inspects content → re-encrypts → forwards | All security profiles: antivirus, IPS, app control, DLP |

### SSL Inspection Profiles in FortiGate

FortiGate includes 4 pre-loaded SSL inspection profiles:
- `certificate-inspection` — read-only
- `deep-inspection` — read-only
- `no-inspection` — read-only
- `custom-deep-inspection` — editable (fourth profile)

You can clone any read-only profile to create custom versions.

### Certificate Warning

When FortiGate performs deep inspection, it re-signs traffic using
its own self-signed certificate. Users may see browser warnings.

**To prevent certificate warnings:**
- Download the Fortinet CA certificate: `Fortinet_CA_SSL`
- Install it on workstations as a Trusted Root Authority

**OR:**
- Use a CA-issued SSL certificate where:
  - Basic Constraints field = `CA: True`
  - Key Usage field = `keyCertSign`

### Why is SSL Inspection Required for Antivirus and IPS?

Both antivirus and IPS need to see the actual content of the traffic
to detect threats. If traffic is encrypted and not decrypted first,
FortiGate sees only ciphertext — no signatures can match against
unreadable data. SSL inspection decrypts the traffic so that
antivirus and IPS engines can inspect the real payload, then
re-encrypts it before forwarding. Without SSL inspection, HTTPS
traffic is a blind spot for all content-based security profiles.

---

## 07 — Antivirus

### Malware Risk

Malware is software designed to damage, disrupt, or gain
unauthorized access to systems. Attackers use it for:
- Data theft and exfiltration
- Ransomware (encrypt data, demand payment)
- Botnet recruitment
- Persistent backdoor access
- Credential harvesting

### FortiGate Scanning Engines

FortiGate Labs provides a continuously updated signature database.

| Scan Type | What It Detects |
|-----------|----------------|
| Antivirus scan | Known malware — matches signatures in FortiGuard database |
| Grayware scan | Unsolicited software installed without user knowledge or consent (adware, spyware, toolbars) — not always malicious but unwanted |
| ML/AI scan | Zero-day and unknown threats using behavioral probability models — may increase false positives because it uses probabilities, not exact signatures |

### Configuring Antivirus Protection

```
1. Create an antivirus profile
   Security Profiles > AntiVirus > Create New
   → Define action for detected infections (block, quarantine, log)

2. Apply the profile to a firewall policy
   Edit Firewall Policy > Security Profiles > Enable AntiVirus
   → Select the profile

3. Verify configuration
   → Test using EICAR test file from eicar.com
   → EICAR is a safe, standard test file that triggers AV detection
     without being actual malware

4. Monitor
   → Check antivirus logs for detections
```

---

## 08 — Web Filtering

### Why Use Web Filtering?

- Preserve employee productivity
- Prevent network congestion from bandwidth-heavy sites
- Decrease exposure to web-based threats
- Limit legal liability
- Prevent access to inappropriate content

### FortiGuard Category Filters

FortiGate works with FortiGuard to categorize websites.
Instead of blocking individual URLs, you block entire categories.

**Main FortiGuard category groups:**
- Security risk (malware sites, phishing, spam URLs)
- General interest (social media, news, entertainment)
- Bandwidth consuming (streaming video, P2P, file sharing)
- Adult/mature content
- Local categories (custom — defined by administrator)

Each category contains websites rated based on their dominant content.

**Example:** Twitter/X is rated under General Interest — Social Networking.

Full category list: fortiguard.com/webfilters/categories

**Difference between website and web page:**
- Website: the entire domain (e.g. youtube.com)
- Web page: a single URL within a domain
  (e.g. youtube.com/watch?v=abc123)
FortiGuard categorizes at the domain level in most cases.

### FortiGuard Category Actions

| Action | What Happens |
|--------|-------------|
| Allow | Traffic is permitted without restriction |
| Block | Access is denied — user sees block page |
| Monitor | Traffic is permitted but logged |
| Warning | User sees a warning page and can choose to proceed |
| Authenticate | User must authenticate before accessing the site |

### Configuring Web Filtering

```
1. Validate FortiGuard security subscription licence
   → Confirm FortiGuard web filtering service is active

2. Identify how FortiGuard has categorized the target website
   → Test at fortiguard.com/webfilter

3. Configure a web filtering security profile
   Security Profiles > Web Filter > Create New
   → Set actions per category

4. Apply the profile to a firewall policy
   → Enable Security Profiles > Web Filter in the policy
   → Enable logging

5. Test
   → Try accessing a blocked category
   → Verify block page appears
   → Check web filter logs
```

---

## 09 — Intrusion Prevention and Application Control

### IPS (Intrusion Prevention System)

IPS analyses traffic to identify and block malicious threats before
they reach their target.

**FortiGate IPS detection techniques:**

| Technique | How It Works |
|-----------|-------------|
| Protocol Decoders | Identify traffic that does not conform to protocol standards — FortiGate detects the protocol regardless of port number, then applies only relevant signatures |
| Signatures | Compare network traffic against a database of known attack patterns — daily updates from FortiGuard |

**IPS Sensor Actions:**

| Action | Behavior |
|--------|---------|
| Default | Use the action defined in the signature itself |
| Allow | Permit the traffic |
| Monitor | Allow and log |
| Block | Drop the traffic |
| Reset | Drop and send TCP reset to both sides |
| Quarantine | Block the source IP for a defined period |

**Configuring FortiGate IPS:**
```
1. Select or create an IPS sensor
   Security Profiles > Intrusion Prevention > Create New

2. Select signatures and filters
   → Choose which signatures to include
   → Enable botnet C&C blocking if needed
   → Enable malicious URL blocking if needed

3. Apply IPS sensor to a firewall policy
   Edit Firewall Policy > Security Profiles > Enable IPS

4. Review IPS logs regularly
```

**IPS best practices:**
- Keep the FortiGuard signature database up to date
- Use provided IPS sensor templates as a starting point for custom sensors
- Clone a default sensor — never modify the originals directly
- Apply IPS to both inbound AND outbound traffic
- Ensure SSL inspection is enabled so IPS can examine encrypted traffic
- Periodically tune sensors to reduce false positives

### Application Control

Application control identifies and controls network traffic by
application — not just by port or protocol.

**Why application control is needed:**
- Traditional firewalls filter by port/protocol
- Modern apps use dynamic ports and evasive techniques
  (e.g. BitTorrent — a peer-to-peer file sharing protocol
  that uses dynamic ports and can disguise itself as HTTP traffic)
- Peer-to-peer apps bypass traditional port-based filtering

**How it works:**
- FortiGuard Labs provides application signature database
- Traffic analysis performed through the IPS engine
- Inspection done on the full byte stream — independent of
  port or protocol number — using flow-based inspection

**Application control categories:** each can be set to:
- Allow
- Monitor
- Block
- Quarantine

**Override option:** allows a child signature to override its parent
category setting. Example: block all Social Media category, but
override LinkedIn specifically to Allow — for business use.

**Configuring application control:**
```
1. Create or modify an application control profile
   Security Profiles > Application Control

2. Set actions per app category
   → Or configure overrides for specific apps

3. Add the profile to a firewall policy

4. Verify and monitor
   → Check application control logs
```

---

## 10 — SSL VPN

### What is SSL VPN?

SSL VPN uses TLS/SSL encryption to create a secure connection
between a remote client and the FortiGate acting as VPN server.
By default uses port 443 — typically not blocked by intermediate firewalls.

### SSL VPN Modes

**Web Mode (Portal VPN):**
- Access through a web browser only — no client software required
- Administrators provide granular access to specific resources
- Supports limited protocols: bookmarked URLs, FTP, RDP, etc.

**Tunnel Mode:**
- Full network access — user appears as if physically on the network
- Requires FortiClient VPN installed on the remote device
- Supports all resource types but creates extra overhead for support

### SSL VPN Benefits

- Uses common port 443 — usually passes through firewalls
- Flexible — web browser or full client depending on need
- Granular access control per user or group
- Client integrity check for Windows: verifies antivirus and firewall
  are installed before granting access
- No additional license required for SSL VPN on FortiGate

### Configuring SSL VPN

```
1. Create users and groups authorized to connect

2. Review, edit, or create SSL VPN portals
   VPN > SSL-VPN Portals

3. Configure SSL VPN settings
   VPN > SSL-VPN Settings
   → Listening interface and port
   → Certificate
   → Tunnel IP range for clients

4. Create a firewall policy to allow VPN traffic
   → Source: SSL-VPN tunnel interface
   → Destination: internal network
   → Action: Accept
```

### SSL VPN Best Practices

- Disable unused SSL VPN mode in portals (web or tunnel — not both if not needed)
- Use remote authentication servers — avoid local users in large environments
- Replace default self-signed certificate with a trusted CA certificate
- Apply principle of least privilege in VPN firewall policies
- Enable client integrity check for Windows endpoints
- Restrict connections to specific known public IPs where possible

---

## 11 — IPsec VPN

### What is IPsec VPN?

IPsec is a suite of industry-standard protocols that creates secure
connections between devices in different geographic locations.

**IPsec can provide:**
- Data authentication (verifies sender identity)
- Data integrity (detects tampering)
- Data confidentiality (encryption)
- Anti-replay protection

**Key advantage over other VPN types:**
No service provider intervention needed — only IP reachability
between the two tunnel endpoints is required.

### IPsec VPN Types

**Remote access VPN:**
- Client device connects to a remote network
- Client always initiates the connection

**Site-to-site VPN:**
- Connects two networks in different physical locations
- Topologies: Hub and Spoke, Partial Mesh, Full Mesh
- FortiGate can connect with other FortiGate devices AND
  with devices from other vendors

### IKE Protocol — Two Versions

IKE (Internet Key Exchange) creates IPsec tunnels dynamically.

**IKEv1 — Two Phase Process:**

Phase 1:
- Two peers authenticate each other
- Establish a secure channel for Phase 2 negotiation
- Parameters that must match: IKE Mode (Main or Aggressive),
  Authentication method, Encryption Algorithm, Hashing Algorithm,
  Diffie-Hellman Group

Phase 2:
- Determine which traffic is protected
- Create the data sub-tunnel inside the Phase 1 tunnel
- Parameters that must match: Encryption Algorithm, Hashing
  Algorithm, DH Group (only if PFS is used — highly recommended)
- Traffic protected by listing local and remote subnets:
  - Remote access: both subnets configured on server side
  - Site-to-site: subnets on each peer must mirror each other

**IKEv2 — Improvements over IKEv1:**
- No two-phase process — more efficient negotiation
- Reduced latency — fewer messages exchanged
- Better reliability — sequence numbers and acknowledgements
- Supports EAP (Extensible Authentication Protocol)
- Supports asymmetric authentication — peers can use different methods
- Stronger algorithms: PRF-SHA hashing, AES-GCM encryption
- Better resilience against DoS attacks
- Incompatible with IKEv1

### ESP (Encapsulating Security Payload)

Supported by FortiGate — provides encryption + authentication.

**Encryption algorithms:**
| Algorithm | Status |
|-----------|--------|
| DES | Weak — not recommended |
| 3DES | Slow, short key — not best option |
| AES | Current standard — available in 128/192/256-bit. Considered very secure |

**Data integrity and authentication algorithms:**
| Algorithm | Status |
|-----------|--------|
| MD5 | Legacy — no longer recommended |
| SHA-1 | Known vulnerabilities — no longer recommended |
| SHA-2 | Secure — available in multiple bit lengths. Higher = more secure |

### VPN Configuration Best Practices

- Keep FortiGate firmware updated with latest patches
- Ensure required ports are open in all firewalls in the traffic path
- Select the correct IKE mode when using IKEv1 (Main vs Aggressive)
- Verify both peers support the same IPsec features before deployment
- Use encryption and hashing levels that meet security requirements

---

## 12 — SD-WAN Configuration and Monitoring

### What is SD-WAN?

Software-Defined WAN — manages multiple WAN links intelligently
based on application requirements rather than just routing tables.

**FortiGate SD-WAN features:**
- Load balance traffic across multiple WAN connections
- Route specific applications over preferred links
- Monitor link health and automatically failover
- Provides performance metrics per interface and per application

---

## 13 — Security Fabric

### What is Fortinet Security Fabric?

A unified security architecture that connects multiple Fortinet
products into a single coordinated ecosystem with centralized
visibility and automated response.

### Benefits

- Unified view of entire network from a single console
  (logical and physical topology showing all devices,
  interconnections, security details, and interfaces)
- Object synchronization across devices
- Security rating: assess and score security posture
- Integration with third-party tools
- Automatic detection of end devices
- Centralized management
- Automation without administrator intervention

**Automation example workflow:**
```
1. Malicious site detected → FortiClient sends log to FortiAnalyzer
2. FortiAnalyzer discovers IOC → notifies FortiGate
3. FortiGate instructs EMS to quarantine the infected computer
4. EMS sends quarantine message to the endpoint
5. Endpoint quarantines itself → notifies FortiGate and EMS
6. FortiGate sends notification to Microsoft Teams channel
```

### Minimum Requirements

- Two FortiGate firewalls running in NAT mode
- One FortiAnalyzer or a cloud logging solution

### Configuring Security Fabric

```
1. Configure a centralized logging platform (FortiAnalyzer)

2. On the root FortiGate:
   → Enable Security Fabric on required interfaces
   → Configure Security Fabric connector: Serve as Fabric Root
   → Configure log forwarding to logging platform
   → Optionally pre-authorize downstream devices

3. On downstream devices:
   → Enable Security Fabric on required interfaces
   → Configure connector: Join Existing Fabric
   → Set the root FortiGate IP address

4. On root FortiGate:
   → Authorize all downstream devices
```

---

## 14 — High Availability

### What is HA?

High Availability (HA) = a cluster of FortiGate devices working
together to eliminate single points of failure.

### Why Use HA?

- Redundancy: maintains continuity during outages and upgrades
- Configuration synchronization: config data synced across all members
- Session synchronization: active connections survive failover
- Simplified management: changes made on primary sync to all members

### How HA Works

**Layer 1 — Cluster Election:**
The cluster elects one device as primary using these criteria in order:

Active-Passive mode priority order:
1. Fewest failed monitored interfaces
2. Highest HA uptime
3. Highest Priority value
4. Highest Serial Number

Active-Active mode priority order:
1. Fewest failed monitored interfaces
2. Highest Priority value
3. Highest HA uptime
4. Highest Serial Number

### HA Protocol — FGCP

FortiGate Clustering Protocol (FGCP):
- Discovers cluster members
- Elects the primary FortiGate
- Synchronizes data among members
- Monitors member health
- Assigns virtual MAC addresses to primary unit interfaces
- Synchronizes TCP sessions (must be enabled manually)

### What is Synchronized vs Not Synchronized?

**Synchronized:**
- Cluster configuration settings (with exceptions listed below)
- FIB (Forwarding Information Base) entries
- DHCP leases
- ARP table
- FortiGuard definitions
- IPsec tunnel SAs
- Active session information (if enabled)

**NOT synchronized:**
- Dashboard widgets
- HA override configuration
- HA device priority value
- HA management interface settings
- In-band HA management interface
- All licenses (except FortiToken)
- Cache (web filtering, email filtering, web cache)

### HA Modes

**Active-Passive (AP):**
- Only the primary device processes traffic
- Secondary devices are on standby
- Simpler — one device handles all traffic

**Active-Active (AA):**
- All devices in the cluster process traffic
- Primary distributes sessions to secondary devices
- Higher throughput — all hardware utilized

### HA Requirements

All cluster members must have the same:
- Model
- Firmware version
- Licensing (cluster uses lowest-level license if different)
- Hard drive configuration
- Operating mode (NAT or transparent)

During cluster creation these parameters must match:
- HA group ID
- Group name
- Password
- Heartbeat interface settings

### HA Best Practices

- Configure at least two dedicated heartbeat interfaces for redundancy
- Use dual back-to-back connections between HA units (recommended)
- Connect each HA unit to the same switches using identical ports
- All cluster members must run the same model and firmware version
- Never make manual changes on secondary units — always configure
  from the primary only to avoid mismatches
- Enable link monitoring on WAN and LAN interfaces to detect failures
- Test failover periodically to verify the cluster works as expected

---

## 15 — Diagnostics and Troubleshooting

### Key Troubleshooting Resources

**Routing issues:**
```
Dashboard > Network > Static and Dynamic Routing
→ Check if route is active in the routing table
→ If route configured but missing: check interface status,
  check for conflicting better routes, verify gateway IP
```

**Authentication issues:**
```
Log & Report > Security Events > User
→ View authentication success and failure events
→ Check which auth method was used
```

**General flow debug (CLI):**
```
diagnose debug flow filter addr <IP>
diagnose debug flow show iprope 1
diagnose debug flow show function-name 1
diagnose debug enable
→ Trace how FortiGate processes specific traffic
→ See which policy matched, what action was taken
```

**Checking FortiGuard connectivity:**
```
diagnose debug rating
→ Verify FortiGuard subscription status and connectivity
```

---

## Additional Module — FortiLink

### What is FortiLink?

FortiLink is a proprietary Fortinet protocol that allows FortiGate
to manage FortiSwitches directly through the FortiGate GUI —
without requiring an additional license.

### Why Use FortiLink?

- Centralized management of FortiSwitches from FortiGate GUI or CLI
- Scalability: supports stacking, clustering — any network size
- Simplified deployment: FortiSwitches auto-discovered and authorized
- Enhanced security: VLANs and policies applied consistently from
  a single management point

### How FortiLink Works

FortiGate uses several protocols to control FortiSwitch:

| Protocol | Role |
|----------|------|
| FortiLink | Default discovery method + heartbeats between FortiGate and FortiSwitch |
| LLDP (Link Layer Discovery Protocol) | Alternative discovery method — automatically enables trunk links in a stack |
| CAPWAP | Switch authentication, authorization, heartbeats, legacy firmware upgrade |
| HTTPS | Default protocol for firmware image delivery during upgrades |
| REST API | Configuration and management API |
| DHCP, DNS, NTP, SSH | Supporting protocols |

### FortiLink Topologies

| Topology | Description |
|----------|-------------|
| Single FortiGate + switch stack | Lead switch directly connected to FortiGate — others daisy-chained or ring |
| HA FortiGate + switch stack | Both HA FortiGate units connect to first switch in stack |
| FortiLink over Layer 3 | FortiSwitch islands across routed networks not directly connected to FortiGate |
| Standalone FortiGate + dual-homed FortiSwitch access | Two tiers of switches for high port density |

### FortiLink Best Practices

- Enable link aggregation between FortiGate and FortiSwitches for
  redundancy and increased throughput
- Keep FortiGate and FortiSwitch firmware versions consistent
- Plan VLANs and port assignments before deployment to minimize
  reconfiguration later
- Monitor switch status and logs regularly to detect issues early

---

*FortiGate Administrator Notes — based on official 15-module course*
