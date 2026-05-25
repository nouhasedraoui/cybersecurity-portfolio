# CyberHeroes — TryHackMe Room

**Room:** [CyberHeroes](https://tryhackme.com/room/cyberheroes)  
**Category:** Web · Authentication  
**Difficulty:** Easy  
**Flags:** 1  
**Completed:** May 2026

---

## What This Room Is Actually About

The room asks one question: *"Want to be a part of the elite club of CyberHeroes? Prove your merit by finding a way to log in."*

There's a login form, a flag behind it, and no instructions beyond that. The whole challenge is about recognizing that **client-side authentication is not real authentication** — and that developers sometimes leave credentials sitting right there in the page source, thinking obscuring them slightly is good enough.

This room is deliberately beginner-friendly, but the vulnerability it demonstrates (broken authentication via exposed client-side logic) shows up in real-world applications more than you'd expect.

---

## The Methodology

### Step 1 — Reconnaissance with Nmap

Before touching the web interface, I ran a port scan to understand what services are running:

```bash
nmap -sV -vv <MACHINE_IP>
```

Results:
- **Port 22** — SSH (OpenSSH)
- **Port 80** — HTTP (Apache httpd 2.4.48)

SSH with no credentials is a dead end at this stage. HTTP is where the target lives.

### Step 2 — Visit the Web Application

Navigating to `http://<MACHINE_IP>` brings up a simple page with a login form. Nothing unusual on the surface — just username and password fields, and a submit button.

At this point I tried the obvious:
- `admin:admin` — rejected
- SQL injection (`' OR 1=1 --`) — nothing
- Default creds — nothing

The form just rejected everything. That's the cue to stop guessing and start reading.

### Step 3 — View Page Source

This is the move that breaks the room. `Ctrl+U` in the browser opens the raw HTML source. Scrolling through it, there's a `<script>` block handling the login validation:

```javascript
function checkCreds() {
    let a = document.getElementById('uname')
    let b = document.getElementById('pass')
    const RevereString = str => [...str].reverse().join('');

    if (a.value == "h3ck3rBoi" & b.value == RevereString("54321@terceSrepuS")) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                document.getElementById("flag").innerHTML = this.responseText;
                document.getElementById("todel").innerHTML = "";
                document.getElementById("rm").remove();
            }
        };
        // ... fetches flag from server
    }
}
```

Everything is right there.

---

## Breaking Down the JavaScript

### The `RevereString` Function

```javascript
const RevereString = str => [...str].reverse().join('');
```

This is an ES6 arrow function. It does three things to whatever string you pass it:

1. `[...str]` — Spreads the string into an array of individual characters: `["5","4","3","2","1","@","t","e","r","c","e","S","r","e","p","u","S"]`
2. `.reverse()` — Flips the array order
3. `.join('')` — Stitches it back into a single string

So `RevereString("54321@terceSrepuS")` becomes `SuperSecret@12345`.

The developer stored the password reversed in the source code, probably thinking that would be enough to hide it. It's not. Anyone reading the source immediately sees both the original reversed string *and* the function that reverses it.

### The Credentials

From the `if` statement:

| Field | Value |
|-------|-------|
| Username | `h3ck3rBoi` |
| Password | `SuperSecret@12345` (reverse of `54321@terceSrepuS`) |

### Step 4 — Log In

Enter the credentials into the login form and submit. The flag appears on the page.

---

## Alternative Method — Using Linux `rev`

Instead of reversing the string manually or in your head, you can do it straight in the terminal:

```bash
echo "54321@terceSrepuS" | rev
# Output: SuperSecret@12345
```

The `rev` command reads each line and outputs the characters in reverse order. One line, done.

---

## Optional: Directory Enumeration

While not required to solve this room, running a directory scan is good practice:

```bash
gobuster dir -u http://<MACHINE_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 50
```

In this case it doesn't reveal anything critical, but the habit of enumerating before diving into manual analysis is worth building early. You don't want to miss a `/admin` panel or a `/backup` directory by jumping straight to the first thing you see.

---

## What I Actually Learned

### Client-side authentication is not authentication

This is the main lesson and it can't be overstated. Putting credential checks inside JavaScript that runs *in the user's browser* means the user has full access to that code. There is no secret. The browser downloads it, executes it, and the developer console or `View Source` exposes everything.

Real authentication happens on the **server side**. The server receives the credentials, checks them against a database (using hashed and salted values), and only then grants access. The browser never sees the logic, never sees the stored credentials, and has nothing to inspect.

### Obscuring ≠ Encrypting

Reversing a string is not a security measure. It's not hashing, it's not encryption, it's a transformation that anyone who reads the code can instantly reverse. The developer might have thought: *"well, it's not in plain text."* But reversed text is still in plain sight the moment you see the reversal function next to it.

This thinking — that slight obfuscation equals security — has a name: **Security Through Obscurity**. It's considered a failed approach in any serious security design.

### Source Code Review is a Core Skill

This room only requires reading the page source. No fancy tools, no exploit frameworks, no brute force. The vulnerability is sitting openly in the HTML. This is a reminder that before reaching for automated tools, a manual look at what the application is actually serving you often saves significant time.

In real-world web testing, JavaScript files are often where the interesting things hide: hardcoded API keys, internal endpoints, logic that shouldn't be client-side, debug functions left in production builds.

### `Ctrl+U` and Developer Tools Are Your Default Starting Point

For any web challenge, the first two things to check should be:
- `Ctrl+U` — raw page source
- `F12` → Console/Network/Sources tabs in browser DevTools

A huge percentage of beginner-to-intermediate web CTF challenges are solved purely through source inspection, before a single packet gets analyzed or a single tool gets launched.

### The `&` vs `&&` Bug

One small detail worth noting from the source: the condition uses `&` instead of `&&`:

```javascript
if (a.value == "h3ck3rBoi" & b.value == RevereString("54321@terceSrepuS"))
```

`&` is a bitwise AND operator. `&&` is a logical AND. This is a bug — both happen to produce correct behavior here because the comparison results are booleans (0 or 1), but in more complex conditions this could cause unexpected behavior. Spotting these kinds of micro-bugs in code review is part of what makes a good security engineer.

---

## The Vulnerability in OWASP Terms

This room demonstrates **A07:2021 — Identification and Authentication Failures** from the OWASP Top 10. Specifically:

- Credentials stored/exposed in client-side code
- Authentication logic executing in an untrusted environment (the browser)
- No server-side validation of any kind

---

## Key Takeaways

| Lesson | Practical Impact |
|--------|----------------|
| Client-side auth = no auth | Never trust logic that runs in the browser |
| Source code always leaks eventually | Treat JS files as public documentation |
| Obscurity ≠ security | Reversing, encoding, or renaming isn't protecting |
| `rev` in Linux | Quick one-liner for string reversal in terminal |
| Enumeration before exploitation | Scan and explore before guessing |

---

## Tools Used

- `nmap` — port scanning and service discovery
- `gobuster` — directory enumeration (optional)
- Browser `View Page Source` (`Ctrl+U`) — the actual solution
- `rev` (Linux) — terminal string reversal
- Browser DevTools — inspection and analysis

---

## Related Rooms

- [Authentication Bypass](https://tryhackme.com/room/authenticationbypass) — goes deeper into broken auth techniques
- [How Websites Work](https://tryhackme.com/room/howwebsiteswork) — explains the client-server model that makes this attack possible
- [Offensive Security Intro](https://tryhackme.com/room/offensivesecurityintrokK) — broader ethical hacking context

---

*Completed May 2026 · Documented for personal reference and portfolio*
