# Network Protocols Reference — Security Engineer & Pentester Edition

> Personal reference for protocols, their function, ports, and attack vectors.
> Organized by attack surface category.

---

## Quick Index

- [Authentication & Access Control](#authentication--access-control)
- [File Sharing & Transfer](#file-sharing--transfer)
- [Email Protocols](#email-protocols)
- [Web Protocols](#web-protocols)
- [Routing Protocols](#routing-protocols)
- [Layer 2 / Switching](#layer-2--switching)
- [VPN & Tunneling](#vpn--tunneling)
- [Wireless Security](#wireless-security)
- [Industrial & Management](#industrial--management)
- [Voice & Multimedia](#voice--multimedia)
- [Encryption & Key Exchange](#encryption--key-exchange)
- [Miscellaneous / Web Dev](#miscellaneous--web-dev)
- [OSI Quick Reference](#osk-quick-reference)
- [Reserved IP Ranges](#reserved-ip-ranges)
- [MAC Address Cheat Sheet](#mac-address-cheat-sheet)

---

## Authentication & Access Control

### SSH — Secure Shell
| Field | Value |
|---|---|
| Port | 22 TCP |
| Layer | L7 Application |
| Purpose | Encrypted remote terminal and command execution |

**How it works:** Client and server perform a key exchange (Diffie-Hellman), authenticate (password or public key), and establish an encrypted channel. Everything inside is encrypted — commands, output, file transfers (SCP/SFTP).

**Attack vectors:**
- Default or weak credentials → brute force with `hydra` or `medusa`
- Old versions → check CVEs (e.g. CVE-2023-38408 OpenSSH agent vulnerability)
- Private key theft → if you find `~/.ssh/id_rsa` during post-exploitation, you can impersonate that user anywhere they have a trusted public key
- SSH tunneling abuse → attacker uses SSH as a tunnel to reach internal hosts (legitimate feature used maliciously)

**Pentest commands:**
```bash
nmap -sV -p 22 target          # grab banner and version
hydra -l root -P wordlist.txt ssh://target
ssh -i stolen_key user@target
```

---

### EAP — Extensible Authentication Protocol
| Field | Value |
|---|---|
| Port | N/A (framework, not standalone) |
| Layer | L2 Data Link |
| Purpose | Authentication framework used in 802.1X and WPA Enterprise |

**How it works:** EAP is a container/framework for many authentication methods. The actual method is negotiated between client and authenticator. Used in 802.1X port-based network access control and WPA Enterprise WiFi.

**Methods — from weakest to strongest:**
- EAP-MD5 → no server certificate, vulnerable to MITM and offline dictionary attack
- LEAP → Cisco proprietary, completely broken, offline crackable
- PEAP → wraps inner auth in TLS tunnel, requires server certificate
- EAP-TLS → mutual certificate auth, strongest, hardest to attack

**Attack vectors:**
- LEAP → capture challenge/response → crack offline with `asleap`
- PEAP misconfiguration → if client doesn't validate server cert → MITM with fake RADIUS server (`hostapd-wpe`, `eaphammer`)
- EAP downgrade → force client to negotiate weaker EAP method

---

### LEAP — Lightweight EAP
| Field | Value |
|---|---|
| Port | N/A (over 802.1X) |
| Layer | L2 |
| Purpose | Cisco proprietary WiFi authentication (deprecated, broken) |

**Attack vectors:**
- MS-CHAPv2 challenge/response is crackable offline
- Tool: `asleap` — captures LEAP exchange and cracks it
- If you see a Cisco WPA Enterprise network, always probe for LEAP support

---

### PEAP — Protected EAP
| Field | Value |
|---|---|
| Port | N/A |
| Layer | L2 |
| Purpose | Secure EAP wrapper using TLS tunnel |

**Attack vectors:**
- If client does not validate server certificate → set up rogue RADIUS server → capture NTLMv2 hash → crack offline
- Tools: `hostapd-wpe`, `eaphammer`
- Key check: does the client prompt the user about certificate errors? If ignored → vulnerable

---

### TACACS — Terminal Access Controller Access-Control System
| Field | Value |
|---|---|
| Port | 49 TCP |
| Layer | L7 |
| Purpose | Centralized AAA (Authentication, Authorization, Accounting) for network devices |

**How it works:** Network devices (routers, switches) offload admin authentication to a central TACACS server. Admin logs into a Cisco router → router asks TACACS server "is this user valid?" → server responds with yes/no and what commands this user is allowed to run.

**Attack vectors:**
- Compromise the TACACS server → you have credentials for every managed network device
- TACACS+ encrypts the body but the header is plaintext — version fingerprinting possible
- Weak shared secret between device and TACACS server → brute force
- Without TACACS: check for devices still using local `enable` passwords

---

### RSH — Remote Shell
| Field | Value |
|---|---|
| Port | 514 TCP |
| Layer | L7 |
| Purpose | Remote command execution on Unix (legacy, pre-SSH) |

**How it works:** Authentication based entirely on IP address + username trust via `.rhosts` files. No encryption. If the `.rhosts` file on the target trusts your IP, you get a shell with no password.

**Attack vectors:**
- Find `.rhosts` or `/etc/hosts.equiv` → direct unauthenticated shell
- IP spoofing to impersonate trusted host (historic attack)
- Immediate critical finding if RSH port 514 is open — should not exist in modern networks

```bash
nmap -p 514 target
rsh target command
```

---

## File Sharing & Transfer

### FTP — File Transfer Protocol
| Field | Value |
|---|---|
| Port | 21 TCP (control), 20 TCP (data) |
| Layer | L7 |
| Purpose | File transfer between systems |

**How it works:** Two channels — control channel (commands) and data channel (actual file transfer). Credentials and data both sent in plaintext. Active mode: server initiates data connection back to client. Passive mode: client initiates both connections (used through firewalls/NAT).

**Attack vectors:**
- Anonymous FTP login → `ftp target` with username `anonymous` → often misconfigured with sensitive files exposed
- Plaintext credentials → capture with Wireshark on the network
- Brute force with `hydra`
- FTP bounce attack → use FTP server to port scan third-party hosts (FTP `PORT` command abuse)
- Writable FTP directory → upload webshell if FTP root overlaps with web root

```bash
nmap -sV -p 21 target
ftp target                           # try anonymous
hydra -l admin -P wordlist ftp://target
nmap -b anonymous@target target2     # FTP bounce scan
```

---

### SMB — Server Message Block
| Field | Value |
|---|---|
| Port | 445 TCP (direct), 139 TCP (over NetBIOS) |
| Layer | L7 |
| Purpose | Windows file sharing, printer sharing, IPC |

**How it works:** Windows machines share files, printers, and named pipes over SMB. Also used for inter-process communication (IPC$) which is how many Windows services talk to each other remotely.

**Attack vectors:**
- EternalBlue (MS17-010) → unauthenticated RCE on unpatched Windows → `exploit/windows/smb/ms17_010_eternalblue`
- Null session → `smbclient -N -L //target` → enumerate shares without credentials
- Pass-the-hash → capture NTLM hash → replay it without cracking → `pth-smbclient`, CrackMapExec
- SMB relay → capture NTLMv2 challenge from victim → relay it to another server in real time → `responder` + `ntlmrelayx`
- Brute force → `crackmapexec smb target -u users.txt -p passwords.txt`
- Sensitive files in open shares → `smbmap -H target`

```bash
nmap -p 445 --script smb-vuln* target
smbclient -N -L //target
smbmap -H target
crackmapexec smb target -u admin -p password
```

---

### NFS — Network File System
| Field | Value |
|---|---|
| Port | 2049 TCP/UDP |
| Layer | L7 |
| Purpose | File sharing for Unix/Linux systems |

**How it works:** NFS server exports directories. Clients mount them over the network. Access control based on IP address and UID/GID matching.

**Attack vectors:**
- `no_root_squash` misconfiguration → when set, remote root user is treated as local root → upload SUID binary → local privilege escalation
- World-readable exports → `showmount -e target` → mount and read all files
- UID matching → create a local user with same UID as a target file owner → access their files

```bash
showmount -e target
mount -t nfs target:/share /mnt/nfs
# if no_root_squash: cp /bin/bash /mnt/nfs/bash; chmod +s /mnt/nfs/bash
```

---

## Email Protocols

### SMTP — Simple Mail Transfer Protocol
| Field | Value |
|---|---|
| Port | 25 TCP (server-to-server), 587 TCP (submission), 465 TCP (SMTPS) |
| Layer | L7 |
| Purpose | Sending and relaying email |

**How it works:** Client connects to SMTP server, announces sender (`MAIL FROM`), recipient (`RCPT TO`), and sends message body (`DATA`). No authentication required in the original design.

**Attack vectors:**
- User enumeration → `VRFY username` and `EXPN list` commands reveal valid users on the server
- Open relay → server forwards email for any sender to any recipient → use for phishing from trusted domain
- Plaintext on port 25 → capture credentials with Wireshark
- `RCPT TO` enumeration → send to multiple addresses, valid ones return 250, invalid return 550

```bash
nmap -p 25 --script smtp-enum-users target
telnet target 25
VRFY admin
EXPN administrators
# Test open relay:
MAIL FROM: attacker@evil.com
RCPT TO: victim@external.com
```

---

## Web Protocols

### HTTP — Hypertext Transfer Protocol
| Field | Value |
|---|---|
| Port | 80 TCP |
| Layer | L7 |
| Purpose | Web traffic, client-server data exchange |

**How it works:** Request-response protocol. Client sends HTTP request (verb + path + headers + optional body). Server responds (status code + headers + body). Stateless — no built-in session tracking, that's handled by cookies.

**Attack vectors:** The largest attack surface in existence.
- SQL Injection (SQLi) → malicious SQL in parameters
- Cross-Site Scripting (XSS) → inject JavaScript into pages
- SSRF → trick server into making requests to internal hosts
- XXE → XML external entity injection
- IDOR → change an ID in a URL to access other users' data
- Command injection → OS commands in input fields
- Path traversal → `../../etc/passwd` in file parameters
- CRLF injection → `\r\n` in headers → response splitting
- AJAX endpoints → often undocumented, less tested → same vulns

**CRLF Injection specifically:**
CRLF = `\r\n` = hex `0D 0A`. HTTP headers end with CRLF, header section ends with double CRLF. If user input containing `\r\n` is reflected in a response header → attacker can inject new headers, set cookies, split responses.

```
GET /page?next=value%0d%0aSet-Cookie:session=attacker HTTP/1.1
```

---

### HTTPS = HTTP + TLS
Same attack surface as HTTP but traffic is encrypted. Additional attack surface: TLS itself (BEAST, POODLE, HEARTBLEED for old versions), certificate validation errors, SSL stripping (downgrade HTTPS to HTTP).

---

### URI vs URL
- **URI** (Uniform Resource Identifier) → any string identifying a resource. Broad concept.
- **URL** (Uniform Resource Locator) → a URI that also specifies how to access the resource (scheme://host/path?query#fragment)
- All URLs are URIs. Not all URIs are URLs.
- Pentest relevance: understand every part of a URL — scheme, host, port, path, query parameters, fragment. Each is a potential injection point.

---

### AJAX — Asynchronous JavaScript and XML
Not a protocol — a technique. Web pages use JavaScript to make HTTP requests in the background without page reloads.

**Pentest relevance:**
- AJAX endpoints are API calls, often undocumented
- Watch browser Network tab or Burp Suite proxy history for XHR/fetch requests
- Often bypass WAF rules tuned for regular page requests
- Frequently have IDOR, auth bypass, SQLi — same vulns as regular endpoints, less tested

---

### ISAPI — Internet Server Application Programming Interface
Microsoft IIS web server extension API. Old technology.

**Attack vectors:**
- Legacy IIS servers with old ISAPI extensions → check CVE databases
- Buffer overflows in ISAPI DLLs (historically common)

---

## Routing Protocols

### RIP — Routing Information Protocol
| Field | Value |
|---|---|
| Port | 520 UDP |
| Layer | L3 Network |
| Purpose | Distance-vector interior routing (legacy) |

**How it works:** Routers broadcast their full routing table every 30 seconds. Metric = hop count (max 15). Slow convergence. RIPv1 no auth. RIPv2 has optional MD5 auth.

**Attack vectors:**
- RIPv1 → inject fake routes by sending spoofed RIP response packets → redirect traffic
- RIPv2 with no auth → same attack
- Max 15 hops → route poisoning by advertising a destination as 16 hops away = unreachable

---

### OSPF — Open Shortest Path First
| Field | Value |
|---|---|
| Port | IP protocol 89 (not TCP/UDP) |
| Layer | L3 |
| Purpose | Link-state interior gateway protocol for enterprise networks |

**How it works:** Routers share Link State Advertisements (LSAs) describing their direct connections. Every router builds a complete topology map and runs Dijkstra's algorithm. Faster convergence than RIP. Scales better.

**Attack vectors:**
- No auth configured (common) → inject fake LSAs → manipulate routing table → redirect traffic through attacker
- OSPF neighbor spoofing → become a fake router in the OSPF domain
- Traffic analysis → OSPF packets reveal internal network topology

---

### EIGRP — Enhanced Interior Gateway Routing Protocol
| Field | Value |
|---|---|
| Port | IP protocol 88 |
| Layer | L3 |
| Purpose | Cisco proprietary advanced distance-vector routing |

**Attack vectors:**
- Same as OSPF if authentication not configured
- EIGRP uses multicast `224.0.0.10` — listen for EIGRP hello packets to confirm Cisco infrastructure and learn topology

---

### IGRP — Interior Gateway Routing Protocol
Older Cisco proprietary routing protocol. Replaced by EIGRP. Finding it means very legacy infrastructure. No authentication.

---

### CDP — Cisco Discovery Protocol
| Field | Value |
|---|---|
| Port | Multicast `01:00:0C:CC:CC:CC` (L2 only, not routed) |
| Layer | L2 |
| Purpose | Cisco device discovery and topology mapping |

**How it works:** Cisco devices broadcast CDP frames every 60 seconds advertising: device hostname, model, IOS version, IP address, connected interface, capabilities.

**Attack vectors:**
- Completely passive — just listen with Wireshark, filter `cdp`
- Reveals: exact device model, IOS version → look up CVEs immediately
- Reveals: IP addresses of all Cisco devices → build network map
- CDP flooding → send many fake CDP announcements → exhaust device memory
- CDP is enabled by default on all Cisco interfaces — most admins never disable it

```bash
# Wireshark: filter "cdp"
# tshark:
tshark -i eth0 -Y cdp
```

---

## Layer 2 / Switching

### STP — Spanning Tree Protocol
| Field | Value |
|---|---|
| Port | Multicast `01:80:C2:00:00:00` (L2 only) |
| Layer | L2 |
| Purpose | Prevent loops in switched networks by blocking redundant paths |

**How it works:** Switches elect a Root Bridge (lowest Bridge ID = priority + MAC). All other switches calculate shortest path to root and block redundant links. If root fails, election happens again.

**Attack vectors:**
- Claim root bridge by sending STP BPDUs with priority 0 → all switches re-converge toward you → all traffic passes through your machine → MITM + network disruption
- STP topology change → cause network disruption by repeatedly triggering reconvergence
- Tool: `yersinia -G` (graphical) or `yersinia -attack stp` in CLI

---

### VLAN — Virtual Local Area Network
| Field | Value |
|---|---|
| Standard | IEEE 802.1Q |
| Layer | L2 |
| Purpose | Logical network segmentation on a single physical switch |

**How it works:** Frames are tagged with a VLAN ID (1-4094). Switches only forward frames to ports in the same VLAN. Separates broadcast domains logically without physical separation.

**Attack vectors:**
- VLAN hopping — double tagging: send a frame with two 802.1Q tags. First switch pops outer tag (your VLAN), second switch sees inner tag (victim VLAN) → you reach a VLAN you shouldn't have access to. Only works toward the native VLAN on a trunk link.
- Requires your port to be on the native VLAN — check before attempting

---

### VTP — VLAN Trunking Protocol
| Field | Value |
|---|---|
| Port | L2 (over trunk links) |
| Layer | L2 |
| Purpose | Sync VLAN database across all switches in a domain |

**How it works:** Switches share a VTP domain name and revision number. Higher revision number = authoritative. All switches adopt the VLAN config from the highest revision number device.

**Attack vectors:**
- Connect a rogue switch with a higher VTP revision number and an empty VLAN database → all switches in the domain adopt the empty config → every VLAN disappears → complete network outage
- This attack is catastrophic and irreversible without manual reconfiguration
- Defense: set all switches to VTP transparent or server mode with a password, or disable VTP entirely

---

### HSRP — Hot Standby Router Protocol
| Field | Value |
|---|---|
| Port | UDP 1985, multicast 224.0.0.2 |
| Layer | L3 (managed at L2 via multicast) |
| Purpose | Cisco router redundancy — virtual gateway IP shared between routers |

**Attack vectors:**
- No auth by default → send HSRP Hello with priority 255 → claim active router role → all subnet traffic routes through you → MITM
- Tool: `yersinia -attack hsrp`
- After taking over: enable IP forwarding on your machine so traffic still flows (transparent MITM)

---

### VRRP — Virtual Router Redundancy Protocol
| Field | Value |
|---|---|
| Port | IP protocol 112, multicast 224.0.0.18 |
| Layer | L3 |
| Purpose | Open standard router redundancy (same idea as HSRP) |

**Attack vectors:**
- Same as HSRP — inject VRRP advertisement with higher priority → claim master router role
- No auth by default in VRRPv2. VRRPv3 has optional auth.
- Tool: `yersinia` or custom Scapy script

---

## VPN & Tunneling

### IPsec — Internet Protocol Security
| Field | Value |
|---|---|
| Port | UDP 500 (IKE), UDP 4500 (NAT traversal), IP protocol 50 (ESP), 51 (AH) |
| Layer | L3 |
| Purpose | Encrypted and authenticated IP communication |

**How it works:** Two modes — Transport mode (encrypts payload only, L4 and above) and Tunnel mode (encrypts entire original packet, wraps in new IP header). Two protocols — ESP (Encapsulating Security Payload, provides encryption + auth) and AH (Authentication Header, auth only, no encryption).

**Attack vectors:**
- IKEv1 aggressive mode → server sends hash in response to any probe before authenticating initiator → capture hash → crack offline
- Weak pre-shared keys → brute force
- Tool: `ike-scan -A target` (probe for aggressive mode)

```bash
ike-scan target                    # check if IKE is running
ike-scan -A target                 # probe aggressive mode
ike-scan -A --id=0 target          # try with null ID
# If aggressive mode responds with hash → crack with hashcat or psk-crack
```

---

### IKE — Internet Key Exchange
| Field | Value |
|---|---|
| Port | UDP 500 |
| Layer | L7 (operates on top of UDP/IP) |
| Purpose | Negotiate and establish IPsec security associations |

**Attack vectors:**
- IKEv1 aggressive mode hash capture → see IPsec above
- IKEv2 is more secure but still worth probing for weak PSK
- Fingerprint IKE implementation to find version-specific CVEs

---

### GRE — Generic Routing Encapsulation
| Field | Value |
|---|---|
| Port | IP protocol 47 |
| Layer | L3 |
| Purpose | Tunnel any L3 protocol inside IP packets |

**How it works:** Wraps any network layer protocol inside an IP packet. No encryption, no authentication. Just a transport wrapper. Used with IPsec for encrypted VPN tunnels or alone for simple point-to-point tunnels.

**Attack vectors:**
- GRE traffic is plaintext → capture and decapsulate in Wireshark → read tunnel contents
- No authentication → inject packets into GRE tunnel if you're on the path
- C2 tunneling: attackers encapsulate malicious traffic in GRE to bypass protocol-based firewalls

---

### PPTP — Point-to-Point Tunneling Protocol
| Field | Value |
|---|---|
| Port | TCP 1723, IP protocol 47 (GRE) |
| Layer | L2 tunnel |
| Purpose | Legacy VPN protocol |

**Attack vectors:**
- MS-CHAPv2 authentication is cryptographically broken → capture handshake → crack 100% of the time given enough compute
- Finding PPTP in a corporate environment = immediate high severity finding
- Tool: `chapcrack`, cloud cracking services

---

### VPN — Virtual Private Network
VPN is the concept, not a single protocol. Built on IPsec, OpenVPN (TLS-based), WireGuard, PPTP, L2TP.

**Pentest relevance:**
- Split tunneling misconfiguration → VPN client routes only corporate traffic through VPN → attacker on same LAN can still reach corporate user's machine
- VPN gateway as a target → exposed to internet → check for known CVEs (Pulse Secure, Fortinet, Cisco ASA have had critical pre-auth RCE vulns)
- DNS leak → even with VPN, DNS queries may go through local resolver → leaks browsing activity

---

## Wireless Security

### WEP — Wired Equivalent Privacy
| Standard | IEEE 802.11 |
|---|---|
| Status | **BROKEN. Dead. Never use.** |

**Attack:** RC4 IV reuse vulnerability → capture enough packets → statistical analysis → recover key in minutes.
```bash
airmon-ng start wlan0
airodump-ng wlan0mon --bssid TARGET --channel N -w capture
aireplay-ng -3 -b TARGET wlan0mon    # ARP replay to generate IVs
aircrack-ng capture*.cap
```

---

### WPA / TKIP — Wi-Fi Protected Access with TKIP
| Standard | IEEE 802.11 |
|---|---|
| Status | Weak. TKIP is deprecated. |

**Attack:** TKIP has known weaknesses. WPA with TKIP: capture 4-way handshake → offline dictionary attack.
```bash
airodump-ng wlan0mon --bssid TARGET -w capture
aireplay-ng -0 1 -a TARGET wlan0mon   # deauth to force re-handshake
aircrack-ng -w wordlist capture*.cap
```

---

### WPA2 with CCMP/AES
| Standard | IEEE 802.11 |
|---|---|
| Status | Current standard. No protocol-level break. |

**Attack:** Capture 4-way handshake → offline brute force/dictionary attack. No shortcut — strength entirely depends on password complexity.

**PMKID attack (no deauth needed):**
```bash
hcxdumptool -i wlan0mon -o capture.pcapng --enable_status=1
hcxpcapngtool -o hash.hc22000 capture.pcapng
hashcat -m 22000 hash.hc22000 wordlist.txt
```

---

### WPA Enterprise (802.1X)
Uses EAP for authentication. See EAP/PEAP/LEAP section above.

---

## Industrial & Management

### SNMP — Simple Network Management Protocol
| Field | Value |
|---|---|
| Port | UDP 161 (agent), UDP 162 (trap/notifications) |
| Layer | L7 |
| Purpose | Monitor and manage network devices |

**How it works:** Manager polls agents on devices. Gets/sets values in the MIB (Management Information Base) — a database of device properties. Community strings act as passwords. v1/v2c: plaintext. v3: encrypted + proper auth.

**Attack vectors:**
- Default community strings → `public` (read), `private` (read-write) → `snmpwalk -v2c -c public target`
- Read access → dump entire device config, routing table, interface IPs, running processes, open ports, user accounts
- Write access (`private`) → change device configuration → routing changes, shutdown interfaces
- SNMPv1/v2c community strings captured in plaintext via Wireshark
- SNMP amplification DDoS → small request → large response → use as reflector

```bash
snmp-check target -c public
snmpwalk -v2c -c public target
onesixtyone -c community_list.txt target    # brute force community strings
```

---

### NTP — Network Time Protocol
| Field | Value |
|---|---|
| Port | UDP 123 |
| Layer | L7 |
| Purpose | Time synchronization across network hosts |

**Attack vectors:**
- Clock skew attack → if you can cause >5 minute time difference on a Windows host → Kerberos authentication fails → denial of service on AD-joined machines
- NTP amplification DDoS → `monlist` command returns list of last 600 clients → ~200x amplification factor → classic DDoS reflection
- Rogue NTP server → push wrong time → affect logging timestamps, certificate validity, scheduled tasks

```bash
ntpq -p target              # query NTP server
nmap -sU -p 123 --script ntp-info target
# Check for monlist (legacy DDoS vector):
nmap -sU -p 123 --script ntp-monlist target
```

---

### SCADA — Supervisory Control and Data Acquisition
Not a single protocol — a category of industrial control systems. Common SCADA protocols: Modbus (port 502), DNP3 (port 20000), EtherNet/IP (port 44818).

**Attack vectors:**
- Most SCADA systems have zero authentication by design ("air-gapped" assumption)
- Modbus has no auth → read/write directly to PLC registers → control physical processes
- Default credentials everywhere
- Ancient unpatched operating systems (Windows XP, older)
- Finding SCADA on a connected network = critical finding
- Real-world impact: Stuxnet (nuclear centrifuges), Ukrainian power grid attacks

---

### SCTP — Stream Control Transmission Protocol
| Field | Value |
|---|---|
| Port | IP protocol 132 |
| Layer | L4 Transport |
| Purpose | Multi-streaming, multi-homing transport for telecom (SS7, VoIP signaling) |

Encountered in 4G/5G core networks and telecom infrastructure. Similar attack surface to TCP but with additional features that add complexity.

---

## Voice & Multimedia

### SIP — Session Initiation Protocol
| Field | Value |
|---|---|
| Port | 5060 UDP/TCP (plain), 5061 TCP (TLS) |
| Layer | L7 |
| Purpose | Signaling for VoIP calls — setup, modify, teardown sessions |

**How it works:** SIP sets up calls. The actual audio/video is separate — carried by RTP (Real-time Transport Protocol) on dynamic UDP ports. SIP is text-based, similar to HTTP in structure.

**Attack vectors:**
- Extension enumeration → send OPTIONS or REGISTER to extensions → valid ones return 200 OK, invalid return 404 → map all valid extensions → tool: `svmap`, `svwar` (SIPVicious)
- VoIP eavesdropping → if already on network (ARP poisoning) → capture RTP stream → reassemble audio → tool: `rtpbreak`, Wireshark
- SIP authentication brute force → REGISTER requests with different passwords → tool: `svcrack`
- Toll fraud → unauthenticated SIP server → make calls billed to victim organization
- Denial of service → SIP flood → disrupt phone system

```bash
svmap 192.168.1.0/24        # discover SIP devices
svwar -e 100-999 target     # enumerate extensions
svcrack -u 100 target       # brute force extension 100
```

---

### VoIP — Voice Over IP
VoIP is the technology category. SIP is the most common signaling protocol. RTP (Real-time Transport Protocol) carries the actual audio on UDP.

**Pentest relevance:** VoIP infrastructure often on the same flat network as workstations. Compromise it → eavesdrop on calls → corporate espionage. Misconfigured SIP proxies → toll fraud.

---

## Encryption & Key Exchange

### PGP — Pretty Good Privacy
| Field | Value |
|---|---|
| Port | N/A (application-level) |
| Layer | L7 |
| Purpose | Asymmetric encryption for email and files |

**How it works:** Public key encrypts (anyone can encrypt to you). Private key decrypts (only you can read). Private key signs (proves message came from you). Public key verifies signature.

**Pentest relevance:**
- PGP public keys on keyservers (keys.openpgp.org) reveal email addresses → OSINT
- Finding unprotected private keys in post-exploitation → can decrypt stored communications
- PGP-signed commits in git repos → verify developer identity

---

### IPsec
See VPN & Tunneling section above.

---

## Miscellaneous / Web Dev

### NAT — Network Address Translation
| Field | Value |
|---|---|
| Port | N/A (router function) |
| Layer | L3/L4 |
| Purpose | Map multiple private IPs to one public IP |

**Pentest relevance:**
- Devices behind NAT not directly reachable from internet → SSRF to pivot to internal hosts from a compromised server
- Internal IPs leaking in HTTP headers (`X-Forwarded-For`, `X-Real-IP`) → info disclosure
- NAT doesn't exist in IPv6 → all devices directly reachable → different attack model

---

### CRLF — Carriage Return Line Feed
`\r\n` = `0x0D 0x0A`. HTTP uses CRLF to separate headers. Double CRLF ends headers.

**Attack:** Inject `%0d%0a` (URL-encoded CRLF) into a value reflected in HTTP response headers → inject new headers, set cookies, split responses.

```
GET /redirect?url=http://evil.com%0d%0aSet-Cookie:%20session=attacker
```

---

### AJAX
Background HTTP requests from JavaScript. Watch for XHR calls in Burp Suite history. Often less secured than main application endpoints.

---

### NNTP — Network News Transfer Protocol
| Field | Value |
|---|---|
| Port | 119 TCP (plain), 563 TCP (TLS) |
| Layer | L7 |
| Purpose | Usenet newsgroup distribution (legacy) |

Rarely seen. Check for anonymous access and information disclosure if encountered.

---

## OSI Quick Reference

```
Layer 7 - Application   Data      HTTP, DNS, FTP, SMTP, SSH, SNMP, SIP
Layer 6 - Presentation  Data      TLS/SSL, encoding, compression
Layer 5 - Session       Data      Session management, NetBIOS
Layer 4 - Transport     Segment   TCP, UDP, SCTP
Layer 3 - Network       Packet    IP, ICMP, IPsec, OSPF, RIP, EIGRP
Layer 2 - Data Link     Frame     Ethernet, ARP, STP, VTP, 802.1Q VLAN
Layer 1 - Physical      Bits      Cables, WiFi, fiber, electrical signal
```

---

## Reserved IP Ranges

```
10.0.0.0/8          Private Class A  → Large enterprise, VPNs, cloud
172.16.0.0/12       Private Class B  → VM environments, corporate VPN
192.168.0.0/16      Private Class C  → Home/small office
127.0.0.0/8         Loopback         → Service on 127.x = local access only
169.254.0.0/16      APIPA            → Failed DHCP → device self-assigned
224.0.0.0/4         Multicast D      → 224.0.0.2 HSRP, 224.0.0.5 OSPF
240.0.0.0/4         Reserved E       → Unused
255.255.255.255/32  Broadcast        → All hosts on local subnet
0.0.0.0/0           Default route    → Matches all IPs (used in routing/firewall rules)
```

---

## MAC Address Cheat Sheet

```
FF:FF:FF:FF:FF:FF   Broadcast        → All devices on subnet
01:00:5E:xx:xx:xx   IPv4 Multicast   → Group traffic
01:80:C2:00:00:00   STP              → Spanning Tree BPDUs
01:00:0C:CC:CC:CC   CDP/VTP          → Cisco Discovery Protocol
01:00:0C:CC:CC:CD   PVST+            → Cisco Per-VLAN STP

First byte bit 0: 0=Unicast, 1=Multicast
First byte bit 1: 0=Global OUI (real hardware), 1=Locally administered (MAC was changed)

OUI Fingerprinting:
00:50:56  → VMware VM
00:0C:29  → VMware VM
B8:27:EB  → Raspberry Pi
00:1A:A0  → Dell
3C:D9:2B  → HP
```

---

## Quick Attack Cheat Sheet by Protocol

| Protocol | Port | Quick Win |
|---|---|---|
| FTP | 21 | `ftp target` → try anonymous |
| SSH | 22 | Check version CVEs, try default creds |
| SMTP | 25 | `VRFY user` → enumerate users |
| HTTP | 80 | Burp Suite, dirbusting, param fuzzing |
| SNMP | 161 UDP | `snmpwalk -v2c -c public target` |
| HTTPS | 443 | Check TLS version, cert, Burp Suite |
| SMB | 445 | `smbmap -H target`, check MS17-010 |
| NFS | 2049 | `showmount -e target` |
| SIP | 5060 | `svmap target`, extension enum |
| RIP | 520 UDP | Inject fake routes (no auth v1) |
| OSPF | proto 89 | Inject LSAs if no auth |
| CDP | L2 only | Wireshark → filter cdp → free recon |
| HSRP | 1985 UDP | `yersinia` → claim active router |
| STP | L2 only | `yersinia` → claim root bridge |
| IKE | 500 UDP | `ike-scan -A target` → aggressive mode |

---

*Last updated: based on HTB Academy Intro to Networking module*
*Reference: personal notes — security engineer / pentester oriented*
