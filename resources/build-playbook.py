#!/usr/bin/env python3
"""Regenerate fullstack-playbook.html from FULLSTACK-PLAYBOOK.md.

This is a build-time dev tool only — the GitHub Pages site ships the
generated, self-contained HTML (no runtime dependencies).

Usage:
    python3 -m venv .venv && .venv/bin/pip install markdown
    .venv/bin/python resources/build-playbook.py

Edit FULLSTACK-PLAYBOOK.md (and re-export FULLSTACK-PLAYBOOK.docx for the
download button), then re-run this to refresh the reading page.

The page also has a "Copy LLM prompt" button. The copied text = a hands-on
guide preamble + the playbook with repo/workplace-specific blockquote
callouts stripped (so it's project-agnostic). It is embedded base64-encoded
so copy works offline. The on-page reading version keeps every callout.
"""
import os
import re
import base64
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "FULLSTACK-PLAYBOOK.md")
OUT = os.path.join(HERE, "fullstack-playbook.html")


def github_slugify(value, separator="-"):
    """Reproduce GitHub's heading-anchor algorithm so the document's own
    table-of-contents links (e.g. #75-input-validation-...) resolve."""
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)      # drop punctuation, keep word chars/space/hyphen
    value = value.replace(" ", separator)        # spaces -> hyphens (no collapsing)
    return value


def fix_nested_list_indent(text):
    """Python-Markdown nests lists at 4-space indents; the source TOC uses 3.
    Re-indent nested list *markers* (never code fences or paragraph
    continuations) so sub-lists nest properly."""
    out, in_fence = [], False
    for ln in text.split("\n"):
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            continue
        m = re.match(r"^( +)([-*+]|\d+\.)(\s)", ln)
        if not in_fence and m:
            indent = len(m.group(1))
            new_indent = (indent // 3) * 4  # 3->4, 6->8
            if new_indent != indent:
                ln = " " * new_indent + ln[indent:]
        out.append(ln)
    return "\n".join(out)


def strip_repo_callouts(text):
    """Remove blockquote callouts that reference the author's specific repo
    or workplace, so the copied LLM prompt is project-agnostic. General
    teaching blockquotes (e.g. "How to read this", "jsdom gotchas") are kept.
    The on-page reading version is rendered separately and keeps everything."""
    markers = ("in this repo", "reference repo", "city furniture")
    lines = text.split("\n")
    out, i, in_fence = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            i += 1
            continue
        if not in_fence and ln.startswith(">"):
            block, j = [], i
            while j < len(lines) and lines[j].startswith(">"):
                block.append(lines[j])
                j += 1
            blocktext = " ".join(re.sub(r"^>\s?", "", b) for b in block).lower()
            if any(m in blocktext for m in markers):
                if j < len(lines) and lines[j].strip() == "":
                    j += 1  # also drop one trailing blank line
                i = j
                continue
            out.extend(block)
            i = j
            continue
        out.append(ln)
        i += 1
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


def scrub_repo_prose(text):
    """Remove the few non-blockquote sentences that name the author's
    reference app, so the copied prompt references no specific project."""
    patterns = [
        # intro paragraph's reference-implementation sentence
        r"\s+Where it helps to be concrete, it references.*?theory maps to practice\.",
        # §9.2 parenthetical aside
        r"\s*\*This is what\s+the reference repo uses\.\*",
        # closing line's callout clause
        r"; the \"In this repo\" callouts map.*?practice side by side",
    ]
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.DOTALL)
    return text


with open(SRC, encoding="utf-8") as f:
    raw_md = f.read()

md_text = fix_nested_list_indent(raw_md)

body = markdown.markdown(
    md_text,
    extensions=["extra", "sane_lists", "toc"],
    extension_configs={"toc": {"slugify": github_slugify}},
    output_format="html5",
)

# --- Build the copy-paste LLM prompt (hands-on-guide framing) -------------
PROMPT_HEAD = (
    "You are an expert full-stack web developer acting as my hands-on "
    "pair-programming guide. I want to build, test, and ship a modern "
    "full-stack web app by following the playbook below.\n\n"
    "Your job: help me apply this playbook to MY project.\n"
    "1. First, ask me about what I'm building, my experience level, and my goals.\n"
    "2. Then guide me step by step — recommend decisions, write and explain "
    "code, and keep me on the Red→Green→Refactor TDD workflow the playbook describes.\n"
    "3. Cite the playbook's sections as we go, and adapt its choices to my needs.\n\n"
    "Here is the playbook:\n\n---\n\n"
)
PROMPT_TAIL = "\n\n---\n\nStart by asking me about my project.\n"

