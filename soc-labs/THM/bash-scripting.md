# Bash Scripting — TryHackMe Room

**Room:** [Bash Scripting](https://tryhackme.com/room/bashscripting)  
**Category:** Scripting / Linux  
**Difficulty:** Easy  
**Completed:** May 2026

---

## What This Room Is Actually About

Bash is everywhere in security work. Every time you automate a scan, loop through a list of targets, or chain tools together in a pipeline, you're writing bash. This room covers the core building blocks: scripts, variables, parameters, arrays, and conditionals — and puts them together into small working programs by the end.

It's a walkthrough room, meaning it teaches while you do. I tested every example in my own terminal rather than just reading through it, which made a big difference in how well things stuck.

Reference I kept open throughout: [https://devhints.io/bash](https://devhints.io/bash) — it's the best bash cheatsheet I've found.

---

## Task 2 — First Scripts & The Shebang

Every bash script starts with this line:

```bash
#!/bin/bash
```

This is called the **shebang** (or hashbang). It tells the system which interpreter to use when running the file — in this case, bash located at `/bin/bash`. Without it, the shell might try to execute the file with a different interpreter and things break in unexpected ways.

After that, you can run any Linux command you'd normally type in the terminal:

```bash
#!/bin/bash
echo "Hello World"
whoami
id
ls
```

To make the script executable and run it:

```bash
chmod +x myscript.sh
./myscript.sh
```

### Comments

Anything after a `#` on a line is a comment — the interpreter ignores it:

```bash
# This is a comment
echo "This runs"  # This part is also a comment
```

### Debugging Mode

This one is genuinely useful and I'd never really used it before:

```bash
bash -x ./myscript.sh
```

Running with `-x` prints every command before it executes, with a `+` prefix. If a line fails, you see a `-`. You can also scope it inside your script:

```bash
set -x   # start debug
echo "debug this section"
set +x   # stop debug
```

This saves a lot of time when a script isn't behaving the way you expect.

---

## Task 3 — Variables

Variables in bash are simple but have one strict rule: **no spaces around the `=`**. This is probably the most common beginner mistake.

```bash
name="Nouha"       # correct
name = "Nouha"     # WRONG — bash sees "name" as a command
```

To use a variable, prefix it with `$`:

```bash
name="Nouha"
age=21
city="Ariana"
country="Tunisia"

echo "$name is $age years old"
echo "City: $city, Country: $country"
```

Output:
```
Nouha is 21 years old
City: Ariana, Country: Tunisia
```

You can mix multiple variables in a single echo statement without any issue. The `$` is what tells bash "this is a variable, expand it."

### Why Variables Matter in Security Scripts

In real automation scripts — port scanners, log parsers, report generators — you'll use variables constantly. Hardcoding an IP address or a filename in 20 places and then having to change it is painful. Putting it in a variable at the top means one change, done.

---

## Task 4 — Parameters

Parameters let you pass input to a script from the command line, making it reusable instead of hardcoded.

```bash
#!/bin/bash
name=$1
echo "Hello, $name"
```

Running:
```bash
./script.sh Nouha
# Output: Hello, Nouha
```

| Special Variable | What It Gives You |
|-----------------|-------------------|
| `$1`, `$2`, `$3`... | Positional arguments (1st, 2nd, 3rd...) |
| `$0` | The script's own filename |
| `$#` | The number of arguments passed |
| `$@` | All arguments as a list |

So if you run `./script.sh hello hola aloha`:
- `$1` = `hello`
- `$3` = `aloha`
- `echo $1 $3` outputs: `hello aloha`

### Interactive Input with `read`

Instead of passing arguments on the command line, you can prompt the user:

```bash
#!/bin/bash
echo "What is your name?"
read name
echo "Hello, $name"
```

The script pauses and waits for you to type. Whatever you enter gets stored in `name`. This is useful for scripts that need interactive confirmation or multi-step input.

To read into a variable called `test`:
```bash
read test
```

### Building a Biography Script

The room suggests building a small biography maker as a practice exercise. Here's what I put together:

```bash
#!/bin/bash
name=$1
age=$2
job=$3

echo "Name: $name"
echo "Age: $age"
echo "Job: $job"
echo "---"
echo "$name is $age years old and works as a $job."
```

Run with: `./bio.sh Nouha 22 "Security Engineer"`

---

## Task 5 — Arrays

Arrays store multiple values in a single variable, accessed by index position. All indexes start at **0**.

```bash
transport=('car' 'train' 'bike' 'bus')
```

| Item | Index |
|------|-------|
| car | 0 |
| train | 1 |
| bike | 2 |
| bus | 3 |

### Common Operations

```bash
# Print all elements
echo "${transport[@]}"

# Print a specific element (train = index 1)
echo "${transport[1]}"

# Remove an element
unset transport[1]

# Replace/add an element
transport[1]='trainride'

# Print the total number of elements
echo "${#transport[@]}"
```

### The `@` and `[]` Syntax

The `@` means "all elements." The `[]` specifies the index. Combined: `${transport[@]}` gives you the whole array. `${transport[2]}` gives you just the item at position 2.

### Practical Example with the `cars` Array

```bash
cars=('honda' 'audi' 'bmw' 'tesla')

echo "${cars[1]}"       # prints: audi
unset cars[3]           # removes tesla
cars[3]='toyota'        # replaces tesla with toyota
```

### Why Arrays Matter in Security Work

Arrays are how you handle lists in bash — lists of IP addresses to scan, lists of wordlist entries, lists of found subdomains. Without arrays you're stuck writing one variable per item, which doesn't scale at all.

---

## Task 6 — Conditionals

Conditionals are the decision-making part of any script. An `if` statement runs a block of code only when a condition is true.

### Basic Syntax

```bash
if [ condition ]; then
    # code runs if condition is true
else
    # code runs if condition is false
fi
```

The spaces inside `[ ]` are **required** in bash. `[-eq` without the space before `]` will throw an error.

Every `if` must end with `fi` (if backwards).

### Comparison Operators

| Operator | Meaning |
|----------|---------|
| `-eq` | Equal to (numbers) |
| `-ne` | Not equal to |
| `-gt` | Greater than |
| `-lt` | Less than |
| `-ge` | Greater than or equal to |
| `-le` | Less than or equal to |
| `=` | Equal to (strings) |

### File Test Flags

These are the ones I found most immediately useful for real scripting:

| Flag | Checks |
|------|--------|
| `-f` | File exists and is a regular file |
| `-d` | Is a directory |
| `-r` | File has read permission |
| `-w` | File has write permission |
| `-x` | File has execute permission |
| `-e` | File or directory exists |

The answers to the room questions:
- Flag to check read access: `-r`
- Flag to check for directory: `-d`

### A Guessing Game Script

```bash
#!/bin/bash
if [ "$1" = "guessme" ]; then
    echo "They are equal"
else
    echo "They are not equal"
fi
```

Run with:
```bash
./example.sh guessme   # → They are equal
./example.sh hi        # → They are not equal
```

### A Practical File Handler Script

This one combines two conditions — checking if a file exists (`-f`) AND if it's writable (`-w`):

```bash
#!/bin/bash
if [ -f $1 ] && [ -w $1 ]; then
    echo "hello" >> $1
else
    touch $1
    echo "hello" >> $1
fi
```

Run with:
```bash
./example.sh hello.txt
cat hello.txt
# Output: hello
```

If the file doesn't exist, it creates it. If it exists but isn't writable, it can be modified to handle that case too.

### Extended: Age Checker with `read`

Building on the earlier parameters work:

```bash
#!/bin/bash
echo "Enter your name:"
read name
echo "Enter your age:"
read age

if [ $age -lt 18 ]; then
    echo "$name, you are not eligible for work."
else
    echo "Welcome $name! What is your job?"
    read job
    echo "$name works as a $job."
fi
```

This combines variables, `read` for interactive input, and conditionals — basically everything from the room in one script.

---

## What I Actually Learned

### The shebang is not optional

Skipping `#!/bin/bash` doesn't always break things — sometimes the system defaults to bash anyway. But sometimes it doesn't, and you get cryptic errors. Always include it. It takes two seconds and removes ambiguity entirely.

### Variable spacing is a bash-specific trap

Every other language I've touched lets you write `x = 5`. Bash doesn't. The `=` must be glued to both the variable name and the value. Getting burned by this once is enough to never forget it.

### `-x` debug mode is genuinely useful

Before this room I was debugging bash by adding `echo` statements everywhere. Running `bash -x script.sh` and seeing every line execute in real time is significantly better. It shows you the actual values being substituted into variables, which is where most bugs hide.

### File test flags are useful far beyond CTFs

In real security work: checking if a log file exists before trying to parse it, checking if an output directory is writable before running a scan, checking if a tool's binary exists before calling it. These `-f`, `-r`, `-w`, `-d` flags come up constantly.

### Arrays replace messy variable naming

Without arrays, handling 10 IP addresses means `ip1`, `ip2`, `ip3`... With an array it's `ips[0]` through `ips[9]`, and you can loop over the whole thing with `${ips[@]}`. Much cleaner.

### Bash automation is a multiplier

Every manual, repetitive task in security — generating reports, running the same nmap flags against a list of hosts, checking if certain ports are open across a range — can be scripted. This room is the foundation for all of that.

---

## Quick Reference Card

```bash
#!/bin/bash                    # always first line

# Variables
name="value"                   # declare (no spaces around =)
echo $name                     # use

# Parameters
$0   # script name
$1   # first argument
$#   # number of arguments
$@   # all arguments

# Read input
read varname

# Arrays
arr=('a' 'b' 'c')
echo "${arr[@]}"               # all elements
echo "${arr[1]}"               # element at index 1
unset arr[2]                   # remove element
arr[2]='new'                   # replace element

# Conditionals
if [ $x -eq 10 ]; then
    echo "equal"
elif [ $x -gt 10 ]; then
    echo "greater"
else
    echo "less"
fi

# File tests
[ -f file ]    # is a file
[ -d dir ]     # is a directory
[ -r file ]    # readable
[ -w file ]    # writable
[ -x file ]    # executable

# Debug
bash -x ./script.sh
set -x  # start debug in script
set +x  # end debug in script
```

---

## Tools & Resources Used

- Kali Linux terminal — testing all examples live
- [devhints.io/bash](https://devhints.io/bash) — the reference I kept open throughout
- TryHackMe AttackBox — for running the room exercises

---

## Related Rooms

- [Linux Fundamentals Part 1](https://tryhackme.com/room/linuxfundamentalspart1) — prerequisite the room itself recommends
- [Python Basics](https://tryhackme.com/room/pythonbasics) — similar scripting foundations in Python

---

*Completed May 2026 · Documented for personal reference and portfolio*
