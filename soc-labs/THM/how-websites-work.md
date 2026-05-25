# How Websites Work - TryHackMe Room

**Room:** [How Websites Work](https://tryhackme.com/room/howwebsiteswork)  
**Category:** Web / Pre-Security  
**Difficulty:** Easy  
**Completed:** May 2026

---

## What This Room Is Actually About

Before you can exploit a website, you need to understand what it is made of. This room is the foundation layer: how a browser and server communicate, what HTML and JavaScript actually do, and how two of the most common beginner-level web vulnerabilities work in practice. Sensitive data exposure and HTML injection both come up in real-world assessments. Seeing them in a controlled lab first makes them much easier to recognize later.

---

## Task 1 - How Websites Work (The Big Picture)

When you visit any website, two things are happening simultaneously:

**Frontend (Client-Side):** What your browser downloads and renders. HTML for structure, CSS for styling, JavaScript for behavior. All of this runs inside the user's browser. The user can see and interact with all of it.

**Backend (Server-Side):** The server that processes your request and sends back the response. This could be a database, application logic, authentication systems. The user cannot see this directly.

The critical security implication is built into this model from the start: **anything that runs on the client side is accessible to the user**. JavaScript code, HTML comments, hardcoded values in source files - all of it. This is what makes client-side security mistakes so costly.

The answer to the first room question: the component rendered by the browser is the **Front End**.

---

## Task 2 - HTML

HTML (HyperText Markup Language) is the skeleton of every webpage. It defines the structure and content using elements called tags.

### Basic HTML Structure

```html
<!DOCTYPE html>
<html>
    <head>
        <title>Page Title</title>
    </head>
    <body>
        <h1>This is a heading</h1>
        <p>This is a paragraph</p>
        <img src="img/cat.jpg">
        <button>Click me</button>
    </body>
</html>
```

Key components:

| Tag | Purpose |
|-----|---------|
| `<!DOCTYPE html>` | Tells the browser this is HTML5 |
| `<html>` | Root element, everything goes inside it |
| `<head>` | Page metadata (title, scripts, stylesheets) - not displayed |
| `<body>` | Everything visible on the page goes here |
| `<h1>` to `<h6>` | Headings, h1 being the largest |
| `<p>` | Paragraph |
| `<img src="...">` | Image with its source path |
| `<a href="...">` | Hyperlink |

### Attributes

Tags can carry attributes that modify their behavior:

```html
<p class="bold-text">Styled paragraph</p>
<img src="img/cat.jpg">
<p id="unique-element">This has a unique identifier</p>
```

- `class` can be shared by multiple elements and used for CSS styling
- `id` must be unique per element, used for JavaScript targeting and CSS
- `src` tells an image tag where to find the image file

### Room Challenge - Broken Image Fix

The cat website had a broken image. Viewing the source revealed the `src` attribute was pointing to the wrong path. Fixing the path revealed the hidden text: **HTMLHERO**

Adding a dog image on line 11:

```html
<img src="img/dog-1.png">
```

The text in the dog image: **DOGHTML**

### How to View Page Source

Right-click any webpage and choose **View Page Source** (Chrome) or **Show Page Source** (Safari). This is always one of the first things to do when assessing a web application. Developers leave more in there than they should.

---

## Task 3 - JavaScript

JavaScript (JS) is what makes websites interactive. Where HTML defines what is on the page and CSS defines how it looks, JavaScript defines what it does.

### How JavaScript Gets Added to a Page

Either inline inside `<script>` tags:

```html
<script>
    document.getElementById("demo").innerHTML = "Hack the Planet";
</script>
```

Or loaded from an external file:

```html
<script src="/location/of/script.js"></script>
```

### DOM Manipulation

JavaScript interacts with the page through the DOM (Document Object Model). The DOM is the live representation of the HTML that JavaScript can read and modify.

```javascript
// Find an element by its ID and change its content
document.getElementById("demo").innerHTML = "Hack the Planet";
```

This finds the HTML element with `id="demo"` and replaces whatever was inside it with the string "Hack the Planet".

### Events

HTML elements can trigger JavaScript when the user does something:

```html
<button onclick='document.getElementById("demo").innerHTML = "Button Clicked";'>
    Click Me!
</button>
```

When the button is clicked, the `onclick` event fires and runs the JavaScript inside the quotes. Events can also be defined entirely within `<script>` tags rather than directly on elements.

### Room Challenge - JS Answers

Task asks you to add JavaScript that changes the `demo` element's content to `"Hack the Planet"`:

```javascript
document.getElementById("demo").innerHTML = "Hack the Planet";
```

Flag received: **JSISFUN**

---

## Task 4 - Sensitive Data Exposure

This task introduces one of the most straightforward vulnerabilities in web security: developers leaving sensitive information in client-side code.

### What It Is

Because HTML and JavaScript are downloaded by the browser, anyone who views the page source can read everything in those files. If a developer has left credentials, API keys, hidden links, or any other sensitive data in comments or variables, they are visible to every visitor.

Common forms this takes:

- HTML comments containing credentials (`<!-- username: admin, password: letmein -->`)
- Hardcoded passwords in JavaScript functions (like CyberHeroes)
- Internal endpoint URLs left in comments
- API keys or tokens stored in frontend JavaScript files
- Configuration values that should only exist server-side

### Room Challenge

The task linked to a specific page and asked to find the password hidden in the source. Right-clicking and choosing **View Page Source** revealed a multi-line HTML comment containing credentials:

```html
<!-- username: admin password: testpasswd -->
```

The password: **testpasswd**

### Why This Matters

This is not a theoretical issue. Developers push code under deadline pressure and forget to clean up debug comments, test credentials, or placeholder values. Public GitHub repositories are full of accidental secret commits. Security assessments consistently find API keys and credentials in JavaScript bundles on production websites.

The first thing any web security assessment should do is read the full page source before touching any other tool.

---

## Task 5 - HTML Injection

### What It Is

HTML Injection is a vulnerability that occurs when user input is placed directly into the page without being sanitized (cleaned of potentially malicious content). When the browser receives HTML, it renders it. So if a user can submit HTML and have it appear on the page, they can change how the page looks and behaves for anyone who sees it.

### How It Works

The vulnerable page had an input field. Whatever you typed would be passed to a JavaScript function and displayed on the page. Because the developer did not strip HTML tags from the input, you could type raw HTML and the browser would render it as actual page elements.

### The Payload

To create a malicious link to `http://hacker.com`:

```html
<a href="http://hacker.com">Click here</a>
```

Entering this into the input field and submitting it caused the link to appear on the page as a real, clickable hyperlink pointing to the attacker's site.

Flag: **HTML_INJ3CTI0N**

### The Difference Between HTML Injection and XSS

HTML injection lets you inject HTML elements. XSS (Cross-Site Scripting) takes it further by injecting JavaScript. Both share the same root cause: unsanitized user input being rendered by the browser. HTML injection is the simpler form, but the path from HTML injection to XSS is often short once you understand both.

### What Proper Sanitization Looks Like

The developer should strip or escape HTML tags from any user input before using it in the page. In JavaScript, this means converting characters like `<`, `>`, and `"` into their HTML entity equivalents (`&lt;`, `&gt;`, `&quot;`) so the browser displays them as text rather than interpreting them as markup.

The general rule: **never trust user input**. Anything coming from the user should be treated as potentially malicious until proven otherwise.

---

## What I Actually Learned

### The client-server split is the foundation of web security

Almost every web vulnerability maps back to this architecture. Client-side code is public. Server-side code is private. Anything that needs to be secret has to live on the server. The moment credentials, keys, or sensitive logic touch the frontend, they are exposed. Understanding this at a foundational level makes every web vulnerability easier to reason about.

### HTML is not just structure, it is an attack surface

A broken image tag, a missing attribute, an unescaped character in user input - these are all entry points. Viewing page source is not just a developer skill, it is a core recon step in web security testing.

### JavaScript is powerful and dangerous in equal measure

Because JavaScript runs in the browser with access to the DOM, cookies, and local storage, injecting JavaScript into a page gives an attacker significant control. The HTML injection task here is the beginner form of this idea. XSS and more complex client-side attacks follow the same logic at a deeper level.

### Comments in source code are visible to everyone

This should be obvious once stated, but developers routinely leave credentials, internal notes, disabled code blocks, and debug values in HTML comments or JavaScript. Viewing source should be automatic habit when doing any kind of web assessment.

### Input sanitization is not optional

The HTML injection task works because the developer assumed users would type their names. They did not account for users typing HTML. This failure of assumption is at the root of injection vulnerabilities of all types: SQL injection, command injection, XSS, HTML injection. The fix is always the same: validate and sanitize input before using it.

---

## Web Technology Quick Reference

```
Request Flow:
User types URL -> Browser sends HTTP request -> Server processes it
-> Server sends HTML/CSS/JS back -> Browser renders the page

HTML key tags:
<!DOCTYPE html>     document type declaration
<html>              root element
<head>              metadata (not displayed)
<body>              visible content
<h1> to <h6>        headings
<p>                 paragraph
<a href="url">      hyperlink
<img src="path">    image
<button>            clickable button
<script>            inline JavaScript
<script src="...">  external JavaScript file

JavaScript DOM:
document.getElementById("id")          find element by ID
element.innerHTML = "new content"       change element content
element.onclick = function() { ... }    attach click handler

Security Flags to Check During Web Testing:
- View page source (Ctrl+U)
- Look for HTML comments
- Look for hardcoded values in JS
- Test input fields for unsanitized output
- Check for external JS files that might contain secrets
```

---

## Tools Used

- Browser (View Page Source - `Ctrl+U`)
- Browser DevTools (F12)
- TryHackMe interactive site labs

---

## Related Rooms

- [Putting It All Together](https://tryhackme.com/room/puttingitalltogether) - completes the web fundamentals picture
- [HTTP in Detail](https://tryhackme.com/room/httpindetail) - digs deeper into the request and response cycle
- [CyberHeroes](https://tryhackme.com/room/cyberheroes) - applies the sensitive data exposure concept in a CTF format
- [Authentication Bypass](https://tryhackme.com/room/authenticationbypass) - next step from client-side auth failures

---

*Completed May 2026 - Documented for personal reference and portfolio*