prompt_text = PROMPT_HEAD + scrub_repo_prose(strip_repo_callouts(raw_md)).strip() + PROMPT_TAIL
prompt_b64 = base64.b64encode(prompt_text.encode("utf-8")).decode("ascii")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Modern Full-Stack Web App Playbook — Chase Sweers</title>
<meta name="description" content="A practical, tool-by-tool guide to building, testing, and shipping a typed, test-driven full-stack web application.">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Outfit:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
  :root {
    --black: #08070a;
    --black-soft: #100d16;
    --purple: #8b3df5;
    --purple-bright: #b07cff;
    --purple-deep: #4a1d8a;
    --text: #ece9f1;
    --text-dim: #9a93ab;
    --line: rgba(139, 61, 245, 0.18);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--black);
    color: var(--text);
    font-family: 'Outfit', sans-serif;
    font-weight: 300;
    line-height: 1.6;
    overflow-x: hidden;
  }

  /* atmospheric background (matches home) */
  .glow { position: fixed; border-radius: 50%; filter: blur(120px); opacity: 0.5; z-index: 0; pointer-events: none; }
  .glow-1 { width: 600px; height: 600px; background: var(--purple-deep); top: -240px; left: -180px; }
  .glow-2 { width: 460px; height: 460px; background: var(--purple); bottom: -160px; right: -120px; opacity: 0.22; }
  body::after {
    content: ""; position: fixed; inset: 0; z-index: 1; pointer-events: none; opacity: 0.035;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }

  /* sticky top bar */
  .doc-top {
    position: sticky; top: 0; z-index: 50;
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px; row-gap: 10px;
    padding: 18px clamp(20px, 6vw, 64px);
    backdrop-filter: blur(10px);
    background: linear-gradient(to bottom, rgba(8,7,10,0.92), rgba(8,7,10,0.72));
    border-bottom: 1px solid var(--line);
  }
  .doc-top .back {
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem;
    color: var(--text); text-decoration: none; letter-spacing: -0.01em;
    display: inline-flex; align-items: center; gap: 9px; transition: color 0.3s;
    white-space: nowrap;
  }
  .doc-top .back span { color: var(--purple-bright); }
  .doc-top .back:hover { color: var(--purple-bright); }
  .actions { display: flex; align-items: center; gap: 10px; margin-left: auto; flex-wrap: wrap; }
  .btn {
    display: inline-flex; align-items: center; gap: 9px;
    background: var(--purple); color: #fff; text-decoration: none; font-weight: 500;
    padding: 11px 22px; border-radius: 100px; font-size: 0.9rem;
    transition: transform 0.3s, box-shadow 0.3s, background 0.3s, color 0.3s;
    box-shadow: 0 8px 30px rgba(139,61,245,0.3); white-space: nowrap;
  }
  .btn:hover { transform: translateY(-2px); background: var(--purple-bright); box-shadow: 0 12px 40px rgba(139,61,245,0.5); }
  button.btn { border: none; cursor: pointer; font-family: inherit; }
  .btn-secondary { background: transparent; color: var(--purple-bright); border: 1px solid var(--line); box-shadow: none; }
  .btn-secondary:hover { background: rgba(139,61,245,0.14); color: #fff; box-shadow: none; }
  .btn-copy.copied { background: #2ea36b; box-shadow: 0 8px 30px rgba(46,163,107,0.4); }
  .btn-copy.copied:hover { background: #2ea36b; transform: none; }

  /* document column */
  .doc {
    position: relative; z-index: 2;
    max-width: 860px; margin: 0 auto;
    padding: clamp(40px, 7vw, 80px) clamp(20px, 6vw, 40px) 120px;
    color: #c7c1d4; font-size: 1.02rem;
  }
  .doc > *:first-child { margin-top: 0; }

  .doc h1, .doc h2, .doc h3, .doc h4 {
    font-family: 'Syne', sans-serif; color: var(--text);
    line-height: 1.15; letter-spacing: -0.02em; scroll-margin-top: 84px;
  }
  .doc h1 {
    font-weight: 800; font-size: clamp(2.1rem, 5.5vw, 3.4rem); margin: 0 0 18px;
    background: linear-gradient(110deg, var(--purple-bright), var(--purple) 55%, #d9c4ff);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .doc h2 {
    font-weight: 700; font-size: clamp(1.6rem, 3.4vw, 2.2rem);
    margin: 72px 0 22px; padding-top: 30px; border-top: 1px solid var(--line);
  }
  .doc h3 { font-weight: 600; font-size: 1.3rem; margin: 44px 0 14px; color: #efeaf6; }
  .doc h4 { font-weight: 600; font-size: 1.05rem; margin: 32px 0 12px; color: var(--purple-bright); }

  .doc p { margin: 0 0 18px; line-height: 1.75; }
  .doc a { color: var(--purple-bright); text-decoration: none; border-bottom: 1px solid rgba(176,124,255,0.3); transition: border-color 0.25s, color 0.25s; }
  .doc a:hover { color: #d9c4ff; border-color: var(--purple-bright); }
  .doc strong { color: var(--purple-bright); font-weight: 500; }
  .doc em { color: #d6d0e2; }

  .doc ul, .doc ol { margin: 0 0 18px; padding-left: 1.5em; line-height: 1.7; }
  .doc li { margin-bottom: 8px; }
  .doc li::marker { color: var(--purple); }
  .doc ul ul, .doc ol ul, .doc ul ol, .doc ol ol { margin: 8px 0 4px; }

  /* inline code */
  .doc code {
    font-family: 'JetBrains Mono', monospace; font-size: 0.85em;
    background: rgba(139,61,245,0.14); color: #d9c4ff;
    padding: 2px 6px; border-radius: 6px; border: 1px solid rgba(139,61,245,0.18);
  }
  /* code blocks */
  .doc pre {
    background: var(--black-soft); border: 1px solid var(--line); border-radius: 14px;
    padding: 20px 22px; overflow-x: auto; margin: 0 0 24px; line-height: 1.55;
  }
  .doc pre code {
    font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
    background: none; border: none; padding: 0; color: #d8d3e3; white-space: pre;
  }

  /* tables */
  .doc .table-scroll { overflow-x: auto; margin: 0 0 26px; border: 1px solid var(--line); border-radius: 14px; }
  .doc table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
  .doc th, .doc td { text-align: left; padding: 11px 16px; border-bottom: 1px solid var(--line); vertical-align: top; }
  .doc thead th { background: rgba(139,61,245,0.12); color: var(--text); font-family: 'Outfit', sans-serif; font-weight: 500; letter-spacing: 0.01em; }
  .doc tbody tr:nth-child(even) { background: rgba(255,255,255,0.02); }
  .doc tbody tr:last-child td { border-bottom: none; }
  .doc td code, .doc th code { white-space: nowrap; }

  /* blockquotes ("In this repo" / notes) */
  .doc blockquote {
    margin: 0 0 24px; padding: 18px 22px;
    background: linear-gradient(135deg, var(--black-soft), rgba(74,29,138,0.12));
    border: 1px solid var(--line); border-left: 3px solid var(--purple);
    border-radius: 12px; color: var(--text-dim);
  }
  .doc blockquote p { margin: 0 0 10px; }
  .doc blockquote p:last-child { margin-bottom: 0; }
  .doc blockquote strong { color: var(--purple-bright); }
  .doc blockquote code { background: rgba(139,61,245,0.1); }

  .doc hr { border: none; height: 1px; background: var(--line); margin: 56px 0; }

  footer {
    position: relative; z-index: 2; text-align: center;
    padding: 36px 8vw; color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace; font-size: 0.76rem;
    border-top: 1px solid var(--line);
  }

  @media (max-width: 600px) {
    .doc { font-size: 0.98rem; }
    .doc pre code, .doc table { font-size: 0.78rem; }
    .doc-top { padding-left: 16px; padding-right: 16px; }
    .doc-top .back { font-size: 0.92rem; }
    .doc-top .btn { padding: 10px 16px; font-size: 0.85rem; }
  }
</style>
</head>
<body>

<div class="glow glow-1"></div>
<div class="glow glow-2"></div>

<header class="doc-top">
  <a class="back" href="../index.html"><span>&larr;</span> Chase Sweers</a>
  <div class="actions">
    <button class="btn btn-copy" id="copyPrompt" type="button">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>
      <span class="label">Copy LLM prompt</span>
    </button>
    <a class="btn btn-secondary" href="FULLSTACK-PLAYBOOK.docx" download>
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/></svg>
      <span class="label">Download .docx</span>
    </a>
  </div>
</header>

<main class="doc">
__BODY__
</main>

<footer>
  &copy; 2026 Chase Sweers &middot; Full-Stack Web App Playbook
</footer>

<script type="text/plain" id="llm-prompt-b64">__PROMPT_B64__</script>
<script>
(function () {
  var btn = document.getElementById('copyPrompt');
  if (!btn) return;
  var labelEl = btn.querySelector('.label');
  var original = labelEl.textContent;
  var resetTimer;
  function decodePrompt() {
    var b64 = document.getElementById('llm-prompt-b64').textContent.trim();
    var bin = atob(b64);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder('utf-8').decode(bytes);
  }
  function flash(msg, ok) {
    labelEl.textContent = msg;
    btn.classList.toggle('copied', !!ok);
    clearTimeout(resetTimer);
    resetTimer = setTimeout(function () {
      labelEl.textContent = original;
      btn.classList.remove('copied');
    }, 2200);
  }
  btn.addEventListener('click', async function () {
    var text = decodePrompt();
    var ok = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        ok = true;
      }
    } catch (e) { ok = false; }
    if (!ok) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
    }
    flash(ok ? 'Copied!' : 'Press Ctrl/Cmd+C', ok);
  });
})();
</script>

</body>
</html>
"""

html = TEMPLATE.replace("__BODY__", body)

# Make wide GFM tables horizontally scrollable on narrow screens.
html = html.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")

# Embed the copy-paste prompt (base64, so copy works offline with no escaping issues).
html = html.replace("__PROMPT_B64__", prompt_b64)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("wrote", OUT)
print("headings with ids:", len(re.findall(r"<h[1-6] id=", html)),
      "| tables:", html.count("<table>"), "| code blocks:", html.count("<pre>"))
print("prompt chars:", len(prompt_text), "| base64 chars:", len(prompt_b64))
