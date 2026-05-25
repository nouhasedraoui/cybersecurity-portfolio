# W1seGuy — TryHackMe Room

**Room:** [W1seGuy](https://tryhackme.com/room/w1seguy)  
**Category:** Cryptography  
**Difficulty:** Easy  
**Flags:** 2  
**Completed:** May 2026  
**Score:** 16,193 (BOTSv1 session) — *(W1seGuy itself: both flags captured, key found manually via CyberChef)*

---

## What This Room Is Actually About

The room gives you a Python source file and a server listening on port 1337. When you connect, it sends you a hex-encoded XOR-encrypted string and asks you: *"What is the encryption key?"* Give it the right key and you get the second flag. That's it.

But the whole point isn't just to get the flags — it's to understand *why* this encryption is breakable without bruteforcing blindly. The moment I read the source code, everything clicked.

---

## Understanding the Source Code

The server-side script does the following:

```python
flag = open('flag.txt', 'r').read().strip()

def setup(server, key):
    xored = ""
    for i in range(0, len(flag)):
        xored += chr(ord(flag[i]) ^ ord(key[i % len(key)]))
    hex_encoded = xored.encode().hex()
    return hex_encoded

def start(server):
    res = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    key = str(res)
    hex_encoded = setup(server, key)
    send_message(server, "This XOR encoded text has flag 1: " + hex_encoded + "\n")
    send_message(server, "What is the encryption key? ")
    key_answer = server.recv(4096).decode().strip()
    if key_answer == key:
        send_message(server, "Congrats! Here is flag 2: " + flag + "\n")
```

Three things that matter here:

1. **The key is exactly 5 characters long** — randomly generated from letters and digits each session.
2. **The key repeats** — `i % len(key)` means if the flag is longer than 5 characters, the key wraps and starts over.
3. **The output is hex-encoded** — so the ciphertext we receive needs to be decoded from hex first.

---

## The Attack: Known Plaintext Attack (KPA)

This is where it gets interesting. XOR has a beautiful mathematical property:

```
Flag XOR Key = Ciphertext
Ciphertext XOR Flag = Key       ← this is the one we exploit
Ciphertext XOR Key = Flag
```

The key insight is: **we already know part of the flag before we even start.**

TryHackMe flags always begin with `THM{` and end with `}`. That's 5 known characters — which is *exactly* the length of the key.

So if we take the first 4 bytes of the ciphertext and XOR them against `T`, `H`, `M`, `{` one by one, we get the first 4 characters of the key directly. The 5th character can be found using the closing `}` at the last byte.

No bruteforce needed when you think about it this way.

---

## The Walkthrough — CyberChef Method (No Scripts)

I followed the no-scripts approach using [CyberChef](https://gchq.github.io/CyberChef/), which made it much more visual.

### Step 1 — Connect to the server

```bash
nc <MACHINE_IP> 1337
```

The server responds with something like:

```
This XOR encoded text has flag 1: 2e390e30194b102f251d3f09370a1d0e4520200a3b1f317808163d3a233c08053a7b1c08090c3914
What is the encryption key?
```

Save that hex string. Don't close the connection.

### Step 2 — Recover the key via CyberChef

Open CyberChef and build this recipe:

```
From Hex → XOR (key: THM{, UTF8)
```

- Input: the full hex string from the server
- XOR key: `THM{`
- Encoding: UTF8

The first 4 output characters are the first 4 characters of the encryption key.

For my session that was: `zqCK`

### Step 3 — Find the 5th key character

The flag ends with `}`. The last byte of the ciphertext XOR'd with `}` gives the last key character.

Take just the last 2 hex characters of the ciphertext (1 byte), run it through CyberChef:

```
From Hex → XOR (key: }, UTF8)
```

That gave me: `i`

Full key: **`zqCKi`**

### Step 4 — Verify: decrypt the full flag

Back in CyberChef:

```
From Hex → XOR (key: zqCKi, UTF8)
```

The decrypted output is Flag 1.

### Step 5 — Send the key to the server

Back in the terminal where you left the netcat connection open:

```
zqCKi
```

The server responds with:

```
Congrats! That is the correct key! Here is flag 2: THM{BrUt3_ForC1nG_XOR_cAn_B3_FuN_nO?}
```

---

## What I Actually Learned

### XOR is reversible — and that's the problem

The entire attack works because XOR is its own inverse. There's no one-way function here, no hashing, no key derivation. If you know even a slice of the plaintext, you can pull out the key. And in CTFs, the plaintext format (`THM{...}`) is always known. In real-world scenarios, HTTP headers, file magic bytes, or protocol prefixes serve the same purpose.

### Short repeating keys = Vigenère cipher, dressed up

This is exactly what the Vigenère cipher from the 1500s did — except instead of letter shifting, we're using XOR on ASCII values. The weakness is identical: once you know the key length and have any known plaintext, the cipher collapses. Charles Babbage figured this out in the 19th century. The room is essentially a modern re-run of that same attack.

### The `%` operator is what makes it repeat

`key[i % len(key)]` — this single line is responsible for the weakness. It ensures the key cycles. Without it (if the key was as long as the flag, used only once), this would be a One-Time Pad and mathematically unbreakable. With it, it's predictably weak.

### Source code review is part of the job

This room gave us the source code deliberately, but in real engagements, source code often leaks through exposed Git repositories, misconfigured servers, or JavaScript bundles. The habit of reading code before touching the target is something I want to carry forward.

### Linux `rev` command

Didn't expect to learn a terminal trick from a crypto room, but the `rev` command came up here. It's the shell equivalent of that JavaScript `RevereString` function:

```bash
echo "54321@terceSrepuS" | rev
# Output: SuperSecret@12345
```

Useful for quick string reversal without writing a script.

---

## Key Concepts to Remember

| Concept | What It Means |
|---------|--------------|
| XOR (^) | Bitwise Exclusive OR — output is 1 only if inputs differ |
| Known Plaintext Attack | Using a known portion of the original message to recover the key |
| Repeating XOR Key | Identical weakness to Vigenère cipher — short key cycles over long plaintext |
| One-Time Pad | Theoretically unbreakable XOR where key = message length, used once only |
| CyberChef | Browser-based Swiss Army knife for encoding, decoding, and crypto ops |

---

## Tools Used

- `netcat` — TCP connection to the challenge server
- [CyberChef](https://gchq.github.io/CyberChef/) — hex decoding and XOR operations
- `rev` (Linux) — quick string reversal in terminal

---

## Related Rooms

- [Cryptography Concepts](https://tryhackme.com/room/cryptographyconcepts) — foundation for understanding what happened here
- [Offensive Security Intro](https://tryhackme.com/room/offensivesecurityintrokK) — broader context on ethical hacking methodology

---

*Completed May 2026 · Documented for personal reference and portfolio*
