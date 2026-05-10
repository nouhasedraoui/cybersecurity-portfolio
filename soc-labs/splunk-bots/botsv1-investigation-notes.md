# Splunk Boss of the SOC v1 (BOTSv1) — Investigation Notes
**Platform:** Splunk BOTS (bots.splunk.com)  
**Date Completed:** May 10, 2026  
**Score:** 16,193 | Base: 9,700 | Bonus: 6,493 | Penalty: 0  
**Scenarios:** Web Defacement (Scenario 1) + Cerber Ransomware (Scenario 2)  
**Status:** Both scenarios completed ✓

---

## What is BOTSv1?

BOTSv1 is a blue team CTF created by Splunk. It simulates a real SOC
investigation where you play the role of Alice, a security analyst at
Wayne Enterprises, investigating two real attack scenarios using Splunk
across live log sources.

Unlike courses and certifications, BOTSv1 gives you real data from a
real attack — no simulated answers, no multiple choice. You write SPL
queries, correlate events across multiple log sources, and reconstruct
the full attack chain yourself.

---

## Log Sources Available in BOTSv1

| Sourcetype | What It Records |
|-----------|----------------|
| `stream:http` | HTTP traffic — URLs, POST uploads, user agents, file downloads |
| `stream:dns` | DNS queries and responses |
| `stream:smb` | SMB file share activity |
| `WinRegistry` | Windows Registry changes — USB insertions, persistence |
| `WinEventLog:Security` | Windows Security events — logins, process creation (EventID 4688) |
| `XmlWinEventLog:Microsoft-Windows-Sysmon/Operational` | Sysmon — process creation, file creation, hashes (most detailed) |
| `fgt_utm` | Fortigate firewall logs — file downloads, URL filtering |
| `suricata` | Suricata IDS — signature alerts for known malware |

---

## SPL Commands Learned

### Basic Search Structure
```
index=botsv1 sourcetype=stream:http src_ip=192.168.250.100
| table _time, src_ip, dest_ip, uri_path
| sort _time
```

### Key Commands

**`table`** — Pick which columns to display. Without this, Splunk
shows the full raw event which is overwhelming.
```
| table _time, src_ip, dest_ip, uri_path, http_method, status
```

**`stats count by`** — Group and count events. Used to spot
anomalies like one IP making thousands of requests.
```
| stats count by src_ip
| sort -count
```
The `-` before count means descending (biggest first). The attacker
always appears at the top because their request count is abnormally high.

**`stats earliest(_time) as first_seen by stage`** — For timelines.
Gets the first occurrence of each stage instead of listing every event.
```
| stats earliest(_time) as first_seen by stage
| eval first_seen=strftime(first_seen, "%Y-%m-%d %H:%M:%S")
```

**`sort`** — Order results:
```
| sort -count     ← biggest first (descending)
| sort +count     ← smallest first (ascending)
| sort _time      ← chronological
```

**`head`** — Show only top N results:
```
| head 10
```

**`eval`** — Create new fields or categorize events:
```
| eval stage=case(
    sourcetype="winregistry", "Stage 2: USB Inserted",
    sourcetype="stream:dns", "Stage 6: DNS Lookup"
)
```

**`mvexpand`** — Expand multi-value fields into separate rows.
Critical for `part_filename` (file uploads) and `answer` (DNS responses)
because Splunk stores them as multi-value and they appear empty in `table`
without this command:
```
| mvexpand part_filename
| search part_filename=*.exe
```

**`rex`** — Extract specific text from a field using regex.
Used to pull MD5 from the Sysmon Hashes field:
```
| rex field=Hashes "MD5=(?<md5>[A-F0-9]+)"
```
Breaking it down:
- `MD5=` → find the literal text "MD5="
- `(?<md5>` → start a named capture group called "md5"
- `[A-F0-9]+` → capture hex characters (A-F and 0-9), one or more
- `)` → end the capture group

**`where isnotnull(stage)`** — Filter out null values. Used after
`eval case()` to remove events that didn't match any condition.

**`match(_raw, "keyword")`** — Raw text search inside the full event.
More reliable than field-based search when fields are empty or multi-value:
```
sourcetype="WinEventLog:Security" AND match(_raw,"Miranda_Tate_unveiled")
```

---

## Regex Cheat Sheet for SPL

| Pattern | Meaning |
|---------|---------|
| `.` | Any single character |
| `+` | One or more of previous |
| `*` | Zero or more of previous |
| `\d` | Any digit (0-9) |
| `[A-Z]` | Any uppercase letter |
| `[0-9]` | Any digit |
| `[A-F0-9]` | Hex characters (for hashes) |
| `(?<name>...)` | Named capture group |
| `.*` | Any text (wildcard) |
| `(?i)` | Case-insensitive matching |
| `\.` | Literal dot (escaped) |

