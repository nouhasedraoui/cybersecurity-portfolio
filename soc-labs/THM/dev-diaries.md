# Dev Diaries — TryHackMe Room

**Room:** [Dev Diaries](https://tryhackme.com/room/devdiaries)  
**Category:** OSINT / Git Forensics  
**Difficulty:** Easy  
**Flags:** 1 hidden flag + 4 investigative answers  
**Completed:** May 2026

---

## What This Room Is Actually About

A freelance developer built a website for a client and then disappeared without handing over the source code. The client is left with one thing: the domain `marvenly.com`. Your job is to trace every digital breadcrumb the developer left behind — subdomains, archived pages, GitHub commits, email metadata — and recover the flag and the full story.

No exploits. No CVEs. No brute force. This is pure OSINT: open-source intelligence gathering using publicly available information. The whole room demonstrates a concept that matters a lot in real security work — **data doesn't disappear just because someone tried to delete it.**

---

## The Investigation — Step by Step

### Step 1 — Subdomain Enumeration via Certificate Transparency

The main `marvenly.com` domain is either down or returns nothing useful. The first move is to look for subdomains — development environments, staging servers, admin panels — that might still be up and less locked down.

The tool here is **crt.sh**, a public database of SSL/TLS certificate transparency logs. Every time a certificate is issued for a domain or subdomain, it gets logged publicly.

Navigate to: `https://crt.sh/?q=marvenly.com`

This reveals a subdomain: **`uat-testing.marvenly.com`**

UAT stands for **User Acceptance Testing** — it's the pre-production environment developers use before pushing to production. These environments are typically:
- Less secured than the production site
- Sometimes left running long after the main site goes offline
- Often contain debugging info, comments, and references to internal tooling

Alternatively, subdomain enumeration tools work here too:

```bash
subfinder -d marvenly.com
```

**Answer to Q1:** `uat-testing.marvenly.com`

---

### Step 2 — Inspect the UAT Site's Source Code

Navigate to `http://uat-testing.marvenly.com` in the browser and open the page source (`Ctrl+U`).

Inside the HTML, there's a comment left by the developer referencing their GitHub profile. The username is visible directly in the source code — the developer didn't clean up their dev notes before leaving the site live.

This is a classic mistake: comments and metadata that are harmless in a local dev environment become intelligence leaks the moment the code goes anywhere public-facing.

**Answer to Q2:** *[GitHub username found in page source — visible on the UAT site]*

---

### Step 3 — Find the Developer's Repository on GitHub

Search for `marvenly` on GitHub. Among the results, one repository stands out: **`marvenly_site`**.

This is the source code repository for the site. Even though the developer removed files from the repository, the **commit history is still there**. Git tracks every change ever made — deletions included. If something was ever committed, it can be recovered.

Clone the repository locally for deeper inspection:

```bash
git clone https://github.com/<username>/marvenly_site
cd marvenly_site
git log --oneline
```

`git log` shows the full commit history with messages. This is where the story starts coming together.

---

### Step 4 — Extract the Developer's Email from Commit Metadata

Git commits contain author metadata: name, email, and timestamp. Even if someone scrubs the files, the commit metadata remains.

The trick here is appending `.patch` to any commit URL on GitHub:

```
https://github.com/<username>/marvenly_site/commit/<COMMIT_HASH>.patch
```

This outputs the raw patch format, which includes the `From:` header with the author's email address — something not shown by default in the GitHub web interface.

Alternatively in the terminal:

```bash
git log --format="%ae" | sort -u
# or
git show <commit_hash> --format="%ae"
```

**Answer to Q3:** *[Email visible in commit patch metadata]*

---

### Step 5 — Read the Commit Messages for the Reason Code Was Removed

Reviewing commit messages with `git log`:

```bash
git log --oneline
```

One commit message directly explains why the source code was pulled from the repository. The developer cited a **payment dispute** — the project was abandoned because the client and developer had a falling out over payment.

```bash
git show <commit_hash>
```

This shows the full diff of that commit, including what was removed and the message explaining it.

**Answer to Q4:** *Payment dispute — project abandoned*

---

### Step 6 — Recover the Hidden Flag from Git History

Even though the developer deleted files from the repository, those files exist in earlier commits. Git's design principle is that **history is permanent by default** — deleting a file from the working tree just removes it from the latest snapshot, not from the historical record.

To list all commits and their changes:

```bash
git log --all --oneline
git show <early_commit_hash>
```

Or to see a specific deleted file's content from an earlier commit:

```bash
git checkout <commit_hash> -- <filename>
```

Digging through the older commits reveals the hidden flag embedded in the removed source files.

**Answer to Q5:** *[Flag recovered from git commit history]*

---

## What I Actually Learned

### Deleted ≠ Gone (in Git)

This is the biggest takeaway from this room. Git is designed to be an append-only history system. When a developer runs `git rm` and commits the deletion, the file disappears from the current state of the repo — but every previous commit still holds the full file content. Anyone with access to the repository (including public repos) can walk back through history and retrieve anything that was ever committed.

The practical implication: **sensitive data committed to a public repo is permanently compromised.** API keys, passwords, email addresses, private configuration files — if they were ever in a commit, they need to be considered leaked. Rotating secrets is the only fix.

### Certificate Transparency Logs Are a Recon Goldmine

crt.sh logs every SSL certificate issued publicly. This means every subdomain that ever got a certificate is findable — including dev, staging, UAT, and internal environments that were "private." Security teams use this for their own asset discovery; attackers use it for reconnaissance. Knowing it exists and how to query it is table stakes for web recon.

### Source Code Comments Are Intelligence

The developer left a GitHub username in an HTML comment on a UAT page. This is something that happens constantly in real engagements — developers leave TODO comments, internal URLs, database connection strings (in older codebases), and personal identifiers in code that eventually makes it to a public-facing server.

During web security assessments, reading the page source (and the JavaScript files) carefully is never optional. It's one of the first things to do.

### The `.patch` Trick for Git Email Extraction

Appending `.patch` to a GitHub commit URL is a technique I'll carry forward. The raw patch format exposes metadata that GitHub's normal web interface doesn't surface — specifically, the `From:` header with the committer's email. This is useful for attribution in OSINT investigations and for understanding who actually made a change in a codebase.

### Development Environments Are High-Value Targets

UAT and staging environments consistently appear in real-world vulnerability reports because:
- They often run older, unpatched versions of software
- Authentication is frequently weaker (or absent)
- They may point to the same backend databases as production
- They expose development artifacts that production scrubs

Finding `uat-testing.marvenly.com` and it still being live while the main domain was unreachable is a textbook example of this.

### OSINT is a Methodology, Not a Single Tool

The solution to this room wasn't one tool. It was a chain:

```
Domain → crt.sh (subdomain discovery) → UAT site → page source → GitHub username
→ Repository → commit history → .patch metadata → email
→ old commit diffs → deleted files → flag
```

Each step informed the next. This is how real OSINT investigations work — you follow threads, not blast a single scanner at a target.

---

## Tools & Techniques Used

| Tool / Technique | Purpose |
|-----------------|---------|
| [crt.sh](https://crt.sh) | Certificate transparency log search for subdomains |
| `subfinder` | Automated subdomain enumeration |
| Browser Page Source (`Ctrl+U`) | Finding developer comments in HTML |
| `git clone` | Downloading the repository locally |
| `git log --oneline` | Reviewing commit history and messages |
| `git show <hash>` | Inspecting specific commit changes |
| `.patch` URL trick | Extracting author email from commit metadata |
| `git checkout <hash> -- <file>` | Recovering deleted files from git history |

---

## Key Concepts to Remember

| Concept | What It Means |
|---------|--------------|
| Certificate Transparency (CT) | Public log of all issued SSL certs — every subdomain leaves a trace |
| Git History Permanence | Committed data is never truly deleted from a repo |
| UAT/Staging Exposure | Dev environments often live past their usefulness, less secured |
| Known Plaintext in Source | Comments, usernames, and references left in client-side code |
| OSINT Chain | Intelligence gathering works iteratively — each find opens the next |

---

## Related Rooms

- [Offensive Security Intro](https://tryhackme.com/room/offensivesecurityintrokK) — broader context on recon methodology
- [DNS in Detail](https://tryhackme.com/room/dnsindetail) — understanding the DNS layer that subdomains live on
- [How Websites Work](https://tryhackme.com/room/howwebsiteswork) — the web architecture context behind what this room exploits

---

*Completed May 2026 · Documented for personal reference and portfolio*
