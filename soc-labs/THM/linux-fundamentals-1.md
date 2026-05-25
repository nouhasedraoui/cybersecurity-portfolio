# Linux Fundamentals Part 1 - TryHackMe Room

**Room:** [Linux Fundamentals Part 1](https://tryhackme.com/room/linuxfundamentalspart1)  
**Category:** Linux / Fundamentals  
**Difficulty:** Easy  
**Completed:** May 2026

---

## What This Room Is Actually About

This is the starting point for anyone getting serious about Linux. And in security, that means everyone. Whether you are doing forensics, running penetration tests, analyzing malware, or just using Kali, you live in the terminal. This room strips everything back and builds from zero: what Linux is, how to navigate the filesystem, how to find things, and how shell operators let you chain commands together in ways that become second nature over time.

I ran every command in the terminal as I went through the room rather than just reading. That is the only way any of this sticks.

---

## Task 2 - A Bit of Background on Linux

### Where Linux Actually Lives

Linux is not just a server OS. It is everywhere:

- Websites and web servers (most of the internet runs on Linux)
- Android phones (the kernel is Linux-based)
- Smart car entertainment and control systems
- Point of Sale terminals and checkout registers
- Traffic light controllers and industrial sensors
- Supercomputers (literally all of the top 500 run Linux)

The reason it is so widespread is that Linux is open-source and extremely lightweight. Ubuntu Server can run on as little as 512MB of RAM, which makes it deployable in environments where Windows would be completely impractical.

### Distributions ("Distros")

Linux is technically an umbrella term. The core is the Linux kernel, and different organizations build operating systems on top of it. These are called distributions:

- **Ubuntu / Debian** - most common for general use and servers
- **Kali Linux** - built for penetration testing, pre-loaded with security tools
- **Parrot OS** - another security-focused distro
- **Fedora / Arch** - popular in the developer community

For this room, the machine used is Ubuntu.

**First release of Linux:** 1991, by Linus Torvalds

---

## Task 4 - Running Your First Commands

The terminal is text-only. No icons, no mouse required. At first it feels limiting. After a while it feels like a superpower, because text commands are fast, scriptable, and repeatable.

Two foundational commands to start:

### `echo`

Outputs text to the screen. The equivalent of `print` in Python.

```bash
echo Hello
# Output: Hello

echo "Hello Friend!"
# Output: Hello Friend!
```

Single words do not need quotes. If there are spaces, wrap in double quotes.

### `whoami`

Tells you which user you are currently logged in as.

```bash
whoami
# Output: tryhackme
```

This one shows up constantly in CTF writeups because the first thing you want to confirm after getting a shell is what user you are running as.

---

## Task 5 - Interacting With the Filesystem

This is where the room gets genuinely useful. Four commands that you will use every single time you open a terminal:

### `ls` - List

Shows what files and folders exist in the current directory.

```bash
ls
# Output: 'Important Files'  'My Documents'  Notes  Pictures
```

Pro tip: you can check the contents of any directory without navigating into it first:

```bash
ls Pictures
# Output: dog_picture1.jpg  dog_picture2.jpg  dog_picture3.jpg  dog_picture4.jpg
```

### `cd` - Change Directory

Moves you into a different directory.

```bash
cd Pictures
# Now you are inside the Pictures folder

cd ..
# Goes back up one level

cd /home/tryhackme/folder4
# Goes directly to a path regardless of where you currently are
```

### `cat` - Concatenate

Outputs the contents of a file directly to the terminal.

```bash
cat todo.txt
# Output: Here's something important for me to do later!
```

You can also cat a file using its full path without navigating to it first:

```bash
cat /home/ubuntu/Documents/todo.txt
```

In security contexts, `cat` is how you read config files, log files, flag files, and anything stored as text. Credentials, flags, API keys left in plain text files, all retrieved with `cat`.

### `pwd` - Print Working Directory

Shows your exact current location in the filesystem as a full path.

```bash
pwd
# Output: /home/ubuntu/Documents
```

When you are navigating deep into a filesystem structure and lose track of where you are, `pwd` is how you get your bearings back.

### Room Challenge Answers (Task 5)

The deployed machine had 4 folders in the home directory. Checking each one with `ls` revealed that **folder4** contained a file. Running `cat` on that file returned `Hello World!`. After navigating into folder4 with `cd`, running `pwd` confirmed the path: `/home/tryhackme/folder4`.

---

## Task 6 - Searching for Files

Navigating with `ls` and `cd` works fine when you know roughly where things are. When you have no idea, or when the filesystem is large, you need tools that search for you.

### `find` - Find Files by Name

Searches recursively from the current directory for a file matching the name you give it.

```bash
find -name passwords.txt
# Output: ./folder1/passwords.txt
```

Using a wildcard to find all files with a specific extension:

```bash
find -name *.txt
# Output:
# ./folder1/passwords.txt
# ./Documents/todo.txt
```

The `*` matches anything, so `*.txt` means "any filename that ends in .txt". This is how you quickly locate all log files, all config files, or all text files on a system without manually checking every folder.

### `grep` - Search File Contents

While `find` locates files by name, `grep` searches inside files for specific text.

```bash
grep "81.143.211.90" access.log
# Output: 81.143.211.90 - - [25/Mar/2021:11:17 +0000] "GET / HTTP/1.1" 200 417 "-" "Mozilla/5.0..."
```

In this example, `access.log` had 244 entries. Reading through all of them with `cat` to find one IP address would be painful. `grep` finds it instantly.

The `-R` flag makes grep search recursively through all files in a directory and its subdirectories:

```bash
grep -R "PRETTY_NAME" /etc/
# Output: /etc/os-release:PRETTY_NAME="Ubuntu"
```

This is extremely useful in security work: searching an entire server for a specific config value, a password pattern, or a string that should not be there.

### Room Challenge Answer (Task 6)

Running `grep "THM" access.log` on the file in `/home/tryhackme/` returned the flag: `THM{ACCESS}`

---

## Task 7 - Shell Operators

Shell operators are what turn individual commands into actual workflows. Four operators that matter:

### `&` - Background Execution

Runs a command in the background so you can keep using the terminal while it runs.

```bash
cp large_file.tar.gz /backup/ &
```

Without the `&`, the terminal hangs until the copy finishes. With it, you get the prompt back immediately and the copy runs behind the scenes.

### `&&` - Sequential Execution (Conditional)

Runs two commands in sequence, but only runs the second if the first succeeds.

```bash
mkdir newfolder && cd newfolder
```

If `mkdir` fails (because the folder already exists, or permissions are denied), `cd` never runs. This is safer than just putting commands on separate lines, because it prevents you from acting on a failed state.

### `>` - Output Redirect (Overwrite)

Takes the output of a command and writes it to a file instead of the terminal. Overwrites any existing content.

```bash
echo hey > welcome
cat welcome
# Output: hey
```

If `welcome` already exists and had content in it, that content is gone. Replaced entirely.

```bash
echo password123 > passwords
```

### `>>` - Output Redirect (Append)

Same as `>` but adds to the end of the file instead of replacing it.

```bash
echo hello >> welcome
cat welcome
# Output:
# hey
# hello
```

Both lines are now in the file. The original content was preserved.

```bash
echo tryhackme >> passwords
```

Now `passwords` contains both `password123` and `tryhackme`, one per line.

### Practical Example - Saving Command Output

This pattern shows up constantly in security workflows:

```bash
nmap -sV 10.10.10.10 > scan_results.txt
nmap -sC 10.10.10.10 >> scan_results.txt
```

First scan goes to a new file. Second scan gets appended to the same file. You now have all results in one place without running one big command.

---

## What I Actually Learned

### The terminal is not intimidating once you have the basics

The first few commands (`ls`, `cd`, `cat`, `pwd`) cover a huge percentage of what you actually do on a day-to-day basis in a terminal. The intimidation comes from not knowing where to start. Once you have those four commands, you can navigate basically any Linux system.

### `grep` is one of the most useful tools in security

Searching log files is a huge part of SOC work and forensics. `grep` does that search in seconds against files that would take hours to read manually. Combining it with `-R` for recursive search means you can hunt through entire directory trees for a specific string. In real investigations I use it to search for specific IP addresses, usernames, or error codes across log directories.

### `find` vs `grep`

Easy way to remember the difference: `find` locates files by their name or properties. `grep` searches inside files for content. You often chain them together:

```bash
find /var/log -name "*.log" | xargs grep "Failed password"
```

Find all log files, then search all of them for failed login attempts.

### `>` vs `>>` is a trap

I have seen people accidentally wipe files by using `>` when they meant `>>`. The distinction matters and it is easy to mix up when you are working fast. If you are unsure, always use `>>` first, then check the file. You can always clean up duplicates. You cannot recover overwritten data without backups.

### Shell operators make workflows composable

`&&` in particular changes how you think about chaining commands. Instead of running each command and checking if it worked before running the next one manually, you let the shell do that check for you. This is the beginning of thinking in scripts rather than just typing commands one at a time.

### Linux powers the infrastructure security is meant to protect

Every web server I will interact with as a security engineer is almost certainly running Linux. Every Docker container runs on a Linux kernel. Every cloud VM defaults to Linux. Learning this is not just about passing rooms on TryHackMe. It is about being able to actually navigate the systems I will be assessing, hardening, or responding to incidents on.

---

## Quick Reference Card

```bash
# Navigation and filesystem
ls                    # list files in current directory
ls foldername         # list files in specific folder without navigating
cd foldername         # move into a directory
cd ..                 # go up one level
cd /full/path         # go directly to any path
pwd                   # print full path of current directory
cat filename          # output contents of a file
cat /full/path/file   # output file using full path

# Searching
find -name filename   # find file by exact name
find -name *.ext      # find all files with extension
grep "text" file      # search for text inside a file
grep -R "text" /path  # search recursively through all files in directory

# Shell operators
command &             # run in background
cmd1 && cmd2          # run cmd2 only if cmd1 succeeds
echo text > file      # write to file (overwrites)
echo text >> file     # append to file (keeps existing content)

# First commands
echo "text"           # print text to screen
whoami                # show current username
```

---

## Tools Used

- TryHackMe AttackBox / deployed Ubuntu machine
- Browser-based Linux terminal

---

## Related Rooms

- [Linux Fundamentals Part 2](https://tryhackme.com/room/linuxfundamentalspart2) - direct continuation of this room
- [Linux Fundamentals Part 3](https://tryhackme.com/room/linuxfundamentalspart3) - completes the series
- [Bash Scripting](https://tryhackme.com/room/bashscripting) - puts these commands to work inside scripts

---

*Completed May 2026 - Documented for personal reference and portfolio*