---

## Sysmon EventIDs Reference

| EventID | Meaning | When to Use |
|---------|---------|-------------|
| 1 | Process creation | Find process hashes, command lines, parent processes |
| 2 | File creation time changed | Find encrypted files — ransomware changes timestamps |
| 3 | Network connection | Find malware making outbound connections |
| 7 | Image/DLL loaded | Shows DLLs loaded by a process |
| 11 | File created | Find files dropped to disk by malware |

**Important:** When searching for a file hash, always use `EventID=1`
(process creation). EventID 7 gives hashes of loaded DLLs which are
different from the main executable hash.

---

## SOC Analyst Query-Building Process

A real analyst thinks in 5 questions before writing any SPL:

```
1. WHAT am I looking for?    → file, IP, user, hash, domain
2. WHERE is that data?       → which sourcetype has it?
3. HOW is it stored?         → field name, multi-value, raw text?
4. HOW do I filter noise?    → narrow by IP, time, host, method
5. HOW do I present it?      → table, stats, chart
```

Build queries one piece at a time — not all at once:

```
Step 1: index=botsv1 sourcetype=stream:http        ← where
Step 2: dest_ip=192.168.250.70 http_method=POST    ← filter
Step 3: | mvexpand part_filename                    ← fix multi-value
Step 4: | search part_filename=*.exe               ← narrow down
Step 5: | table _time, src_ip, part_filename       ← clean output
```

---

## When Fields Fail — Use Raw Text Search

| Situation | Solution |
|-----------|---------|
| Field works correctly | `field=value` |
| Field is multi-value and shows blank | `mvexpand field` |
| Field is unreliable or missing | `match(_raw, "keyword")` |
| Not sure which field | Use raw keyword: `"keyword"` in search bar |

Raw text search is your safety net in BOTSv1. Always works.

---

## Scenario 1 — Web Defacement (Po1s0n1vy APT)

### Target
- Victim web server: `192.168.250.70` (`imreallynotbatman.com`)
- CMS: Joomla
- Attacker: Po1s0n1vy APT group

### Attack Chain

**Phase 1 — Reconnaissance**
Attacker IP `40.80.148.42` ran automated scanning using Acunetix
web vulnerability scanner against the Joomla site. Detected via
unusually high request count in `stream:http`.

```
index=botsv1 sourcetype=stream:http dest_ip=192.168.250.70
| stats count by src_ip
| sort -count
```

**Phase 2 — Brute Force**
Attacker brute-forced the Joomla administrator login at
`/joomla/administrator/index.php` with hundreds of POST requests.

```
index=botsv1 sourcetype=stream:http dest_ip=192.168.250.70
uri_path="/joomla/administrator/index.php" http_method=POST
| stats count by src_ip
| sort -count
```

**Phase 3 — Malware Upload**
After gaining Joomla admin access, attacker uploaded `3791.exe`
via Joomla's file manager extension (com_extplorer).

Key lesson: File uploads use `part_filename` field in `stream:http`
and require `mvexpand` to display correctly.

```
index=botsv1 sourcetype=stream:http http_method=POST dest_ip=192.168.250.70
| mvexpand part_filename
| search part_filename=*.exe
| table _time, src_ip, part_filename, uri_path
```

**Phase 4 — Web Defacement**
The web server (`192.168.250.70`) itself reached out to the
attacker's C2 server to download the defacement image.

Critical insight: The web server was the SOURCE, not the destination.
All previous queries failed because they filtered `dest_ip=192.168.250.70`
but the download went FROM the server TO the attacker.

```
index=botsv1 sourcetype=stream:http src_ip=192.168.250.70
| table _time, src_ip, dest_ip, uri_path, site
| sort _time
```

### Key IOCs — Scenario 1

| IOC | Value |
|-----|-------|
| Defacement file | `poisonivy-is-coming-for-you-batman.jpeg` |
| C2 domain | `prankglassinebracket.jumpingcrab.com` |
| Attacker IP | `23.22.63.114` |
| C2 port | `1337` |
| Attacker scanner IP | `40.80.148.42` |
| Uploaded malware | `3791.exe` |
| Attacker's own domain | `po1s0n1vy.com` |

### Key Lesson — Scenario 1

The defacement was not delivered TO the web server — the web server
was compromised and made to pull the file itself. This is a common
pattern: attacker plants a script, script reaches out to C2, C2
delivers the payload. Always check both `src_ip` and `dest_ip`
when investigating web traffic.

---

## Scenario 2 — Cerber Ransomware Investigation

### Incident Summary

| Field | Value |
|-------|-------|
| Incident Date | 2016-08-24 |
| Victim User | bob.smith.WAYNECORPINC |
| Victim Host | we8105desk (192.168.250.100) |
| File Server | we9041srv (192.168.250.20) |
| Malware | Cerber Ransomware v2 |
| Classification | CRITICAL |
| Initial Vector | USB drop — Miranda_Tate_unveiled.dotm |
| Attack Duration | 1 hour 45 minutes |
| Files Encrypted (local) | 406 TXT files on we8105desk |
| Files Encrypted (remote) | 257 PDF files on we9041srv |
| Total Suricata Alerts | 53,592 |

---

### Full Attack Kill Chain

**Stage 1 — USB Drive Inserted (16:42:17)**
Bob found a USB drive in the parking lot (social engineering — USB drop).
He inserted it into his workstation. Detected in `WinRegistry` via
`USBSTOR` key showing device label `MIRANDA_PRI`.

**Stage 2 — Malicious Macro Executed (16:43:27)**
Bob opened `Miranda_Tate_unveiled.dotm` from the USB drive (D:\).
Word opened the file and executed the embedded macro.
`Explorer.exe (PID 3496)` launched `WINWORD.EXE (PID 3756)`.
Detected in `Sysmon EventID 1`.

**Stage 3 — C2 DNS Beacon (16:48:12)**
The macro wrote `20429.vbs` to AppData and immediately resolved
`solidaritedeproximite.org` via DNS. Detected in `stream:dns`.

**Stage 4 — Payload Download — Steganography (16:48:13)**
`mhtr.jpg` downloaded from `solidaritedeproximite.org`.
This is NOT a real image — the Cerber cryptor binary was hidden
inside the JPEG using steganography, bypassing all file-type
inspection at the network perimeter.
Detected in `stream:http` and `fgt_utm`.

**Stage 5 — VBScript Execution (17:15:12)**
`wscript.exe` executed `20429.vbs` which launched `121214.tmp`
(the Cerber cryptor binary extracted from mhtr.jpg).
The cryptor self-deleted after execution using:
```
taskkill /t /f /im "121214.tmp" & ping -n 1 127.0.0.1 & del "121214.tmp"
```
This left no binary on disk — standard anti-forensics technique.
Detected in `Sysmon EventID 1`.

**Stage 6 — IDS Alert — Cerber Detected (16:49:24)**
Suricata fired signature `2816763` (ETPRO TROJAN Ransomware/Cerber
Checkin 2) against external IP `85.93.0.0` — a confirmed Tor relay node.
53,592 total alerts generated during the incident.

**Stage 7 — Local File Encryption (17:05:21)**
Cerber began encrypting files on Bob's local machine. 406 TXT files
encrypted. Detected via `Sysmon EventID 2` (file creation time changed).

**Stage 8 — Lateral Movement to File Server (18:27:38)**
Cerber used Bob's active SMB session to reach `we9041srv`.
No exploit was used — it inherited Bob's existing write permissions
on the network share. This is a textbook Principle of Least Privilege
failure. Detected in `stream:smb`.

**Stage 9 — Remote Server Encryption (18:27:24)**
257 PDF files encrypted on `we9041srv`. Detected via
`WinEventLog:Security EventID 5145` (network share object accessed)
on the file server itself.

**Stage 10 — Ransom Payment C2 (17:15:12)**
Cerber resolved `cerberhhyed5frqa.xmfir0.win` — the Tor-proxied
ransom payment portal. This DNS resolution marks the moment Cerber
completed local encryption and displayed the ransom demand.

---

### Cerber C2 Evasion — NetBIOS Encoded DNS

Cerber used an advanced covert C2 channel — encoding victim machine
identifiers, encryption status, and configuration data into DNS hostnames
in NetBIOS format, then broadcasting to `192.168.250.255`
(the subnet broadcast address).

Example encoded hostname: `FHFAEBEECACACACACACACACACACACAAA`

This blends perfectly into normal Windows NetBIOS traffic and is
extremely difficult to detect with signature-based tools. 228 queries
for the primary encoded hostname confirmed continuous C2 communication
throughout the full encryption session (16:34 to 18:10 UTC).

---

### IOC Summary — Scenario 2

| IOC Type | Value |
|----------|-------|
| Infected host | we8105desk |
| Victim IP | 192.168.250.100 |
| File server | we9041srv / 192.168.250.20 |
| USB device label | MIRANDA_PRI |
| Initial file | Miranda_Tate_unveiled.dotm |
| Dropper | 121214.tmp via VBScript 20429.vbs |
| C2 domain | solidaritedeproximite.org |
| Cryptor payload | mhtr.jpg (steganography) |
| Ransom payment FQDN | cerberhhyed5frqa.xmfir0.win |
| Ransomware family | Cerber v2 |
| Tor relay range | 85.93.0.0/8 |
| Attack start | 2016-08-24 16:42 UTC |
| Encryption complete | 2016-08-24 18:27 UTC |

---

### Complete Kill Chain Timeline Query

```
index=botsv1 (host=we8105desk OR host=we9041srv)
| eval phase=case(
    sourcetype="WinRegistry" AND isnotnull(registry_key_name)
        AND like(registry_key_name,"%USBSTOR%"),
        "1 - USB Inserted",
    sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
        AND isnotnull(CommandLine)
        AND (like(CommandLine,"%.dotm%") OR like(ParentCommandLine,"%WINWORD%")),
        "2 - Macro Executed",
    sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
        AND isnotnull(CommandLine)
        AND (like(CommandLine,"%121214.tmp%") OR like(CommandLine,"%.vbs%")),
        "3 - VBScript/Payload",
    sourcetype="stream:dns" AND isnotnull('query{}')
        AND isnotnull(mvfind('query{}',"solidaritedeproximite")),
        "4 - C2 DNS Beacon",
    sourcetype="stream:http" AND isnotnull('http.url')
        AND like('http.url',"%mhtr.jpg%"),
        "5 - Payload Download",
    sourcetype="suricata" AND isnotnull('alert.signature')
        AND like('alert.signature',"%erber%"),
        "6 - IDS Alert Cerber",
    sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"
        AND EventCode="2" AND isnotnull(TargetFilename)
        AND like(TargetFilename,"%bob.smith%"),
        "7 - Local Encryption",
    sourcetype="stream:smb" AND dest_ip="192.168.250.20",
        "8 - Lateral to File Server",
    host="we9041srv" AND EventCode="5145",
        "9 - Remote Encryption",
    sourcetype="stream:dns" AND isnotnull(mvfind('query{}',"cerberhhyed")),
        "10 - Ransom Page C2",
    true(), "Other"
)
| where phase!="Other"
| eval key=phase+"||"+sourcetype+"||"+coalesce(src_ip,Source_Address,"")
    +"||"+coalesce(dest_ip,"")
| dedup key
| table _time phase sourcetype src_ip dest_ip
| sort _time
```

---

### Suricata IDS Signatures Triggered

| Signature | Sig ID | Risk | Hit Count | Meaning |
|-----------|--------|------|-----------|---------|
| ETPRO TROJAN Ransomware/Cerber Checkin 2 | 2816763 | CRITICAL | 1 | Primary C2 check-in to Tor relay |
| ETPRO TROJAN Ransomware/Cerber Onion Domain Lookup | 2820156 | CRITICAL | 2 | Ransom payment page resolved |
| ET TOR Known Tor Relay | 2523162 | HIGH | 2 | Bidirectional Tor communication |
| ET SCAN Unusual Port 445 traffic | 2001569 | MEDIUM | 3 | SMB scanning behavior |
| ET POLICY Possible External IP Lookup ipinfo.io | 2020716 | MEDIUM | 1 | Malware checking its external IP |
| SURICATA DNS malformed request data | 2240002 | INFO | 705 | Reverse DNS from file server — not attack-related |

---

### Process Execution Chain (Sysmon EventID 1)

```
Explorer.exe (PID 3496)
    └── WINWORD.EXE (PID 3756)
            └── cmd.exe (PID 3884) [obfuscated command — wrote 20429.vbs]
                    └── wscript.exe (PID 3968) [executed 20429.vbs]
                            └── cmd.exe (PID 1476)
                                    └── 121214.tmp (PID 2948) [Cerber cryptor]
                                            └── taskkill.exe [self-deleted 121214.tmp]

Later (17:15:12):
osk.exe (Cerber persistence module)
    └── wscript.exe [played ransom audio + displayed "DECRYPT MY FILES" note]
```

---

### DNS Beaconing Analysis

| Domain | DNS Server | Query Count | Classification | Risk |
|--------|-----------|-------------|---------------|------|
| FHFAEBEECAC... (NetBIOS encoded) | 192.168.250.255 | 228 | Cerber C2 encoded | HIGH |
| cerberhhyed5frqa.xmfir0.win | 192.168.250.20 | 1 | Ransom payment FQDN | CRITICAL |
| solidaritedeproximite.org | 192.168.250.20 | 1 | C2 payload domain | CRITICAL |
| ipinfo.io | 192.168.250.20 | 1 | IP geolocation recon | MEDIUM |

---

### Why the Attack Succeeded — Root Causes

**1. USB ports not restricted by policy**
Bob was able to insert an untrusted USB device and open a file
directly from it with no security control stopping him.

**2. Microsoft Office macros allowed from untrusted sources**
The `.dotm` file ran its macro automatically. Macro execution from
external/untrusted documents should be disabled by Group Policy.

**3. Principle of Least Privilege failure**
Bob had write access to the corporate file server share. Cerber
inherited his credentials from the active session and encrypted
257 PDFs on the file server without exploiting any vulnerability.
Read-only permissions would have prevented all remote encryption.

**4. Steganography bypassed perimeter controls**
The cryptor binary was hidden inside `mhtr.jpg`. All network
perimeter tools inspecting file extensions or MIME types saw only
an image file — no executable detected.

---

### Defensive Recommendations

```
Immediate actions:
→ Block domains: solidaritedeproximite.org, cerberhhyed5frqa.xmfir0.win
→ Isolate we8105desk from network
→ Audit network share permissions — apply read-only where write not needed

SIEM rules to create:
→ Alert on WINWORD.EXE spawning CMD.EXE
→ Alert on mass file modifications on SMB shares (>50 files/minute)
→ Alert on NetBIOS-encoded DNS broadcasts to 255 broadcast address
→ Alert on outbound HTTP to non-standard ports (port 1337, etc.)

Policy changes:
→ Disable USB ports via Group Policy or endpoint control
→ Disable Office macros from external/untrusted sources
→ Enforce Principle of Least Privilege on all network shares
→ Deploy application whitelisting to block unknown executables in AppData
```

---

## Threat Intelligence — External Pivoting

For the question about Po1s0n1vy's pre-staged malware SHA256,
no Splunk data was needed. The answer came from external threat
intelligence databases.

**The pivot chain:**
```
Attacker IP (23.22.63.114)
    ↓
ThreatMiner / AlienVault OTX
    ↓
Passive DNS → found po1s0n1vy.com and multiple Wayne Corp typosquats
    ↓
ThreatMiner domain search → malware samples associated with the domain
    ↓
SHA256 hash of the spear phishing attachment
```

**Threat intelligence sites used:**
- `threatminer.org` — malware samples, passive DNS, IP reputation
- `otx.alienvault.com` — indicators, passive DNS, related pulses
- `virustotal.com` — file and IP analysis

**Key lesson:** SOC analysts don't only work inside SIEM tools.
Real investigations pivot to external threat intelligence sources
to understand attacker infrastructure, TTPs, and historical activity.

---

## Data Inventory Commands for SOC Analysts

These are the first commands to run at the start of any shift
to verify log sources are alive and sending data:

```
| tstats count where index=botsv1 by sourcetype
```
Shows how many events exist per sourcetype — lets you spot missing
or stopped log sources immediately.

```
| metadata type=sourcetypes index=botsv1
| eval last_seen=strftime(recentTime,"%Y-%m-%d %H:%M:%S")
| table sourcetype, totalCount, last_seen
```
Shows the last time each sourcetype sent data. If `last_seen` is
hours ago for a critical source like endpoint logs — investigate.

---

## Key Lessons Learned

**1. src_ip vs dest_ip direction matters**
The web defacement file was NOT sent to the server — the server
fetched it. Always consider both directions of traffic.

**2. Multi-value fields need mvexpand**
`part_filename` in stream:http and `answer` in stream:dns appear
empty in table without `mvexpand`. This is a BOTSv1 gotcha that
applies to real environments too.

**3. Raw text search is your fallback**
When field-based searching fails, `match(_raw,"keyword")` always
works. Fields may be indexed differently but the raw event is always there.

**4. Steganography bypasses perimeter controls**
A cryptor binary hidden in a JPEG file passed all network
inspection tools. Detection required endpoint monitoring (Sysmon)
not perimeter tools.

**5. Least privilege prevents lateral movement**
Cerber reached the file server using Bob's existing permissions.
No exploit, no vulnerability — just inherited access. Proper
share permissions = ransomware stays on one machine.

**6. Covert C2 blends into normal traffic**
Cerber encoded C2 data into NetBIOS DNS queries — identical in
structure to normal Windows network traffic. Signature-based
detection missed it. Behavioral rules are required.

**7. The initial phase generates almost no noise**
USB insertion → document open → DNS query → file download.
Four events before any encryption begins. Signature tools are
blind at this stage. Detection requires behavioral monitoring.

---

*BOTSv1 Investigation Notes — Nouha Sedraoui — May 2026*
